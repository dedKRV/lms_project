from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from data import db_session
from data.submissions import Submission

# API ключ
DEEPSEEK_API_KEY = ""

# URL API
API_URL = ""

# Название модели
MODEL = ""

# Системный промпт
SYSTEM_PROMPT = ""

def init_ai_routes(app):
    @app.route("/submission/<int:submission_id>/check", methods=["POST"])
    @login_required
    # Замени эту функцию (check_submission)
    def check_submission(submission_id):
        db_sess = db_session.create_session()
        submission = db_sess.query(Submission).get(submission_id)

        if not submission:
            db_sess.close()
            return jsonify({"error": "Решение не найдено"}), 404

        if current_user.role == "student" and submission.student_id != current_user.id:
            db_sess.close()
            return jsonify({"error": "Доступ запрещен"}), 403

        if current_user.role == "teacher" and submission.block.lesson.course.teacher_id != current_user.id:
            db_sess.close()
            return jsonify({"error": "Доступ запрещен"}), 403

        code = submission.code
        block_title = submission.block.title

        db_sess.close()

        ai_response = f"Здесь будет ответ нейросети на задание '{block_title}'"

        return jsonify({"response": ai_response})