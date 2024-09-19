from collections import namedtuple
import sqlite3
from os.path import join, exists
from os import remove as delete_file
from enum import Enum
from zlib import crc32
from queue import Queue
from logger import Logger  # Logger'ı import ettik

DATABASE_FILE_NAME = "ninova_arsivci.db"
TABLE_CREATION_QUERY = "CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT UNIQUE, hash INT, isDeleted INT DEFAULT 0);"
TABLE_CHECK_QUERY = "SELECT name FROM sqlite_master WHERE type='table' AND name='files';"
SELECT_FILE_BY_ID_QUERY = "SELECT isDeleted, id FROM files WHERE id = ?"
FILE_INSERTION_QUERY = "INSERT INTO files (id, path, hash) VALUES (?, ?, ?)"

class FILE_STATUS(Enum):
    NEW = 0
    DELETED = 1
    EXISTS = 2

FileRecord = namedtuple("FileRecord", "id, path")

class DB:
    connection: sqlite3.Connection
    to_add = Queue()
    db_path: str
    logger = Logger()

    def init(self, base_path: str):
        """ Connects to DB and checks and creates the table structure """
        self.db_path = join(base_path, DATABASE_FILE_NAME)
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(TABLE_CHECK_QUERY)
        if cursor.fetchone() is None:
            cursor.execute(TABLE_CREATION_QUERY)
            self.logger.verbose("Veri tabanı ilk çalıştırma için hazırlandı.")
        else:
            self.logger.verbose("Veri tabanı mevcut.")
        cursor.close()

    def connect(self):
        """ Connects to DB using db_path """
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

    def add_file(self, id: int, path: str):
        self.to_add.put(FileRecord(id, path))

    def apply_changes_and_close(self):
        self.connection.commit()
        self.connection.close()

    def get_new_cursor(self):
        return self.connection.cursor()

    @logger.speed_measure("Veri tabanına yazma", False, False)
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
