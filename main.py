# Bismillahirrahmanirrahim

import getpass
from tkinter import Tk
from tkinter import filedialog

from login import Login
from logger import Logger
from downloader import Downloader
from course_selector import CourseManager
from database import DB

def main():
    logger_instance = Logger(debug=True, verbose=True)  # Create an instance of Logger

    while True:
        username = input("Kullanıcı adı (@itu.edu.tr olmadan): ")
        password = getpass.getpass("Şifre: ")
        login_instance = Login(username, password)
        
        try:
            session = login_instance.login()
            print("Giriş başarılı!")
            break  # Exit loop if login is successful
        except PermissionError:
            logger_instance.warning("Kullanıcı adı veya şifre hatalı. Tekrar deneyin.")

    # Kurs listesini alma
    course_manager = CourseManager(session)
    courses = course_manager.get_course_list()
    
    # Kullanıcıdan hangi kursu seçeceğini alma
    selected_courses = course_manager.filter_courses(courses)

    # Tkinter penceresini başlatma
    Tk().withdraw()  # Tkinter penceresini gizle

    # Kullanıcıdan indirme yolu seçmesini isteme
    base_path = filedialog.askdirectory(title="Dosyaları nereye indirmek istersiniz?")

    if not base_path:  # Eğer kullanıcı bir dizin seçmezse
        logger_instance.warning("İndirme yolu seçilmedi. Program sonlandırılıyor.")
        return
    
    db_instance = DB()  # Sınıf örneğini oluştur
    db_instance.init(base_path)  # base_path'i geçin

    downloader = Downloader(base_path=base_path, session=session)
    
    for course in selected_courses:
        downloader.download_all_in_course(course)

if __name__ == "__main__":
    main()
