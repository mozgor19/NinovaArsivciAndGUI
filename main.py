# Bismillahirrahmanirrahim

import getpass
from login import Login
from logger import Logger

def main():
    logger = Logger(debug=True, verbose=True)  # Create an instance of Logger

    while True:
        username = input("Kullanıcı adı (@itu.edu.tr olmadan): ")
        password = getpass.getpass("Şifre: ")
        login_instance = Login(username, password)
        
        try:
            session = login_instance.login()
            print("Giriş başarılı!")
            break  # Exit loop if login is successful
        except PermissionError as e:
            logger.warning("Kullanıcı adı veya şifre hatalı. Tekrar deneyin.")

if __name__ == "__main__":
    main()
