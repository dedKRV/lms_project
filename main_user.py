from data import db_session
from data.users import User

db_session.global_init("db/lms.db")
session = db_session.create_session()

print("Создаем тестового пользователя...")

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