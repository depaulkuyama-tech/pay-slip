from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader, PdfWriter
from config import Config
import sqlite3
import os
from datetime import datetime, timedelta

# ------------------ FLASK APP ------------------
app = Flask(__name__)
app.config.from_object(Config)

BASE_DIR = app.config["BASE_DIR"]
MASTER_PDF_DIR = app.config["MASTER_PDF_DIR"]
OUTPUT_DIR = app.config["OUTPUT_DIR"]
DB_PATH = app.config["DB_PATH"]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MASTER_PDF_DIR, exist_ok=True)

# ------------------ DATABASE ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            employee_number TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ PAY PERIODS ------------------
def generate_pay_periods(start_date="01-07-2025", num_periods=52):
    """Generate 52 fortnightly pay periods starting from start_date (July 2025)."""
    first_date = datetime.strptime(start_date, "%d-%m-%Y")
    periods = []
    for i in range(num_periods):
        pay_date = first_date + timedelta(days=i*14)
        filename = pay_date.strftime("%d-%b-%Y") + ".pdf"
        filepath = os.path.join(MASTER_PDF_DIR, filename)
        periods.append({
            "pay_date": pay_date.strftime("%d-%b-%Y"),
            "filepath": filepath,
            "available": os.path.exists(filepath)
        })
    return periods

# ------------------ PDF EXTRACTION ------------------
def extract_payslip(employee_number, master_pdf_path, pay_date_str):
    """Extract employee page from master PDF."""
    if not os.path.exists(master_pdf_path):
        return None

    reader = PdfReader(master_pdf_path)
    writer = PdfWriter()
    found = False

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and employee_number in text:
            writer.add_page(page)
            found = True

    if not found:
        return None

    output_pdf = os.path.join(OUTPUT_DIR, f"employee_{employee_number}_{pay_date_str}.pdf")
    if not os.path.exists(output_pdf):  # Avoid rewriting if already extracted
        with open(output_pdf, "wb") as f:
            writer.write(f)
    return output_pdf

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return redirect(url_for("portal") if "user" in session else url_for("login"))

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        employee_number = request.form["employee_number"].strip()
        email = request.form["email"].strip()
        department = request.form.get("department", "").strip()
        terms = request.form.get("terms")

        if not terms:
            flash("You must agree to the terms and conditions.", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password, employee_number, email, department) VALUES (?, ?, ?, ?, ?)",
                (username, hashed_pw, employee_number, email, department)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Username, email, or employee number already exists!", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_input = request.form["username"].strip()
        password = request.form["password"].strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT password, username, employee_number, department FROM users WHERE username=? OR email=?",
            (user_input, user_input)
        )
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session.clear()
            session["user"] = result[1]
            session["employee_number"] = result[2]
            session["department"] = result[3]
            flash(f"Welcome back, {result[1]}!", "success")
            return redirect(url_for("portal"))

        flash("Invalid username/email or password!", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    user = session.pop("user", None)
    if user:
        flash(f"Goodbye, {user}!", "info")
    return redirect(url_for("login"))

# ---------- PORTAL ----------
@app.route("/portal", methods=["GET", "POST"])
def portal():
    if "user" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT employee_number, department FROM users WHERE username=?", (session["user"],))
    user_data = c.fetchone()
    conn.close()

    if not user_data:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    employee_number_db, department = user_data

    # Generate all pay periods from July 2025
    pay_periods = generate_pay_periods(start_date="24-07-2025", num_periods=26)

    # Handle POST: extract and download selected payslip
    if request.method == "POST":
        selected_date = request.form.get("pay_date")
        if selected_date:
            selected_period = next((p for p in pay_periods if p["pay_date"] == selected_date), None)
            if selected_period and selected_period["available"]:
                output_file = extract_payslip(employee_number_db, selected_period["filepath"], selected_date)
                if output_file:
                    return send_file(output_file, as_attachment=True)
            flash("Selected payslip is not available.", "danger")
        return redirect(url_for("portal"))

    # Build history of already extracted files
    extracted_files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith(f"employee_{employee_number_db}_") and f.endswith(".pdf"):
            pay_date = f.replace(f"employee_{employee_number_db}_", "").replace(".pdf", "")
            extracted_files.append({"pay_date": pay_date, "filename": f})

    return render_template("index.html",
                           username=session["user"],
                           employee_number=employee_number_db,
                           department=department,
                           pay_periods=pay_periods,
                           payslip_history=extracted_files)

# ---------- DOWNLOAD PAYSLIP ----------
@app.route("/download/<filename>")
def download_payslip(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        flash("Payslip not found!", "danger")
        return redirect(url_for("portal"))
    return send_file(path, as_attachment=True)


# ---------- DELETE PAYSLIP ----------
@app.route("/delete_payslip/<filename>", methods=["POST"])
def delete_payslip(filename):
    # Build the current history
    employee_number = session.get("employee_number")
    if not employee_number:
        flash("User session expired.", "warning")
        return redirect(url_for("login"))

    # Only remove from the displayed history
    global OUTPUT_DIR
    current_history = []
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith(f"employee_{employee_number}_") and f.endswith(".pdf"):
            if f != filename:  # skip the file to "delete" from history
                pay_date = f.replace(f"employee_{employee_number}_", "").replace(".pdf", "")
                current_history.append({"pay_date": pay_date, "filename": f})

    # Store filtered history in session temporarily (optional)
    session["payslip_history"] = current_history

    flash(f"Payslip '{filename}' removed from history.", "success")
    return redirect(url_for("portal"))



# ---------- CHANGE PASSWORD ----------
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password").strip()
        new_password = request.form.get("new_password").strip()
        confirm_password = request.form.get("confirm_password").strip()

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return redirect(url_for("change_password"))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (session["user"],))
        user = c.fetchone()
        if not user or not check_password_hash(user[0], current_password):
            conn.close()
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("change_password"))

        hashed_pw = generate_password_hash(new_password)
        c.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, session["user"]))
        conn.commit()
        conn.close()
        flash("Password updated successfully!", "success")
        return redirect(url_for("portal"))

    return render_template("change_password.html")

# ---------- FORGOT PASSWORD ----------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        flash("If the email exists, a password reset link has been sent (demo).", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

# ---------- TERMS PAGE ----------
@app.route("/terms")
def terms():
    return render_template("terms.html")

# ---------- CONTACT HR ----------
@app.route("/contact-hr")
def contact_hr():
    return render_template("contact_hr.html")

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


