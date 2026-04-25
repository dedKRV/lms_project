import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Enrollment(SqlAlchemyBase):
    __tablename__ = 'enrollments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    student_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    course_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("courses.id"), nullable=False)

    student = orm.relationship("User", backref="enrollments")
    course = orm.relationship("Course", backref="enrollments_ref")