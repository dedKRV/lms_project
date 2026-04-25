import os
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from data import db_session
from data.courses import Course
from data.enrollments import Enrollment
from data.lessons import Lesson
from data.lesson_files import LessonFile
from decorators import teacher_required


def init_course_routes(app):
    @app.route("/dashboard")
    @login_required
    def dashboard():
        db_sess = db_session.create_session()
        if current_user.role == "student":
            enrollments = db_sess.query(Enrollment).filter_by(student_id=current_user.id).all()
            courses = [e.course for e in enrollments]
            return render_template("student_dashboard.html", courses=courses, user_name=current_user.name)

        return render_template("teacher_dashboard.html", user_name=current_user.name)

    @app.route("/teacher/courses")
    @teacher_required
    def teacher_courses():
        db_sess = db_session.create_session()
        courses = db_sess.query(Course).filter_by(teacher_id=current_user.id).all()
        return render_template("teacher_courses.html", courses=courses)

    @app.route("/teacher/create-course", methods=["GET", "POST"])
    @teacher_required
    def create_course():
        if request.method == "POST":
            db_sess = db_session.create_session()
            course = Course(
                title=request.form["title"],
                description=request.form["description"],
                teacher_id=current_user.id
            )
            db_sess.add(course)
            db_sess.commit()
            flash("Курс успешно создан")
            return redirect(url_for("teacher_courses"))

        return render_template("create_course.html")

    @app.route("/teacher/course/<int:course_id>/edit", methods=["GET", "POST"])
    @teacher_required
    def edit_course(course_id):
        db_sess = db_session.create_session()
        course = db_sess.query(Course).get(course_id)

        if not course:
            abort(404)

        if course.teacher_id != current_user.id:
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        if request.method == "POST":
            course.title = request.form["title"]
            course.description = request.form["description"]
            db_sess.commit()
            flash("Курс обновлен")
            return redirect(url_for("teacher_courses"))

        return render_template("edit_course.html", course=course)

    @app.route("/teacher/course/<int:course_id>/delete")
    @teacher_required
    def delete_course(course_id):
        db_sess = db_session.create_session()
        course = db_sess.query(Course).get(course_id)

        if not course:
            abort(404)

        if course.teacher_id != current_user.id:
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        db_sess.delete(course)
        db_sess.commit()
        flash("Курс удален")
        return redirect(url_for("teacher_courses"))

    @app.route("/courses")
    @login_required
    def all_courses():
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()
        courses = db_sess.query(Course).all()
        enrollments = db_sess.query(Enrollment).filter_by(student_id=current_user.id).all()
        enrolled_ids = [e.course_id for e in enrollments]

        return render_template("all_courses.html", courses=courses, enrolled_course_ids=enrolled_ids)

    @app.route("/enroll/<int:course_id>")
    @login_required
    def enroll(course_id):
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()

        course = db_sess.query(Course).get(course_id)
        if not course:
            abort(404)

        if db_sess.query(Enrollment).filter_by(student_id=current_user.id, course_id=course_id).first():
            flash("Вы уже записаны на этот курс")
            return redirect(url_for("all_courses"))

        db_sess.add(Enrollment(student_id=current_user.id, course_id=course_id))
        db_sess.commit()
        flash("Вы успешно записаны на курс")
        return redirect(url_for("all_courses"))

    @app.route("/unenroll/<int:course_id>")
    @login_required
    def unenroll(course_id):
        if current_user.role != "student":
            flash("Только студенты могут отписываться")
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()
        enrollment = db_sess.query(Enrollment).filter_by(student_id=current_user.id, course_id=course_id).first()

        if not enrollment:
            flash("Вы не записаны на этот курс")
            return redirect(url_for("all_courses"))

        db_sess.delete(enrollment)
        db_sess.commit()
        flash("Вы отписались от курса")
        return redirect(url_for("all_courses"))

    @app.route("/course/<int:course_id>")
    @login_required
    def course_detail(course_id):
        db_sess = db_session.create_session()
        course = db_sess.query(Course).get(course_id)

        if not course:
            abort(404)

        enrolled = False
        if current_user.role == "student":
            enrolled = db_sess.query(Enrollment).filter_by(
                student_id=current_user.id, course_id=course.id
            ).first() is not None

        return render_template("course_detail.html", course=course, enrolled=enrolled)