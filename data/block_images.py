import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class BlockImage(SqlAlchemyBase):
    __tablename__ = 'block_images'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    block_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lesson_blocks.id"), nullable=False)
    filename = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)

    block = orm.relationship("LessonBlock", backref="block_images_ref")