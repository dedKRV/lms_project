import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import orm


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(100))
    email = sqlalchemy.Column(sqlalchemy.String(120), index=True, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String(200))
    role = sqlalchemy.Column(sqlalchemy.String(20))
    birth_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    courses = orm.relationship("Course", back_populates="teacher")
    enrollments = orm.relationship("Enrollment", back_populates="student")
    submissions = orm.relationship("Submission", back_populates="student")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_age(self):
        if self.birth_date:
            today = datetime.date.today()
            age = today.year - self.birth_date.year
            if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
                age -= 1
            return age
        return None