import os
from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user

from data import db_session
from data.courses import Course
from data.enrollments import Enrollment
from data.lessons import Lesson
from data.lesson_files import LessonFile
from data.users import User
from data.submissions import Submission
from decorators import teacher_required
from sqlalchemy.orm import joinedload


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


def format_score(score):
    return f"{score // 1000}.{score % 1000:03d}"


def init_course_routes(app):
    @app.route("/api/search-student")
    @teacher_required
    def search_student():
        email = request.args.get("email", "").strip()

        if not email or len(email) < 3:
            return jsonify({"error": "Введите минимум 3 символа"})

        db_sess = db_session.create_session()
        student = db_sess.query(User).filter(
            User.email.like(f"%{email}%"),
            User.role == "student"
        ).first()
        db_sess.close()

        if not student:
            return jsonify({"error": "Студент не найден"})

        return jsonify({
            "id": student.id,
            "name": student.name,
            "email": student.email
        })

    @app.route("/dashboard")
    @login_required
    def dashboard():
        db_sess = db_session.create_session()
        if current_user.role == "student":
            enrollments = db_sess.query(Enrollment).filter_by(student_id=current_user.id).all()
            courses = []
            for e in enrollments:
                course = e.course
                score = get_student_course_score(db_sess, current_user.id, course.id)
                courses.append({
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'display_score': format_score(score)
                })
            db_sess.close()
            return render_template("student_dashboard.html", courses=courses, user_name=current_user.name)

        db_sess.close()
        return render_template("teacher_dashboard.html", user_name=current_user.name)

    @app.route("/teacher/courses")
    @teacher_required
    def teacher_courses():
        db_sess = db_session.create_session()
        courses = db_sess.query(Course).filter_by(teacher_id=current_user.id).all()

        courses_data = []
        for course in courses:
            enrollments = db_sess.query(Enrollment).filter_by(course_id=course.id).all()
            students_count = len(enrollments)
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'students_count': students_count
            })

        db_sess.close()
        return render_template("teacher_courses.html", courses=courses_data)

    @app.route("/teacher/course/<int:course_id>/students")
    @teacher_required
    def course_students(course_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        enrollments = db_sess.query(Enrollment).filter_by(course_id=course_id).all()

        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            score = get_student_course_score(db_sess, student.id, course_id)
            students_data.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'score': score,
                'display_score': format_score(score)
            })

        db_sess.close()
        return render_template("course_students.html", course=course, students=students_data)

    @app.route("/teacher/course/<int:course_id>/remove-student/<int:student_id>")
    @teacher_required
    def remove_student(course_id, student_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        enrollment = db_sess.query(Enrollment).filter_by(
            student_id=student_id, course_id=course_id
        ).first()

        if enrollment:
            from notification_routes import create_notification
            student = db_sess.get(User, student_id)
            student_name = student.name
            create_notification(
                student_id,
                f"Вы были отчислены с курса '{course.title}'",
                "/courses"
            )
            db_sess.delete(enrollment)
            db_sess.commit()
            flash(f"Студент {student_name} отчислен с курса")

        db_sess.close()
        return redirect(url_for("course_students", course_id=course_id))

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
            db_sess.close()
            flash("Курс успешно создан")
            return redirect(url_for("teacher_courses"))

        return render_template("create_course.html")

    @app.route("/teacher/course/<int:course_id>/edit", methods=["GET", "POST"])
    @teacher_required
    def edit_course(course_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        if request.method == "POST":
            course.title = request.form["title"]
            course.description = request.form["description"]
            db_sess.commit()
            db_sess.close()
            flash("Курс обновлен")
            return redirect(url_for("teacher_courses"))

        db_sess.close()
        return render_template("edit_course.html", course=course)

    @app.route("/teacher/course/<int:course_id>/delete")
    @teacher_required
    def delete_course(course_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        db_sess.delete(course)
        db_sess.commit()
        db_sess.close()
        flash("Курс удален")
        return redirect(url_for("teacher_courses"))

    @app.route("/courses")
    @login_required
    def all_courses():
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()
        enrollments = db_sess.query(Enrollment).filter_by(student_id=current_user.id).all()

        courses = []
        for e in enrollments:
            course = e.course
            score = get_student_course_score(db_sess, current_user.id, course.id)
            courses.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'display_score': format_score(score)
            })

        db_sess.close()
        return render_template("all_courses.html", courses=courses)

    @app.route("/teacher/course/<int:course_id>/enroll-student", methods=["GET", "POST"])
    @teacher_required
    def enroll_student(course_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        if course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("teacher_courses"))

        if request.method == "POST":
            email = request.form.get("email", "").strip()
            confirm = request.form.get("confirm", "")

            if not email:
                db_sess.close()
                flash("Введите email студента")
                return redirect(url_for("enroll_student", course_id=course_id))

            student = db_sess.query(User).filter(User.email == email).first()

            if not student:
                db_sess.close()
                flash("Студент с таким email не найден")
                return redirect(url_for("enroll_student", course_id=course_id))

            if student.role == "teacher":
                db_sess.close()
                flash("Нельзя записать преподавателя на курс")
                return redirect(url_for("enroll_student", course_id=course_id))

            if db_sess.query(Enrollment).filter_by(student_id=student.id, course_id=course_id).first():
                db_sess.close()
                flash("Этот студент уже записан на курс")
                return redirect(url_for("enroll_student", course_id=course_id))

            if confirm == "yes":
                db_sess.add(Enrollment(student_id=student.id, course_id=course_id))
                db_sess.commit()

                from notification_routes import create_notification
                create_notification(
                    student.id,
                    f"Преподаватель {current_user.name} записал вас на курс '{course.title}'",
                    f"/course/{course.id}"
                )

                db_sess.close()
                flash(f"Студент {student.name} ({student.email}) записан на курс")
                return redirect(url_for("teacher_courses"))

        db_sess.close()
        return render_template("enroll_student.html", course=course)

    @app.route("/enroll/<int:course_id>")
    @login_required
    def enroll(course_id):
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()

        course = db_sess.get(Course, course_id)
        if not course:
            db_sess.close()
            abort(404)

        if db_sess.query(Enrollment).filter_by(student_id=current_user.id, course_id=course_id).first():
            db_sess.close()
            flash("Вы уже записаны на этот курс")
            return redirect(url_for("all_courses"))

        db_sess.add(Enrollment(student_id=current_user.id, course_id=course_id))
        db_sess.commit()
        db_sess.close()
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
            db_sess.close()
            flash("Вы не записаны на этот курс")
            return redirect(url_for("all_courses"))

        db_sess.delete(enrollment)
        db_sess.commit()
        db_sess.close()
        flash("Вы отписались от курса")
        return redirect(url_for("all_courses"))

    @app.route("/course/<int:course_id>")
    @login_required
    def course_detail(course_id):
        db_sess = db_session.create_session()
        course = db_sess.get(Course, course_id)

        if not course:
            db_sess.close()
            abort(404)

        enrolled = False
        if current_user.role == "student":
            enrolled = db_sess.query(Enrollment).filter_by(
                student_id=current_user.id, course_id=course.id
            ).first() is not None

        course_data = {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'teacher': {
                'name': course.teacher.name,
                'id': course.teacher.id
            },
            'lessons': []
        }

        for lesson in course.lessons:
            course_data['lessons'].append({
                'id': lesson.id,
                'title': lesson.title,
                'content': lesson.content
            })

        db_sess.close()
        return render_template("course_detail.html", course=course_data, enrolled=enrolled)