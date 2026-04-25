from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Пожалуйста, войдите в систему")
            return redirect(url_for("login"))
        if current_user.role != "teacher":
            flash("Только для преподавателей")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated