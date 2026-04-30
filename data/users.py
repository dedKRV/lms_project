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
            if today.month < self.birth_date.month or (
                    today.month == self.birth_date.month and today.day < self.birth_date.day):
                age -= 1
            return age
        return None

    def get_display_score(self):
        total = self.get_total_score()
        return f"{total // 1000}.{total % 1000:03d}"

    def get_total_score(self):
        from data import db_session
        db_sess = db_session.create_session()

        total = 0
        for submission in self.submissions:
            if submission.score:
                block = submission.block
                if block and block.lesson:
                    course = block.lesson.course
                    if course:
                        total += submission.score

        db_sess.close()
        return total

    def get_course_scores(self):
        from data import db_session
        from data.enrollments import Enrollment

        db_sess = db_session.create_session()

        enrollments = db_sess.query(Enrollment).filter_by(student_id=self.id).all()

        course_scores = []
        for enrollment in enrollments:
            course = enrollment.course
            total_score = 0
            for lesson in course.lessons:
                for block in lesson.blocks:
                    for submission in block.submissions:
                        if submission.student_id == self.id and submission.score:
                            total_score += submission.score

            if total_score > 0:
                course_scores.append({
                    'title': course.title,
                    'score': total_score,
                    'display_score': f"{total_score // 1000}.{total_score % 1000:03d}"
                })

        db_sess.close()
        return course_scores