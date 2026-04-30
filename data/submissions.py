import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Submission(SqlAlchemyBase):
    __tablename__ = 'submissions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    block_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lesson_blocks.id"), nullable=False)
    student_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    code = sqlalchemy.Column(sqlalchemy.Text)
    score = sqlalchemy.Column(sqlalchemy.Integer)
    feedback = sqlalchemy.Column(sqlalchemy.Text)
    status = sqlalchemy.Column(sqlalchemy.String(20), default="draft")
    submitted_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    graded_at = sqlalchemy.Column(sqlalchemy.DateTime)

    block = orm.relationship("LessonBlock", back_populates="submissions")
    student = orm.relationship("User", back_populates="submissions")