import os
from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.courses import Course
from data.lessons import Lesson
from data.lesson_files import LessonFile
from decorators import teacher_required


def init_lesson_routes(app):
    @app.route("/teacher/course/<int:course_id>/lesson/add", methods=["GET", "POST"])
    @teacher_required
    def add_lesson(course_id):
        db_sess = db_session.create_session()
        course = db_sess.query(Course).get(course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        if request.method == "POST":
            lesson = Lesson(
                title=request.form["title"],
                content=request.form.get("content", ""),
                course_id=course.id
            )
            db_sess.add(lesson)
            db_sess.commit()
            lesson_id = lesson.id
            db_sess.close()

            flash("Урок добавлен")
            return redirect(url_for("lesson_view", lesson_id=lesson_id))

        db_sess.close()
        return render_template("add_lesson.html", course=course)

    @app.route("/teacher/lesson/<int:lesson_id>/edit", methods=["GET", "POST"])
    @teacher_required
    def edit_lesson(lesson_id):
        db_sess = db_session.create_session()
        lesson = db_sess.query(Lesson).get(lesson_id)

        if not lesson:
            db_sess.close()
            abort(404)

        course_id = lesson.course_id

        course = db_sess.query(Course).get(course_id)
        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            lesson.title = request.form["title"]
            lesson.content = request.form.get("content", "")
            db_sess.commit()
            db_sess.close()
            flash("Урок обновлен")
            return redirect(url_for("lesson_view", lesson_id=lesson_id))

        lesson_data = {
            'id': lesson.id,
            'title': lesson.title,
            'content': lesson.content,
            'course_id': course_id
        }

        db_sess.close()
        return render_template("edit_lesson.html", lesson=lesson_data)

    @app.route("/teacher/lesson/<int:lesson_id>/delete")
    @teacher_required
    def delete_lesson(lesson_id):
        db_sess = db_session.create_session()
        lesson = db_sess.query(Lesson).get(lesson_id)

        if not lesson:
            db_sess.close()
            abort(404)

        course_id = lesson.course_id

        if lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Вы не можете удалить этот урок")
            return redirect(url_for("dashboard"))

        for file in lesson.files:
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        db_sess.delete(lesson)
        db_sess.commit()
        db_sess.close()

        flash("Урок удален")
        return redirect(url_for("course_detail", course_id=course_id))

    @app.route("/uploads/<filename>")
    @login_required
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)