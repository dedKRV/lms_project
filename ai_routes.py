import uuid
import json as json_lib
import requests
import urllib3
from flask import request, jsonify
from flask_login import login_required, current_user

from data import db_session
from data.submissions import Submission

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGACHAT_AUTH_KEY = "MDE5ZGYzYTgtYjJiZS03NGRlLWJiNDQtZWE3NDEwMTkyNzQ5OmFlODRjZTUwLTVkYzUtNDAyYS04NjQ4LThkMTg3YWRlNWNjZA=="

TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
MODEL = "GigaChat"

SYSTEM_PROMPT = """Ты — строгий преподаватель программирования. Проверяешь код студента.

ВАЖНЫЕ ПРАВИЛА:
- Ты НЕ решаешь задание за студента
- Ты НЕ пишешь правильный код и НЕ показываешь как именно исправить
- Ты только указываешь на ошибки и объясняешь в чём проблема
- Студент должен сам догадаться как это исправить
- СТРОГО ЗАПРЕЩЕНО критиковать названия переменных, функций, классов и маршрутов
- Названия функций и переменных НЕ являются ошибкой если написаны в snake_case

ПРАВИЛА ВЫВОДА — СТРОГО ОДНО ИЗ ТРЁХ:

Если код полностью правильный и нет никаких ошибок и нарушений:
→ напиши ТОЛЬКО одно слово: Правильно!
→ больше ничего не пиши, никаких пунктов

Если есть ошибки — напиши строго по этой структуре и больше ничего:

ИТОГ: неправильно / частично правильно

ОШИБКИ ЛОГИКИ (если есть):
— только реальные ошибки алгоритма или логики работы программы

НАРУШЕНИЯ PEP8 (если есть):
— только: отступы, пробелы, пустые строки, длина строк, порядок импортов
— НЕ упоминай названия переменных и функций

ЧТО СДЕЛАНО ВЕРНО (если есть):
— коротко, 1-2 пункта

Отвечай на русском. Никогда не пиши одновременно и ошибки и "Правильно!" — это взаимоисключающие варианты."""


def get_gigachat_token():
    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"scope": "GIGACHAT_API_PERS"},
        verify=False,
        timeout=15
    )
    response.raise_for_status()
    return response.json()["access_token"]


def init_ai_routes(app):

    @app.route("/submission/<int:submission_id>/check", methods=["POST"])
    @login_required
    def check_submission(submission_id):
        db_sess = db_session.create_session()
        submission = db_sess.query(Submission).get(submission_id)

        if not submission:
            db_sess.close()
            return jsonify({"error": "Решение не найдено"}), 404

        if current_user.role == "student" and submission.student_id != current_user.id:
            db_sess.close()
            return jsonify({"error": "Доступ запрещен"}), 403

        if current_user.role == "teacher":
            if submission.block.lesson.course.teacher_id != current_user.id:
                db_sess.close()
                return jsonify({"error": "Доступ запрещен"}), 403

        code = submission.code
        block_title = submission.block.title
        block_content = submission.block.content

        db_sess.close()

        user_message = (
            f"Задание: {block_title}\n\n"
            f"Описание задания:\n{block_content}\n\n"
            f"Код студента:\n{code}"
        )

        try:
            token = get_gigachat_token()

            body = json_lib.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }, ensure_ascii=False).encode("utf-8")

            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                data=body,
                verify=False,
                timeout=30
            )

            if response.status_code != 200:
                return jsonify({
                    "error": f"Ошибка API: {response.status_code} — {response.text}"
                }), 500

            data = response.json()
            ai_text = data["choices"][0]["message"]["content"]
            return jsonify({"response": ai_text})

        except requests.exceptions.Timeout:
            return jsonify({
                "error": "Таймаут: нейросеть не ответила за 30 секунд"
            }), 504
        except Exception as e:
            return jsonify({"error": f"Внутренняя ошибка: {str(e)}"}), 500