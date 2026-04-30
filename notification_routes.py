from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from data import db_session
from data.notifications import Notification


def init_notification_routes(app):
    @app.route("/notifications")
    @login_required
    def notifications():
        db_sess = db_session.create_session()
        notifs = db_sess.query(Notification).filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).all()

        notifications_data = []
        for n in notifs:
            notifications_data.append({
                'id': n.id,
                'text': n.text,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at
            })

        db_sess.close()
        return render_template("notifications.html", notifications=notifications_data)

    @app.route("/notifications/read/<int:notif_id>")
    @login_required
    def read_notification(notif_id):
        db_sess = db_session.create_session()
        notif = db_sess.get(Notification, notif_id)

        if not notif or notif.user_id != current_user.id:
            db_sess.close()
            abort(404)

        link = notif.link
        notif.is_read = True
        db_sess.commit()
        db_sess.close()

        if link:
            return redirect(link)
        return redirect(url_for("notifications"))

    @app.route("/notifications/delete-all")
    @login_required
    def delete_all_notifications():
        db_sess = db_session.create_session()
        db_sess.query(Notification).filter_by(user_id=current_user.id).delete()
        db_sess.commit()
        db_sess.close()
        flash("Все уведомления удалены")
        return redirect(url_for("notifications"))


def create_notification(user_id, text, link=None):
    db_sess = db_session.create_session()
    notif = Notification(
        user_id=user_id,
        text=text,
        link=link
    )
    db_sess.add(notif)
    db_sess.commit()
    db_sess.close()