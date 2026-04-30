import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Course(SqlAlchemyBase):
    __tablename__ = 'courses'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(150), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    teacher_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)

    teacher = orm.relationship("User", back_populates="courses")
    lessons = orm.relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = orm.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")