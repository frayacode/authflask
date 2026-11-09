import os
from urllib.parse import urlparse, urljoin

import click
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, abort,
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user,
)

from models import db, User, Post, VALID_ROLES, ROLE_ADMIN, ROLE_USER
from decorators import roles_required


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-ganti-di-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///app.db"
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Silakan login terlebih dahulu."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ---------- Helper ----------
    def is_safe_url(target):
        host_url = urlparse(request.host_url)
        redirect_url = urlparse(urljoin(request.host_url, target))
        return (
            redirect_url.scheme in ("http", "https")
            and host_url.netloc == redirect_url.netloc
        )

    def can_modify(post):
        return current_user.is_authenticated and (
            post.user_id == current_user.id or current_user.is_admin
        )

    app.jinja_env.globals["can_modify"] = can_modify

    # ---------- Autentikasi (Part 18) ----------
    @app.route("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or len(password) < 6:
                flash("Username wajib diisi dan password minimal 6 karakter.", "danger")
            elif User.query.filter_by(username=username).first():
                flash("Username sudah dipakai.", "danger")
            else:
                # Role SELALU 'user' untuk pendaftaran mandiri
                user = User(username=username, role=ROLE_USER)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Pendaftaran berhasil, silakan login.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = User.query.filter_by(username=request.form.get("username", "")).first()
            if user and user.check_password(request.form.get("password", "")):
                login_user(user)
                next_page = request.args.get("next")
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for("dashboard"))
            flash("Username atau password salah.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ---------- Halaman terproteksi ----------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        posts = Post.query.order_by(Post.id.desc()).all()
        return render_template("dashboard.html", posts=posts)

    @app.route("/posts/new", methods=["GET", "POST"])
    @login_required
    def new_post():
        if request.method == "POST":
            post = Post(
                title=request.form["title"].strip(),
                body=request.form["body"].strip(),
                user_id=current_user.id,
            )
            db.session.add(post)
            db.session.commit()
            flash("Postingan dibuat.", "success")
            return redirect(url_for("dashboard"))
        return render_template("edit_post.html", post=None)

    @app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_post(post_id):
        post = db.get_or_404(Post, post_id)
        if not can_modify(post):  # ownership check
            abort(403)
        if request.method == "POST":
            post.title = request.form["title"].strip()
            post.body = request.form["body"].strip()
            db.session.commit()
            flash("Postingan diperbarui.", "success")
            return redirect(url_for("dashboard"))
        return render_template("edit_post.html", post=post)

    # ---------- Admin (Part 19) ----------
    @app.route("/admin/users")
    @roles_required(ROLE_ADMIN)
    def admin_users():
        users = User.query.order_by(User.username).all()
        return render_template("admin_users.html", users=users, roles=VALID_ROLES)

    @app.route("/admin/users/<int:user_id>/role", methods=["POST"])
    @roles_required(ROLE_ADMIN)
    def change_role(user_id):
        user = db.get_or_404(User, user_id)
        new_role = request.form.get("role")
        if new_role not in VALID_ROLES:
            abort(400)
        if user.id == current_user.id and new_role != ROLE_ADMIN:
            flash("Kamu tidak bisa menurunkan role dirimu sendiri.", "danger")
            return redirect(url_for("admin_users"))
        user.role = new_role
        db.session.commit()
        flash(f"Role {user.username} diubah menjadi {new_role}.", "success")
        return redirect(url_for("admin_users"))

    # ---------- Error handler ----------
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    # ---------- CLI ----------
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.password_option()
    def create_admin(username, password):
        """Membuat akun admin baru."""
        if User.query.filter_by(username=username).first():
            click.echo("Username sudah dipakai.")
            return
        user = User(username=username, role=ROLE_ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin '{username}' berhasil dibuat.")

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
