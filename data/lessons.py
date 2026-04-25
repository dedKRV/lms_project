import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Lesson(SqlAlchemyBase):
    __tablename__ = 'lessons'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(150), nullable=False)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    course_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("courses.id"), nullable=False)

    course = orm.relationship("Course", backref="course_lessons")
    files = orm.relationship("LessonFile", cascade="all, delete-orphan")
    blocks = orm.relationship("LessonBlock", cascade="all, delete-orphan")