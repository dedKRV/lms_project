import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Notification(SqlAlchemyBase):
    __tablename__ = 'notifications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    text = sqlalchemy.Column(sqlalchemy.String(500), nullable=False)
    link = sqlalchemy.Column(sqlalchemy.String(200))
    is_read = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)