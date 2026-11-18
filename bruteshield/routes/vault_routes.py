import time
from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, flash
from bruteshield.database import get_db
from bruteshield.security import encrypt_vault_secret, decrypt_vault_secret

vault_bp = Blueprint("vault", __name__, url_prefix="/vault")

def login_required(func):
    """Decorator ensuring that only authenticated users access the vault."""
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return decorated_view

@vault_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]
    conn = get_db()
    
    if request.method == "POST":
        service_name = request.form.get("service_name", "").strip()[:128]
        account_username = request.form.get("username", "").strip()[:128]
        account_password = request.form.get("password", "")
        notes = request.form.get("notes", "").strip()[:1024]

        if service_name and account_username and account_password and len(account_password) <= 256:
            # Authenticated AES-256-GCM encryption
            b64_cipher, b64_nonce = encrypt_vault_secret(account_password)
            now = time.time()
            conn.execute("""
                INSERT INTO vault_items (user_id, service_name, username, encrypted_password, nonce, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, service_name, account_username, b64_cipher, b64_nonce, notes, now, now))
            conn.commit()

    # Retrieve all vault items for this user
    items = conn.execute("""
        SELECT id, service_name, username, notes, created_at, updated_at
        FROM vault_items
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()

    return render_template("vault.html", items=items, username=session.get("username"))

@vault_bp.route("/decrypt/<int:item_id>", methods=["GET"])
@login_required
def decrypt_item(item_id):
    user_id = session["user_id"]
    conn = get_db()
    row = conn.execute("""
        SELECT encrypted_password, nonce
        FROM vault_items
        WHERE id = ? AND user_id = ?
    """, (item_id, user_id)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Item not found or access denied"}), 404

    try:
        decrypted = decrypt_vault_secret(row["encrypted_password"], row["nonce"])
        return jsonify({"success": True, "password": decrypted})
    except Exception as e:
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

@vault_bp.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    user_id = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM vault_items WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("vault.index"))
