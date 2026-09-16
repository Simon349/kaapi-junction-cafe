"""
Kaapi Junction — Cafe Website
A Flask-powered coffee cafe website with a public front-end and an
admin panel for managing the menu and reading customer messages.

Run with:
    python app.py

Everything that happens (visits to key pages, form submissions, admin
actions) is also printed to the terminal so you can watch the app work
while it runs.
"""

import os
import functools
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------------------------------------------------
# App & database setup
# ----------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "kaapi-junction-dev-secret-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "cafe.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


def log(msg):
    """Print a timestamped line to the terminal so the console shows
    live activity while the server runs."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300), default="")
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(60), nullable=False)  # Filter Kaapi / Espresso / Cold Brew / Bakes & Bites
    is_special = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "price": self.price, "category": self.category,
            "is_special": self.is_special, "is_available": self.is_available,
        }


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), default="")
    subject = db.Column(db.String(150), default="General enquiry")
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


# ----------------------------------------------------------------------
# Auth helper
# ----------------------------------------------------------------------

def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


# ----------------------------------------------------------------------
# Seed data (first run only)
# ----------------------------------------------------------------------

def seed_data():
    if Admin.query.count() == 0:
        admin = Admin(username="admin")
        admin.set_password("kaapi123")
        db.session.add(admin)
        log("Created default admin account -> username: admin / password: kaapi123")

    if MenuItem.query.count() == 0:
        items = [
            ("Filter Kaapi", "Slow-decocted Coorg beans, frothed the old-fashioned way with a davara-tumbler pour", 60, "Filter Kaapi", True, 1),
            ("Mysore Filter", "Extra strong, extra chicory — for the days that need it", 70, "Filter Kaapi", False, 2),
            ("Cardamom Kaapi", "Filter coffee with a whisper of crushed elaichi", 80, "Filter Kaapi", False, 3),
            ("Classic Espresso", "Single origin, pulled in nine seconds flat", 90, "Espresso Classics", False, 1),
            ("Cappuccino", "Equal parts espresso, steamed milk, microfoam", 130, "Espresso Classics", False, 2),
            ("Café Mocha", "Espresso, steamed milk, dark chocolate", 150, "Espresso Classics", True, 3),
            ("Cold Brew Original", "Steeped 18 hours, served over ice", 140, "Cold Brews", False, 1),
            ("Nitro Cold Brew", "Cascading, creamy, nitrogen-charged", 170, "Cold Brews", True, 2),
            ("Iced Caramel Kaapi", "Filter coffee meets caramel over ice", 160, "Cold Brews", False, 3),
            ("Banana Walnut Loaf", "Baked in-house, every morning", 110, "Bakes & Bites", False, 1),
            ("Khari Biscuit Stack", "Flaky, buttery, three to a plate", 70, "Bakes & Bites", False, 2),
            ("Masala Maggi Toast", "Because some cravings are non-negotiable", 120, "Bakes & Bites", True, 3),
        ]
        for name, desc, price, cat, special, order in items:
            db.session.add(MenuItem(
                name=name, description=desc, price=price, category=cat,
                is_special=special, sort_order=order
            ))
        log(f"Seeded {len(items)} menu items")

    db.session.commit()


# ----------------------------------------------------------------------
# Public routes
# ----------------------------------------------------------------------

@app.route("/")
def home():
    specials = MenuItem.query.filter_by(is_special=True, is_available=True).limit(4).all()
    log("GET /  (home page viewed)")
    return render_template("index.html", specials=specials)


@app.route("/menu")
def menu():
    items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.category, MenuItem.sort_order).all()
    categories = []
    for item in items:
        if item.category not in categories:
            categories.append(item.category)
    grouped = {cat: [i for i in items if i.category == cat] for cat in categories}
    log("GET /menu  (menu page viewed)")
    return render_template("menu.html", grouped=grouped)


@app.route("/about")
def about():
    log("GET /about")
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip() or "General enquiry"
        body = request.form.get("message", "").strip()

        if not name or not email or not body:
            flash("Please fill in your name, email and message.", "error")
            log("POST /contact  -> rejected (missing fields)")
            return redirect(url_for("contact"))

        msg = Message(name=name, email=email, phone=phone, subject=subject, body=body)
        db.session.add(msg)
        db.session.commit()
        log(f"POST /contact  -> new message from {name} <{email}>: \"{subject}\"")
        flash("Thanks! Your message has reached us — we'll get back to you soon.", "success")
        return redirect(url_for("contact"))

    log("GET /contact")
    return render_template("contact.html")


# ----------------------------------------------------------------------
# Admin routes
# ----------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            log(f"ADMIN LOGIN  -> '{username}' logged in successfully")
            flash(f"Welcome back, {admin.username}.", "success")
            return redirect(url_for("admin_dashboard"))

        log(f"ADMIN LOGIN  -> failed attempt for username '{username}'")
        flash("Incorrect username or password.", "error")
        return redirect(url_for("admin_login"))

    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    username = session.get("admin_username", "unknown")
    session.clear()
    log(f"ADMIN LOGOUT -> '{username}' logged out")
    flash("You've been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    total_items = MenuItem.query.count()
    total_messages = Message.query.count()
    unread_messages = Message.query.filter_by(is_read=False).count()
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    log("ADMIN -> dashboard viewed")
    return render_template(
        "admin/dashboard.html",
        total_items=total_items,
        total_messages=total_messages,
        unread_messages=unread_messages,
        recent_messages=recent_messages,
    )


@app.route("/admin/menu")
@admin_required
def admin_menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.sort_order).all()
    log("ADMIN -> menu list viewed")
    return render_template("admin/menu_list.html", items=items)


@app.route("/admin/menu/add", methods=["GET", "POST"])
@admin_required
def admin_menu_add():
    if request.method == "POST":
        item = MenuItem(
            name=request.form["name"].strip(),
            description=request.form.get("description", "").strip(),
            price=float(request.form["price"]),
            category=request.form["category"].strip(),
            is_special=bool(request.form.get("is_special")),
            is_available=bool(request.form.get("is_available")),
            sort_order=int(request.form.get("sort_order") or 0),
        )
        db.session.add(item)
        db.session.commit()
        log(f"ADMIN -> added menu item '{item.name}' (₹{item.price}, {item.category})")
        flash(f"'{item.name}' added to the menu.", "success")
        return redirect(url_for("admin_menu"))

    log("ADMIN -> add-item form opened")
    return render_template("admin/item_form.html", item=None)


@app.route("/admin/menu/edit/<int:item_id>", methods=["GET", "POST"])
@admin_required
def admin_menu_edit(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if request.method == "POST":
        item.name = request.form["name"].strip()
        item.description = request.form.get("description", "").strip()
        item.price = float(request.form["price"])
        item.category = request.form["category"].strip()
        item.is_special = bool(request.form.get("is_special"))
        item.is_available = bool(request.form.get("is_available"))
        item.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        log(f"ADMIN -> updated menu item '{item.name}' (#{item.id})")
        flash(f"'{item.name}' updated.", "success")
        return redirect(url_for("admin_menu"))

    log(f"ADMIN -> edit form opened for item #{item.id}")
    return render_template("admin/item_form.html", item=item)


@app.route("/admin/menu/delete/<int:item_id>", methods=["POST"])
@admin_required
def admin_menu_delete(item_id):
    item = MenuItem.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    log(f"ADMIN -> deleted menu item '{name}' (#{item_id})")
    flash(f"'{name}' removed from the menu.", "success")
    return redirect(url_for("admin_menu"))


@app.route("/admin/messages")
@admin_required
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    log("ADMIN -> messages inbox viewed")
    return render_template("admin/messages.html", messages=messages)


@app.route("/admin/messages/read/<int:msg_id>", methods=["POST"])
@admin_required
def admin_message_read(msg_id):
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    log(f"ADMIN -> marked message #{msg_id} from {msg.name} as read")
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/delete/<int:msg_id>", methods=["POST"])
@admin_required
def admin_message_delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    log(f"ADMIN -> deleted message #{msg_id}")
    flash("Message deleted.", "success")
    return redirect(url_for("admin_messages"))


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    print("=" * 60)
    print("  KAAPI JUNCTION — cafe website starting up")
    print("  Front-end : http://127.0.0.1:5000/")
    print("  Admin     : http://127.0.0.1:5000/admin/login")
    print("  Admin login -> username: admin | password: kaapi123")
    print("=" * 60)
    app.run(debug=True)
