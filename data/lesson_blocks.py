import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class LessonBlock(SqlAlchemyBase):
    __tablename__ = 'lesson_blocks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    lesson_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lessons.id"), nullable=False)
    block_type = sqlalchemy.Column(sqlalchemy.String(20), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String(200))
    content = sqlalchemy.Column(sqlalchemy.Text)
    order = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=0)

    lesson = orm.relationship("Lesson", back_populates="blocks")
    images = orm.relationship("BlockImage", back_populates="block", cascade="all, delete-orphan")
    files = orm.relationship("BlockFile", back_populates="block", cascade="all, delete-orphan")
    submissions = orm.relationship("Submission", back_populates="block", cascade="all, delete-orphan")