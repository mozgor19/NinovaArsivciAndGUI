from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5 import QtGui, QtWidgets

import sys

from src.login import Login
from src.downloader import Downloader
from src.course_selector import CourseManager
from src.database import Database

from guiFront import Ui_Arsivci


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainApp, self).__init__()
        self.ui = Ui_Arsivci()
        self.ui.setupUi(self)

        self.session = None
        self.download_folder = None
        self.db_instance = None

        self.download_folder = QStandardPaths.writableLocation(
            QStandardPaths.DesktopLocation
        )
        self.ui.label_selectionInfo.setText(f"İndirme Dizini: {self.download_folder}")

        # Connect button signals
        self.ui.pushButton_login.clicked.connect(self.login)
        self.ui.pushButton_selectFolder.clicked.connect(self.select_folder)
        self.ui.pushButton_download.clicked.connect(self.download)

    def login(self):
        username = self.ui.lineEdit_username.text()
        password = self.ui.lineEdit_password.text()

        if not username or not password:
            self.show_message("Kullanıcı adı ve şifre gerekli.", "Hata")
            return

        login_instance = Login(username, password)

        try:
            self.session = login_instance.login()
            self.ui.label_status.setText("Giriş başarılı!")
            self.load_courses()
        except PermissionError:
            self.ui.label_status.setText(
                "Kullanıcı adı veya şifre hatalı. Tekrar deneyin."
            )

    def load_courses(self):

        course_manager = CourseManager(self.session)
        course_manager.get_course_list()

        # ListView'e dersleri ekle
        model = QtGui.QStandardItemModel()

        for course in course_manager.courses:
            item = QtGui.QStandardItem((course.code + " | " + course.name))
            item.setCheckable(True)
            model.appendRow(item)
        self.ui.listView_courses.setModel(model)

        self.ui.label_downloadInfo.setText(
            "Lütfen indirmek istediğiniz dersleri ve indirme yerini seçin."
        )

    def select_courses(self):

        selected_courses = []
        model = self.ui.listView_courses.model()
        for index in range(model.rowCount()):
            item = model.item(index)
            if item.checkState() == Qt.Checked:
                selected_courses.append(item.text())

        if not selected_courses:
            self.show_message("Lütfen en az bir ders seçin.", "Hata")
            return

        return selected_courses

    def select_folder(self):
        self.download_folder = QFileDialog.getExistingDirectory(
            None, "İndirme klasörü seç", ""
        )
        self.ui.label_selectionInfo.setText(f"Seçilen dizin: {self.download_folder}")

    def download(self):

        courses = self.select_courses()
        downloader = Downloader(self.session)
        downloader.set_directory(self.download_folder)
        self.db_instance = Database(self.download_folder)
        self.db_instance.start_db()

        for course in courses:
            print(course)
            downloader.download_all_in_course(
                course, self.db_instance, self.db_instance.first_run
            )

        self.db_instance.write_records()
        self.show_message("Seçilen dersler indirildi.", "Başarılı")
        self.ui.label_status.setText("Seçilen dersler indirildi.")

    def show_message(self, message, title):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
