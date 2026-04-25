from flask_wtf import FlaskForm
from wtforms import PasswordField, EmailField, BooleanField, SubmitField


class LoginForm(FlaskForm):
    email = EmailField('Email')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')