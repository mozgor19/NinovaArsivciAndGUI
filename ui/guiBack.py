from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5 import QtGui, QtWidgets

from src.login import Login
from src.logger import Logger
from src.downloader import Downloader
from src.course_selector import CourseManager
from src.database import Database

from ui.guiFront import Ui_Arsivci


class GuiBackend:
    def __init__(self, ui):
        self.ui = Ui_Arsivci()
        self.ui.setupUi(self)

        self.session = None
        self.logger_instance = Logger(debug=True, verbose=True)
        self.download_folder = None
        self.db_instance = None

        # Connect button signals
        self.ui.pushButton_login.clicked.connect(self.login)
        self.ui.pushButton_selectFolder.clicked.connect(self.select_folder)
        self.ui.pushButton_download.clicked.connect(self.download_selected_courses)

    def login(self):
        username = self.ui.lineEdit_username.text()
        password = self.ui.lineEdit_password.text()

        if not username or not password:
            self.show_message("Kullanıcı adı ve şifre gerekli.", "Hata")
            return

        login_instance = Login(username, password)

        try:
            self.session = login_instance.login()
            self.logger_instance.info("Giriş başarılı!")
            self.ui.label_status.setText("Giriş başarılı!")
            self.load_courses()
        except PermissionError:
            self.ui.label_status.setText(
                "Kullanıcı adı veya şifre hatalı. Tekrar deneyin."
            )
            self.logger_instance.warning(
                "Kullanıcı adı veya şifre hatalı. Tekrar deneyin."
            )

    def select_folder(self):
        self.download_folder = QFileDialog.getExistingDirectory(
            None, "İndirme klasörü seç", ""
        )
        if self.download_folder:
            self.ui.label_selectionInfo.setText(
                f"Seçilen dizin: {self.download_folder}"
            )
            self.logger_instance.info(
                f"İndirme klasörü seçildi: {self.download_folder}"
            )
        else:
            self.logger_instance.warning("İndirme klasörü seçilmedi.")

    def load_courses(self):
        course_manager = CourseManager(self.session)
        courses = course_manager.get_course_list()
        # ListView'e dersleri eklemek
        model = QtGui.QStandardItemModel()
        for course in courses:
            item = QtGui.QStandardItem(course)
            item.setCheckable(True)
            model.appendRow(item)
        self.ui.listView_courses.setModel(model)

    def download_selected_courses(self):
        if not self.download_folder:
            self.show_message("Lütfen indirme klasörü seçin.", "Hata")
            return

        # ListView'den seçilen dersleri al
        selected_courses = []
        model = self.ui.listView_courses.model()
        for index in range(model.rowCount()):
            item = model.item(index)
            if item.checkState() == Qt.Checked:
                selected_courses.append(item.text())

        if not selected_courses:
            self.show_message("Lütfen en az bir ders seçin.", "Hata")
            return

        # Downloader başlat
        downloader = Downloader(self.session)
        self.db_instance = Database(self.download_folder)
        self.db_instance.start_db()

        for course in selected_courses:
            downloader.download_all_in_course(
                course, self.db_instance, self.db_instance.first_run
            )

        self.db_instance.write_records()
        self.show_message("Seçilen dersler indirildi.", "Başarılı")

    def show_message(self, message, title):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec_()
