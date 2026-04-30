import json as json_lib
import requests
import urllib3
from flask import request, jsonify
from flask_login import login_required, current_user

from data import db_session
from data.submissions import Submission

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEEPSEEK_API_KEY = ""

API_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Ты — строгий преподаватель программирования. Проверяешь код студента.

ВАЖНЫЕ ПРАВИЛА:
- Ты НЕ решаешь задание за студента
- Ты НЕ пишешь правильный код и НЕ показываешь как именно исправить
- Ты только указываешь на ошибки и объясняешь в чём проблема
- Студент должен сам догадаться как это исправить
- Если нет ни логических ошибок ни нарушений PEP8 — напиши ТОЛЬКО одно слово: "Правильно!" и больше ничего
- Если код полностью правильный — напиши ТОЛЬКО одно слово: "Правильно!" и больше ничего
- СТРОГО ЗАПРЕЩЕНО писать ИТОГ "неправильно" если в пунктах 2 и 3 нет ни одной ошибки
- СТРОГО ЗАПРЕЩЕНО критиковать названия переменных, функций, классов и маршрутов — это личный выбор разработчика
- Названия функций и переменных НЕ являются ошибкой если написаны в snake_case — даже если название кажется тебе нелогичным

Если код НЕ правильный, структура ответа:

1. ИТОГ: неправильно / частично правильно

2. ОШИБКИ ЛОГИКИ (если есть):
— только реальные ошибки: неверный алгоритм, неправильный результат, падение программы
— НЕ считай ошибкой логики несоответствие названия функции её содержимому

3. НАРУШЕНИЯ PEP8 (если есть):
— только: отступы, пробелы, пустые строки, длина строк, порядок импортов
— НЕ упоминай названия переменных и функций вообще

4. ЧТО СДЕЛАНО ВЕРНО (если есть):
— коротко, 1-2 пункта

Отвечай на русском. Будь конкретным и кратким."""


def init_ai_routes(app):

    @app.route("/submission/<int:submission_id>/check", methods=["POST"])
    @login_required
    def check_submission(submission_id):
        db_sess = db_session.create_session()
        submission = db_sess.get(Submission, submission_id)

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
            last_error = None
            response = None

            for attempt in range(3):
                try:
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
                            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json; charset=utf-8"
                        },
                        data=body,
                        timeout=30,
                        verify=False
                    )
                    break
                except Exception as e:
                    last_error = e
                    continue
            else:
                return jsonify({
                    "error": f"Не удалось подключиться после 3 попыток: {str(last_error)}"
                }), 500

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