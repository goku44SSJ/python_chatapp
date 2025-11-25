from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

DB_PATH = "users.db"


# ---------------------------------------------
#  Initialize DB with 5 users + hashed passwords
# ---------------------------------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL
            );
        """)

        # Sample 5 users
        sample_users = [
            ("user1", "pass1", "Samyak"),
            ("user2", "pass2", "Koyal"),
            ("user3", "pass3", "Gopinath"),
            ("user4", "pass4", "Harekrishna"),
            ("user5", "pass5", "Shreyash"),
        ]

        for u, p, d in sample_users:
            cur.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
                (u, generate_password_hash(p), d)
            )

        conn.commit()
        conn.close()


init_db()


# ---------------------------------------------
#  Routes
# ---------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------
#  Socket Events
# ---------------------------------------------
@socketio.on("login")
def handle_login(data):
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, display_name FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if not user:
        emit("login_failed", {"error": "Invalid username"})
        return

    user_id, password_hash, display_name = user

    if not check_password_hash(password_hash, password):
        emit("login_failed", {"error": "Incorrect password"})
        return

    emit("login_success", {
        "user_id": user_id,
        "display_name": display_name
    })


@socketio.on("send_message")
def handle_message(data):
    display_name = data.get("display_name")
    message = data.get("message")

    socketio.emit("chat_message", {
        "from": display_name,
        "text": message
    })


@socketio.on("connect")
def handle_connect():
    emit("server_message", {"text": "Connected to Flask Chat Server"})


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected:", request.sid)


# ---------------------------------------------
# Run Server (Render compatible)
# ---------------------------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


