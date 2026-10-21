
import os
from pathlib import Path

from dotenv import load_dotenv

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from flask_socketio import SocketIO, join_room, emit

# Load configuration from .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{BASE_DIR / 'quantum_encryption.db'}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session configuration
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing from .env")

app.config["SECRET_KEY"] = secret_key
socketio = SocketIO(app, async_mode="threading")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable this when deployed over HTTPS.
# Keep False for local HTTP development.
app.config["SESSION_COOKIE_SECURE"] = False

db = SQLAlchemy(app)


# User database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


with app.app_context():
    db.create_all()

print("SQLite database ready!")


# Signup route
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send valid JSON data"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (username, email, password)
    ):
        return jsonify({
            "error": "Username, email and password are required"
        }), 400

    username = username.strip()
    email = email.strip().lower()

    if len(username) > 50 or len(email) > 120:
        return jsonify({"error": "Username or email is too long"}), 400

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    # Check for an existing username or email
    existing_user = db.session.execute(
        db.select(User).where(
            db.or_(
                User.username == username,
                User.email == email
            )
        )
    ).scalar_one_or_none()

    if existing_user:
        return jsonify({
            "error": "Username or email already exists"
        }), 409

    # Hash the password before saving it
    password_hash = generate_password_hash(password)

    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Signup database operation failed")
        return jsonify({"error": "Could not create account"}), 500

    return jsonify({
        "message": "Signup successful",
        "user_id": new_user.id
    }), 201


# Login route
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send valid JSON data"}), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400

    email = email.strip().lower()

    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    # Use the same error for unknown email and incorrect password
    if user is None or not check_password_hash(
        user.password_hash, password
    ):
        return jsonify({"error": "Invalid email or password"}), 401

    # Start a fresh authenticated session
    session.clear()
    session["user_id"] = user.id

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200


# Protected test route: requires a logged-in user
@app.route("/api/me", methods=["GET"])
def me():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({"error": "Please log in first"}), 401

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return jsonify({"error": "User not found"}), 401

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200

# Message database model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    encrypted_message = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

with app.app_context():
    db.create_all()


# Logout route
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


@app.route("/")
def home():
    return "Quantum Encryption App is running!"

# Socket.IO connection handler
@socketio.on("connect")
def handle_connect(auth=None):
    # Check whether the user is logged in
    user_id = session.get("user_id")

    if user_id is None:
        return False  # Reject unauthenticated connections

    # Confirm the user still exists
    user = db.session.get(User, user_id)

    if user is None:
        return False

    # Give this user a private room
    join_room(f"user_{user_id}")

    print(f"User {user_id} connected to Socket.IO")

# Handle sending a real-time message
@socketio.on("send_message")
def handle_send_message(data):

    # 1. Identify the logged-in sender
    sender_id = session.get("user_id")

    if sender_id is None:
        return {"error": "Please log in first"}

    # 2. Validate the incoming data
    if not isinstance(data, dict):
        return {"error": "Invalid message data"}

    receiver_id = data.get("receiver_id")
    encrypted_message = data.get("encrypted_message")

    if not isinstance(receiver_id, int) or isinstance(receiver_id, bool):
        return {"error": "Invalid recipient ID"}

    if not isinstance(encrypted_message, str):
        return {"error": "Invalid message content"}

    encrypted_message = encrypted_message.strip()

    if not encrypted_message or len(encrypted_message) > 10000:
        return {"error": "Message must contain 1–10000 characters"}

    # 3. Check that the recipient exists
    recipient = db.session.get(User, receiver_id)

    if recipient is None:
        return {"error": "Recipient not found"}

    # 4. Save the message in SQLite
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        encrypted_message=encrypted_message
    )

    try:
        db.session.add(message)
        db.session.commit()

    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to save message")
        return {"error": "Could not save message"}

    # 5. Prepare the message for the recipient
    message_data = {
        "id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "encrypted_message": message.encrypted_message,
        "created_at": message.created_at.isoformat()
    }

    # 6. Deliver it to the recipient's private room
    socketio.emit(
        "new_message",
        message_data,
        to=f"user_{receiver_id}"
    )

    # 7. Confirm to the sender that it was saved
    return {
        "status": "sent",
        "message_id": message.id
    }


# Handle sending a message in real time
@socketio.on("send_message")
def handle_send_message(data):
    # 1. Check that the sender is logged in
    sender_id = session.get("user_id")

    if sender_id is None:
        return {"error": "Please log in first"}

    # 2. Validate the received data
    if not isinstance(data, dict):
        return {"error": "Invalid message data"}

    receiver_id = data.get("receiver_id")
    encrypted_message = data.get("encrypted_message")

    # Make sure receiver_id is an integer, not a boolean
    if type(receiver_id) is not int:
        return {"error": "Invalid recipient ID"}

    if receiver_id == sender_id:
        return {"error": "You cannot message yourself"}

    if not isinstance(encrypted_message, str):
        return {"error": "Message must be a string"}

    encrypted_message = encrypted_message.strip()

    if not encrypted_message or len(encrypted_message) > 10000:
        return {"error": "Message is empty or too long"}

    # 3. Check that the recipient exists
    recipient = db.session.get(User, receiver_id)

    if recipient is None:
        return {"error": "Recipient not found"}

    # 4. Save the message in SQLite
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        encrypted_message=encrypted_message
    )

    try:
        db.session.add(message)
        db.session.commit()

        # 5. Notify the recipient's private room
        socketio.emit(
            "new_message",
            {
                "id": message.id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "encrypted_message": message.encrypted_message,
                "created_at": message.created_at.isoformat()
            },
            to=f"user_{receiver_id}"
        )

        return {
            "message": "Message sent successfully",
            "message_id": message.id
        }

    except Exception:
        db.session.rollback()
        app.logger.exception("Message sending failed")
        return {"error": "Could not send message"}


if __name__ == "__main__":
    socketio.run(app, debug=False)
