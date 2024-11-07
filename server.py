# server.py
from flask import Flask, request, jsonify, g
import os
from config import Config
import psycopg2
from bb84_utils import *
import json
import random
from contextlib import contextmanager

app = Flask(__name__)

# Global variables to store state
class ServerState:
    def __init__(self):
        self.len_key = 0
        self.bob_bases = []
        self.final_key = []

server_state = ServerState()

def get_db():
    """Get a database connection"""
    if 'db' not in g:
        g.db = psycopg2.connect(
            host=Config.DB_HOST,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            port=Config.DB_PORT
        )
    return g.db

@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of the request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    return "BB84 Quantum Key Distribution Server"

@app.route("/generate_bases", methods=["POST"])
def generate_bases():
    try:
        data = request.get_json()
        server_state.len_key = data['num_qubits']
        server_state.bob_bases = [random.choice(['+', 'x']) for _ in range(server_state.len_key)]
        return jsonify({"server_bases": server_state.bob_bases})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/receive_bases', methods=['POST'])
def receive_bases():
    try:
        data = request.get_json()
        alice_bits = data['alice_bits']
        alice_bases = data['alice_bases']

        sifted_key = []
        for i, (a_base, b_base) in enumerate(zip(alice_bases, server_state.bob_bases)):
            if a_base == b_base:
                sifted_key.append(alice_bits[i])
        
        server_state.final_key = privacy_amplification(sifted_key)
        
        # Print the server_state.bob_bases
        print("Final Key :", server_state.final_key)
        
        
        return jsonify({"status": "success", "Final_Key": server_state.final_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/store_encrypted_message', methods=['POST'])
def store_encrypted_message():
    try:
        data = request.get_json()
        encrypted_message = data['encrypted_message']
        encrypted_bits = json.loads(encrypted_message)

        decrypted_message = decrypt_message(server_state.final_key, encrypted_bits)

        # Print the server_state.bob_bases
        print("Decrypted Message :", decrypted_message)
        
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO "Message" ("sender_id", "receiver_id", "message", "status")
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (1, 2, decrypted_message, True))
            
        return jsonify({
            "status": "success",
            "message": "Message stored successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)