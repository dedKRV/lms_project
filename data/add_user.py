from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField


class AddUserForm(FlaskForm):
    name = StringField('Полное имя')
    email = StringField('Email')
    password = PasswordField('Пароль')
    role = SelectField('Роль', choices=[('student', 'Студент'), ('teacher', 'Преподаватель')])
    submit = SubmitField('Зарегистрироваться')