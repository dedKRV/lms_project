import os
from flask import render_template, request, redirect, url_for, flash, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.lessons import Lesson
from data.lesson_blocks import LessonBlock
from data.block_images import BlockImage
from data.block_files import BlockFile
from data.submissions import Submission
from data.users import User
from decorators import teacher_required
import datetime


def get_block_folder(block_id):
    block_folder = os.path.join(current_app.config["FILES_FOLDER"], str(block_id))
    os.makedirs(block_folder, exist_ok=True)
    return block_folder


def init_block_routes(app):
    @app.route("/lesson/<int:lesson_id>")
    @login_required
    def lesson_view(lesson_id):
        db_sess = db_session.create_session()
        lesson = db_sess.get(Lesson, lesson_id)

        if not lesson:
            db_sess.close()
            abort(404)

        course = lesson.course
        enrolled = True

        if current_user.role == "student":
            from data.enrollments import Enrollment
            enrolled = db_sess.query(Enrollment).filter_by(
                student_id=current_user.id, course_id=course.id
            ).first() is not None

            if not enrolled:
                db_sess.close()
                flash("Запишитесь на курс чтобы просматривать уроки")
                return redirect(url_for("course_detail", course_id=course.id))

        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        blocks = sorted(lesson.blocks, key=lambda x: x.order)
        db_sess.close()
        return render_template("lesson_view.html", lesson=lesson, blocks=blocks)

    @app.route("/block/<int:block_id>")
    @login_required
    def block_view(block_id):
        db_sess = db_session.create_session()
        block = db_sess.get(LessonBlock, block_id)

        if not block:
            db_sess.close()
            abort(404)

        lesson = block.lesson
        course = lesson.course

        if current_user.role == "student":
            from data.enrollments import Enrollment
            enrolled = db_sess.query(Enrollment).filter_by(
                student_id=current_user.id, course_id=course.id
            ).first() is not None

            if not enrolled:
                db_sess.close()
                flash("Запишитесь на курс чтобы просматривать уроки")
                return redirect(url_for("course_detail", course_id=course.id))

        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        block_data = {
            'id': block.id,
            'title': block.title,
            'content': block.content,
            'block_type': block.block_type,
            'lesson_id': lesson.id
        }

        images = list(block.images)
        files = list(block.files)

        submissions_data = []
        if block.block_type == 'assignment':
            if current_user.role == "student":
                subs = db_sess.query(Submission).filter_by(
                    block_id=block_id, student_id=current_user.id
                ).order_by(Submission.submitted_at.desc()).all()
                for sub in subs:
                    submissions_data.append({
                        'id': sub.id,
                        'code': sub.code,
                        'status': sub.status,
                        'score': sub.score,
                        'feedback': sub.feedback,
                        'submitted_at': sub.submitted_at,
                        'graded_at': sub.graded_at,
                        'student_name': None
                    })
            else:
                subs = db_sess.query(Submission).filter_by(
                    block_id=block_id
                ).order_by(Submission.submitted_at.desc()).all()
                for sub in subs:
                    submissions_data.append({
                        'id': sub.id,
                        'code': sub.code,
                        'status': sub.status,
                        'score': sub.score,
                        'feedback': sub.feedback,
                        'submitted_at': sub.submitted_at,
                        'graded_at': sub.graded_at,
                        'student_id': sub.student_id,
                        'student_name': sub.student.name,
                        'student_email': sub.student.email
                    })

        db_sess.close()
        return render_template("block_view.html", block=block_data, images=images, files=files,
                               submissions=submissions_data)

    @app.route("/teacher/lesson/<int:lesson_id>/block/add/<block_type>", methods=["GET", "POST"])
    @teacher_required
    def add_block(lesson_id, block_type):
        db_sess = db_session.create_session()
        lesson = db_sess.get(Lesson, lesson_id)

        if not lesson:
            db_sess.close()
            abort(404)

        if lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            max_order = db_sess.query(LessonBlock).filter_by(lesson_id=lesson_id).count()

            block = LessonBlock(
                lesson_id=lesson_id,
                block_type=block_type,
                title=request.form.get("title"),
                content=request.form.get("content"),
                order=max_order
            )
            db_sess.add(block)
            db_sess.commit()

            block_id = block.id
            block_folder = get_block_folder(block_id)

            images = request.files.getlist("images")
            if images:
                for file in images:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(block_folder, filename)
                        file.save(file_path)

                        img = BlockImage(block_id=block.id, filename=filename)
                        db_sess.add(img)

            uploaded_files = request.files.getlist("files")
            if uploaded_files:
                for file in uploaded_files:
                    if file and file.filename:
                        original_name = file.filename
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(block_folder, filename)
                        file.save(file_path)

                        ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
                        file_type = ext if ext else 'unknown'

                        file_record = BlockFile(
                            block_id=block.id,
                            filename=filename,
                            original_name=original_name,
                            file_type=file_type
                        )
                        db_sess.add(file_record)

            db_sess.commit()
            db_sess.close()
            flash("Блок добавлен")
            return redirect(url_for("block_view", block_id=block_id))

        db_sess.close()
        return render_template("add_block.html", lesson=lesson, block_type=block_type)

    @app.route("/teacher/block/<int:block_id>/edit", methods=["GET", "POST"])
    @teacher_required
    def edit_block(block_id):
        db_sess = db_session.create_session()
        block = db_sess.get(LessonBlock, block_id)

        if not block:
            db_sess.close()
            abort(404)

        if block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            block.title = request.form.get("title")
            block.content = request.form.get("content")

            block_folder = get_block_folder(block_id)

            images = request.files.getlist("images")
            for file in images:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(block_folder, filename)
                    file.save(file_path)

                    img = BlockImage(block_id=block.id, filename=filename)
                    db_sess.add(img)

            new_files = request.files.getlist("files")
            for file in new_files:
                if file and file.filename:
                    original_name = file.filename
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(block_folder, filename)
                    file.save(file_path)

                    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
                    file_type = ext if ext else 'unknown'

                    file_record = BlockFile(
                        block_id=block.id,
                        filename=filename,
                        original_name=original_name,
                        file_type=file_type
                    )
                    db_sess.add(file_record)

            db_sess.commit()
            db_sess.close()
            flash("Блок обновлен")
            return redirect(url_for("block_view", block_id=block_id))

        images = []
        for img in block.images:
            images.append({
                'id': img.id,
                'filename': img.filename
            })

        files = []
        for f in block.files:
            files.append({
                'id': f.id,
                'filename': f.filename,
                'original_name': f.original_name,
                'file_type': f.file_type
            })

        block_data = {
            'id': block.id,
            'title': block.title,
            'content': block.content,
            'lesson_id': block.lesson_id
        }

        db_sess.close()
        return render_template("edit_block.html", block=block_data, images=images, files=files)

    @app.route("/teacher/block/<int:block_id>/delete")
    @teacher_required
    def delete_block(block_id):
        db_sess = db_session.create_session()
        block = db_sess.get(LessonBlock, block_id)

        if not block:
            db_sess.close()
            abort(404)

        if block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        lesson_id = block.lesson_id

        import shutil
        block_folder = get_block_folder(block_id)
        if os.path.exists(block_folder):
            shutil.rmtree(block_folder)

        db_sess.delete(block)
        db_sess.commit()
        db_sess.close()
        flash("Блок удален")
        return redirect(url_for("lesson_view", lesson_id=lesson_id))

    @app.route("/teacher/image/<int:image_id>/delete")
    @teacher_required
    def delete_image(image_id):
        db_sess = db_session.create_session()
        img = db_sess.get(BlockImage, image_id)

        if not img:
            db_sess.close()
            abort(404)

        if img.block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        block_id = img.block_id
        block_folder = get_block_folder(block_id)
        file_path = os.path.join(block_folder, img.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db_sess.delete(img)
        db_sess.commit()
        db_sess.close()
        flash("Изображение удалено")
        return redirect(url_for("edit_block", block_id=block_id))

    @app.route("/teacher/file/<int:file_id>/delete")
    @teacher_required
    def delete_file(file_id):
        db_sess = db_session.create_session()
        file_record = db_sess.get(BlockFile, file_id)

        if not file_record:
            db_sess.close()
            abort(404)

        if file_record.block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        block_id = file_record.block_id
        block_folder = get_block_folder(block_id)
        file_path = os.path.join(block_folder, file_record.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db_sess.delete(file_record)
        db_sess.commit()
        db_sess.close()
        flash("Файл удален")
        return redirect(url_for("edit_block", block_id=block_id))

    @app.route("/download/block/<int:block_id>/<filename>")
    @login_required
    def download_file(block_id, filename):
        db_sess = db_session.create_session()
        block = db_sess.get(LessonBlock, block_id)

        if not block:
            db_sess.close()
            abort(404)

        if current_user.role == "student":
            from data.enrollments import Enrollment
            enrolled = db_sess.query(Enrollment).filter_by(
                student_id=current_user.id, course_id=block.lesson.course_id
            ).first() is not None
            if not enrolled:
                db_sess.close()
                flash("Доступ запрещен")
                return redirect(url_for("dashboard"))

        db_sess.close()

        block_folder = get_block_folder(block_id)
        return send_from_directory(block_folder, filename, as_attachment=True)

    @app.route("/lesson/<int:lesson_id>/block/<int:block_id>/submit", methods=["POST"])
    @login_required
    def submit_assignment(lesson_id, block_id):
        if current_user.role != "student":
            flash("Только студенты могут отправлять задания")
            return redirect(url_for("dashboard"))

        db_sess = db_session.create_session()

        code = request.form.get("code")
        action = request.form.get("action")

        submission = Submission(
            block_id=block_id,
            student_id=current_user.id,
            code=code,
            status=action
        )
        db_sess.add(submission)
        db_sess.commit()

        if action == "submit":
            from notification_routes import create_notification
            block = db_sess.get(LessonBlock, block_id)
            teacher_id = block.lesson.course.teacher_id
            create_notification(
                teacher_id,
                f"Студент {current_user.name} сдал задание '{block.title}'",
                f"/submission/{submission.id}"
            )

        db_sess.close()

        if action == "submit":
            flash("Решение отправлено на проверку")
        else:
            flash("Черновик сохранен")

        return redirect(url_for("block_view", block_id=block_id))

    @app.route("/teacher/submission/<int:submission_id>/grade", methods=["POST"])
    @teacher_required
    def grade_submission(submission_id):
        db_sess = db_session.create_session()
        submission = db_sess.get(Submission, submission_id)

        if not submission:
            db_sess.close()
            abort(404)

        if submission.block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        score = request.form.get("score", type=int)
        if score is None or score < 0 or score > 100:
            db_sess.close()
            flash("Оценка должна быть от 0 до 100")
            return redirect(url_for("block_view", block_id=submission.block_id))

        submission.score = score
        submission.feedback = request.form.get("feedback", "")
        submission.graded_at = datetime.datetime.now()

        db_sess.commit()

        from notification_routes import create_notification
        block = submission.block
        create_notification(
            submission.student_id,
            f"Преподаватель проверил ваше задание '{block.title}'. Оценка: {score}/100",
            f"/submission/{submission.id}"
        )

        block_id = submission.block_id
        db_sess.close()

        flash("Оценка сохранена")
        return redirect(url_for("block_view", block_id=block_id))

    @app.route("/submission/<int:submission_id>")
    @login_required
    def view_submission(submission_id):
        db_sess = db_session.create_session()
        submission = db_sess.get(Submission, submission_id)

        if not submission:
            db_sess.close()
            abort(404)

        block = submission.block
        lesson = block.lesson
        course = lesson.course

        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        if current_user.role == "student" and submission.student_id != current_user.id:
            db_sess.close()
            flash("Доступ запрещен")
            return redirect(url_for("dashboard"))

        submission_data = {
            'id': submission.id,
            'code': submission.code,
            'status': submission.status,
            'score': submission.score,
            'feedback': submission.feedback,
            'submitted_at': submission.submitted_at,
            'graded_at': submission.graded_at,
            'student_name': submission.student.name,
            'student_email': submission.student.email,
            'block_id': block.id,
            'block_title': block.title,
            'lesson_id': lesson.id,
            'lesson_title': lesson.title
        }

        db_sess.close()
        return render_template("view_submission.html", submission=submission_data)