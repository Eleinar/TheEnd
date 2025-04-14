import sys
import bcrypt
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from ui import LoginWindow, MainWindow
from models import Session, User

app = QApplication()
login = LoginWindow()
if login.exec() == QDialog.Accepted:
    session = Session()
    user = session.query(User).filter_by(login=login.login_input.text().strip()).first()
    if user and bcrypt.checkpw(login.password_input.text().strip().encode('utf-8'), user.password.encode('utf-8')):
        window = MainWindow(role=user.role, user_id=user.user_id)
        window.show()
    else:
        QMessageBox.critical(None, "Ошибка входа", "Неверный логин или пароль")
    session.close()
app.exec()