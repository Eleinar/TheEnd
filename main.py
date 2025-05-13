import sys
import bcrypt
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from ui import LoginWindow, MainWindow
from models import Session, User

app = QApplication(sys.argv)

# Инициализация сессии
session = None
try:
    session = Session()


    # Окно логина
    login = LoginWindow()
    if login.exec() == QDialog.Accepted:
        # Поиск пользователя
        user = session.query(User).filter_by(login=login.login_input.text().strip()).first()
        
        # Проверка логина и пароля
        if user and bcrypt.checkpw(
            login.password_input.text().strip().encode('utf-8'),
            user.password.encode('utf-8')
        ):
            # Открываем главное окно
            window = MainWindow(role=user.role, user_id=user.user_id)
            window.show()
            
            # Запускаем приложение
            exit_code = app.exec()
            
            # Закрываем сессию перед выходом
            session.close()
            sys.exit(exit_code)
        else:
            QMessageBox.critical(None, "Ошибка входа", "Неверный логин или пароль")
            session.close()
            sys.exit(1)
            
except Exception as e:
    # Обработка ошибок подключения или других исключений
    QMessageBox.critical(None, "Критическая ошибка", f"Произошла ошибка: {str(e)}")
    if session:
        session.close()
    sys.exit(1)

finally:
    # Гарантируем закрытие сессии
    if session:
        session.close()