import os
from data import db_session
from data.users import User

os.makedirs("db", exist_ok=True)

db_session.global_init("db/lms.db")
session = db_session.create_session()

print("Создаем тестового пользователя...")

existing = session.query(User).filter(User.email == "teacher@test.com").first()
if existing:
    print("Пользователь с таким email уже существует!")
    print(f"ID: {existing.id}")
    print(f"Name: {existing.name}")
    print(f"Email: {existing.email}")
    print(f"Role: {existing.role}")
else:
    user = User()
    user.name = "Тестовый Учитель"
    user.email = "teacher@test.com"
    user.role = "teacher"
    user.set_password("123456")

    try:
        session.add(user)
        session.commit()
        print("Пользователь создан успешно!")
        print(f"ID: {user.id}")
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()

session.close()