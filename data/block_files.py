import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class BlockFile(SqlAlchemyBase):
    __tablename__ = 'block_files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    block_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("lesson_blocks.id"), nullable=False)
    filename = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)
    original_name = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)
    file_type = sqlalchemy.Column(sqlalchemy.String(50), nullable=False)

    block = orm.relationship("LessonBlock", back_populates="files")