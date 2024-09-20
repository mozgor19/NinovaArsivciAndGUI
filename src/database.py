#Bismillahirrahmanirrahim

from collections import namedtuple
import sqlite3
from os.path import join, exists
from os import remove as delete_file
from enum import Enum
from zlib import crc32
from queue import Queue

from src.logger import Logger

DATABASE_FILE_NAME = "ninova_arsivci.db"
TABLE_CREATION_QUERY = "CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT UNIQUE, hash INT, isDeleted INT DEFAULT 0);"
TABLE_CHECK_QUERY = (
    "SELECT name FROM sqlite_master WHERE type='table' AND name='files';"
)
SELECT_FILE_BY_ID_QUERY = "SELECT isDeleted, id FROM files WHERE id = ?"
FILE_INSERTION_QUERY = "INSERT INTO files (id, path, hash) VALUES (?, ?, ?)"


class FILE_STATUS(Enum):
    NEW = 0
    DELETED = 1
    EXISTS = 2

FileRecord = namedtuple("FileRecord", "id, path")


class Database:

    def __init__(self,base_path):
        self.base_path = base_path
        self.db_path = join(self.base_path, DATABASE_FILE_NAME)
        self.logger = Logger()
        self.first_run = None
        self.connection = None
        self.to_add = Queue()

        self.get_first_run()
    
    def start_db(self):

        if self.first_run:
            try:
                delete_file(self.db_path)
            except:
                pass

        self.connect()
        cursor = self.connection.cursor()
        if self.first_run:
            cursor.execute(TABLE_CREATION_QUERY)
            self.logger.verbose("Veri tabanı ilk çalıştırma için hazırlandı.")
        else:
            cursor.execute(TABLE_CHECK_QUERY)
            if cursor.fetchone()[0] != "files":
                self.logger.fail(
                    f"Veri tabanı bozuk. '{DATABASE_FILE_NAME}' dosyasını silip tekrar başlatın. Silme işlemi sonrasında tüm dosyalar yeniden indirilir."
                )

        cursor.close()
    
    def get_first_run(self):
        """
        Checks whether this is the first time that program ran on selected directory by checking database file
        """
        if self.base_path:
            first_run = (not exists(join(self.base_path, "ninova_arsivci.db")))
            self.first_run = first_run
        else:
            self.logger.fail("Klasör seçilmemiş. get_directory() fonksiyonu ile BASE_PATH değişkeni ayarlanmalı! Geliştiriciye bildirin!")
    
    def connect(self):
        """
        Connects to DB using db_path class attribute
        Sets connection object of the class, does not return anything
        """
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.logger.debug("Veri tabanına bağlandı.")
        except:
            self.logger.fail("Veri tabanına bağlanılamadı.")

    def check_file_status(self, file_id: int, cursor: sqlite3.Cursor):
        cursor.execute(SELECT_FILE_BY_ID_QUERY, (file_id,))
        file = cursor.fetchone()
        if file:
            deleted, id = file
            if file_id != id:
                self.logger.fail(
                    "Eş zamanlı erişimden dolayı, race condition oluşturdu. Veri tabanından gelen bilgi, bu dosyaya ait değil. Geliştiriciye bildirin."
                )

            if deleted:
                return FILE_STATUS.DELETED
            else:
                return FILE_STATUS.EXISTS
        else:
            return FILE_STATUS.NEW

    # Should be called after the download
    def add_file(self, id: int, path: str):
        self.to_add.put(FileRecord(id, path))

    def apply_changes_and_close(self):
        self.connection.commit()
        self.connection.close()

    def get_new_cursor(self):
        if self.connection:
            return self.connection.cursor()
        else:
            self.logger.fail("Veri tabanı bağlantısı yok. Cursor alınamıyor.")
            raise AttributeError("Veri tabanı bağlantısı yok.")


    def write_records(self):
        cursor = self.get_new_cursor()
        while not self.to_add.empty():
            record = self.to_add.get()
            if exists(record.path):
                with open(record.path, "rb") as file:
                    hash = crc32(file.read())
                    try:
                        cursor.execute(FILE_INSERTION_QUERY, (record.id, record.path, hash))
                    except Exception as e:
                        self.logger.fail(str(e) + "\n The file_path is " + record.path)
                self.logger.new_file(record.path)
            else:
                self.logger.warning(f"Veritabanına yazılacak {record.path} dosyası bulunamadı. Veri tabanına yazılmayacak")

        self.apply_changes_and_close()