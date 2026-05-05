# lms_project
 
> LMS на Flask с AI-проверкой кода через GigaChat
 
## что это
 
Веб-платформа для обучения программированию. Преподаватели создают курсы с уроками и заданиями, студенты их проходят и сдают код — а GigaChat сразу говорит что не так, не давая готового ответа.
 
## стек
 
- **Flask 3.1** + SQLAlchemy + SQLite
- **Flask-Login** — авторизация, роли (teacher / student)
- **GigaChat API** — AI-проверка кода студентов
- **Jinja2** — шаблоны
## запуск
 
```bash
git clone https://github.com/dedKRV/lms_project.git
cd lms_project
pip install -r requirements.txt
python main.py
```
 
## GigaChat
 
В `ai_routes.py` замени ключ:
 
```python
GIGACHAT_AUTH_KEY = "твой_ключ"
```
 
Ключ — на [developers.sber.ru](https://developers.sber.ru/studio/)
 
## структура
 
```
lms_project/
│
├── main.py                    # точка входа — Flask app, регистрация/логин/логаут
├── main_user.py               # скрипт для создания тестового преподавателя
│
├── ai_routes.py               # POST /submission/<id>/check — проверка кода через GigaChat
├── course_routes.py           # CRUD курсов, дашборд, запись студентов
├── lesson_routes.py           # CRUD уроков внутри курса
├── block_routes.py            # CRUD блоков (задания/контент) внутри урока
├── notification_routes.py     # уведомления: список, отметить прочитанным
├── profile_routes.py          # страница профиля пользователя
│
├── decorators.py              # @teacher_required — доступ только для преподавателей
├── context_processors.py      # get_user_by_id / get_user_by_email в шаблонах
│
├── data/                      # модели SQLAlchemy и сессии БД
│   ├── db_session.py          # инициализация SQLite, создание сессий
│   ├── users.py               # модель User (id, name, email, role, hashed_password)
│   ├── courses.py             # модель Course (title, description, teacher_id)
│   ├── lessons.py             # модель Lesson (title, course_id, order)
│   ├── blocks.py              # модель Block (title, content, lesson_id, type)
│   ├── submissions.py         # модель Submission (code, student_id, block_id, status)
│   ├── notifications.py       # модель Notification (user_id, text, is_read)
│   ├── add_user.py            # WTForms форма регистрации
│   └── login_form.py          # WTForms форма входа
│
├── templates/                 # HTML-шаблоны Jinja2
│   ├── base.html              # базовый шаблон (навбар, флеш-сообщения)
│   ├── index.html             # лендинг
│   ├── login.html / register.html
│   ├── dashboard.html         # главная после логина
│   ├── course_*.html          # страницы курсов
│   ├── lesson_*.html          # страницы уроков
│   ├── block_*.html           # страницы блоков/заданий
│   ├── profile.html
│   ├── notifications.html
│   └── 404.html
│
├── static/                    # CSS, картинки
│   └── uploads/               # аватарки и загружаемые файлы
│
├── files/                     # прикреплённые файлы к урокам
│   └── 1/
│
├── db/
│   └── lms.db                 # SQLite база (создаётся при первом запуске)
│
└── requirements.txt
```
 
