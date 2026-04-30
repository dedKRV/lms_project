from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from data import db_session
from data.users import User


def init_profile_routes(app):
    @app.route("/profile")
    @login_required
    def my_profile():
        return redirect(url_for("view_profile", user_id=current_user.id))

    @app.route("/profile/<int:user_id>")
    @login_required
    def view_profile(user_id):
        db_sess = db_session.create_session()
        user = db_sess.get(User, user_id)

        if not user:
            db_sess.close()
            abort(404)

        display_score = None
        total_score = None
        course_scores = []

        if user.role == "student":
            display_score = user.get_display_score()
            total_score = user.get_total_score()
            course_scores = user.get_course_scores()

        db_sess.close()

        is_own_profile = (current_user.id == user_id)
        age = user.get_age()

        return render_template(
            "profile.html",
            user=user,
            display_score=display_score,
            total_score=total_score,
            course_scores=course_scores,
            is_own_profile=is_own_profile,
            age=age
        )

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def edit_profile():
        db_sess = db_session.create_session()
        user = db_sess.get(User, current_user.id)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            birth_date_str = request.form.get("birth_date", "").strip()

            if not name:
                flash("Имя не может быть пустым")
                db_sess.close()
                return redirect(url_for("edit_profile"))

            user.name = name

            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    if birth_date > today:
                        flash("Дата рождения не может быть в будущем")
                        db_sess.close()
                        return redirect(url_for("edit_profile"))
                    if today.year - birth_date.year > 150:
                        flash("Некорректная дата рождения")
                        db_sess.close()
                        return redirect(url_for("edit_profile"))
                    user.birth_date = birth_date
                except ValueError:
                    flash("Неверный формат даты")
                    db_sess.close()
                    return redirect(url_for("edit_profile"))
            else:
                user.birth_date = None

            db_sess.commit()
            db_sess.close()
            flash("Профиль обновлён")
            return redirect(url_for("view_profile", user_id=current_user.id))

        db_sess.close()
        return render_template("edit_profile.html", user=user)