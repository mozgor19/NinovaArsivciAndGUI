# Bismillahirrahmanirrahim

try:
    from pwinput import pwinput as getpass #pwinput shows *** types
except:
    from getpass import getpass

from login import Login
from logger import Logger
from downloader import Downloader
from course_selector import CourseManager
from database import Database

def main():
    logger_instance = Logger(debug=True, verbose=True)  # Create an instance of Logger

    while True:
        username = input("Kullanıcı adı (@itu.edu.tr olmadan): ")
        password = getpass("Şifre: ")
        login_instance = Login(username, password)
        
        try:
            session = login_instance.login()
            print("Giriş başarılı!")
            break  # Exit loop if login is successful
        except PermissionError:
            logger_instance.warning("Kullanıcı adı veya şifre hatalı. Tekrar deneyin.")
    
    course_manager = CourseManager(session)
    course_manager.get_course_list()
    selected_courses = course_manager.filter_courses()

    downloader = Downloader(session)
    db_instance = Database(downloader.base_path)

    db_instance.start_db()

    for course in selected_courses:
        downloader.download_all_in_course(course,db_instance,db_instance.first_run)

if __name__ == "__main__":
    main()
