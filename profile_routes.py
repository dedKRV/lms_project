from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from data import db_session
from data.users import User
from data.submissions import Submission
from data.enrollments import Enrollment


def get_student_course_score(db_sess, student_id, course_id):
    total_score = 0
    submissions = db_sess.query(Submission).filter(
        Submission.student_id == student_id,
        Submission.score.isnot(None)
    ).all()

    for submission in submissions:
        block = submission.block
        if block and block.lesson and block.lesson.course_id == course_id:
            total_score += submission.score

    return total_score


def get_student_total_score(db_sess, student_id):
    total_score = 0
    submissions = db_sess.query(Submission).filter(
        Submission.student_id == student_id,
        Submission.score.isnot(None)
    ).all()

    for submission in submissions:
        total_score += submission.score

    return total_score


def format_score(score):
    return f"{score // 1000}.{score % 1000:03d}"


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
            total_score = get_student_total_score(db_sess, user.id)
            display_score = format_score(total_score)

            enrollments = db_sess.query(Enrollment).filter_by(student_id=user.id).all()
            for enrollment in enrollments:
                course = enrollment.course
                score = get_student_course_score(db_sess, user.id, course.id)
                if score > 0:
                    course_scores.append({
                        'title': course.title,
                        'score': score,
                        'display_score': format_score(score)
                    })

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