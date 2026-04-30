from flask import current_app
from data import db_session
from data.users import User
import os


def get_user_by_id(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    db_sess.close()
    return user


def get_user_by_email(email):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()
    db_sess.close()
    return user


def init_context_processors(app):
    @app.context_processor
    def utility_processor():
        return {
            'get_user_by_id': get_user_by_id,
            'get_user_by_email': get_user_by_email
        }