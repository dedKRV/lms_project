import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class LessonFile(SqlAlchemyBase):
    __tablename__ = 'lesson_files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    filename = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)
    lesson_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lessons.id"), nullable=False)

    lesson = orm.relationship("Lesson", back_populates="files")