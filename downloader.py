#Bismillahirrahmanirrahim

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from course_selector import Course

from os import mkdir,getcwd
from os.path import join, exists
from tkinter.filedialog import askdirectory

from bs4 import BeautifulSoup, element
from threading import Thread
from zlib import crc32
import copy

from manager import Manager
from database import FILE_STATUS

from logger import Logger

MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD = 5  # in mb
SINIF_DOSYALARI_URL_EXTENSION = "/SinifDosyalari"
DERS_DOSYALARI_URL_EXTENSION = "/DersDosyalari"


class Downloader:

    def __init__(self, session):
        self.thread_list: list[Thread] = []
        self.session = session
        self.logger = Logger()
        self.base_path = None
        self.copy_session = None     

        self.get_directory()
        self.session_copy()

    def get_directory(self):
        """
        Gets the directory from command line if exists, else shows a folder dialog\n
        Guarantees that the returned path exists, if the path does not exists than exits with error\n
        Accesses to '.last_dir' file to get last used directory
        """

        # Get last selected directory from file
        try:
            default_dir_file = open(join(getcwd(), ".last_dir"), "r")
            default_dir = default_dir_file.read().strip()
        except:
            default_dir = getcwd()

        download_directory = askdirectory(initialdir=default_dir, title="Ninova Arşivci - İndirme klasörü seçin")

        if not exists(download_directory):
            self.logger.fail(f"Verilen '{download_directory}' geçerli bir klasör değil!")

        try:
            default_dir_file = open(join(getcwd(), ".last_dir"), "w")
            default_dir_file.write(download_directory)
        finally:
            default_dir_file.close()

        self.base_path = download_directory
    
    def session_copy(self):
        
        self.copy_session = copy.copy(self.session)
        

    def download_all_in_course(self, course: Course, db_instance,first_run):
        subdir_name = join(self.base_path, course.code)
        session = self.copy_session

        try:
            mkdir(subdir_name)
        except FileExistsError:
            pass

        raw_html = session.get(
            Manager.URL.value + course.link + SINIF_DOSYALARI_URL_EXTENSION
        ).content.decode("utf-8")

        try:
            klasor = join(subdir_name, "Sınıf Dosyaları")
            mkdir(klasor)
        except FileExistsError:
            pass

        self.download_or_traverse(raw_html, klasor,db_instance,first_run)

        raw_html = session.get(
            Manager.URL.value + course.link + DERS_DOSYALARI_URL_EXTENSION
        ).content.decode("utf-8")

        try:
            klasor = join(subdir_name, "Ders Dosyaları")
            mkdir(klasor)
        except FileExistsError:
            pass

        self.download_or_traverse(raw_html, klasor,db_instance,first_run)

        for thread in self.thread_list:
            thread.join()

    def get_mb_file_size_from_string(self, raw_file_size: str) -> float:
        size_info = raw_file_size.strip().split(" ")
        size_as_float = float(size_info[0])
        if size_info[1] == "KB":
            size_as_float /= 1024
        return size_as_float

    def download_or_traverse(self, raw_html: str, destination_folder: str, db_instance,first_run):
        try:
            rows = BeautifulSoup(raw_html, "lxml")
            rows = rows.select_one(".dosyaSistemi table.data").find_all("tr")
        except:
            return  # if the 'file' is a link to another page
        rows.pop(0)  # first row is the header of the table

        row: element.Tag
        for row in rows:
            info = self.parse_file_info(row)
            if info:
                file_link, file_size, isFolder, file_name = info
                if isFolder:
                    self.traverse_folder(Manager.URL.value + file_link, destination_folder, file_name,db_instance,first_run)
                elif file_size > MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD:  # mb
                    large_file_thread = Thread(
                        target=self.download_file,
                        args=(
                            Manager.URL.value + file_link, destination_folder, db_instance.get_new_cursor(), db_instance,first_run
                            ),
                    )
                    large_file_thread.start()
                    self.thread_list.append(large_file_thread)
                else:
                    self.download_file(
                        Manager.URL.value + file_link, destination_folder, db_instance.get_new_cursor(),db_instance,first_run
                    )

    def parse_file_info(self, row: element.Tag):
        try:
            file_info = row.find_all("td")
            file_a_tag = file_info[0].find("a")
            file_name = file_a_tag.text
            file_size = self.get_mb_file_size_from_string(file_info[1].text)
            isFolder = file_info[0].find("img")["src"].endswith("/folder.png")
            file_link = file_a_tag["href"]
        except:
            return None

        return file_link, file_size, isFolder, file_name

    def traverse_folder(self, folder_url, current_folder, new_folder_name,db_instance,first_run):
        session = self.copy_session
        resp = session.get(folder_url)
        subdir_name = join(current_folder, new_folder_name)
        try:
            mkdir(subdir_name)
        except FileExistsError:
            pass

        folder_thread = Thread(
            target=self.download_or_traverse,
            args=(resp.content.decode("utf-8"), subdir_name,db_instance,first_run),
        )
        folder_thread.start()
        self.thread_list.append(folder_thread)

    def download_file(self, file_url: str, destination_folder: str, cursor, db_instance, first_run):
        session = self.copy_session
        file_status = db_instance.check_file_status(
            int(file_url[file_url.find("?g") + 2 :]), cursor
        )
        match file_status:
            case FILE_STATUS.NEW:
                file_name, file_binary = self.download_from_server(session,file_url)
                file_full_name = join(destination_folder, file_name)
                while exists(file_full_name):
                    ex_file = open(file_full_name, "rb")
                    if crc32(file_binary) != crc32(ex_file.read()):
                        extension_dot_index = file_full_name.find(".")
                        file_full_name = (
                            file_full_name[:extension_dot_index]
                            + "_new"
                            + file_full_name[extension_dot_index:]
                        )
                    else:
                        if not first_run:
                            self.logger.warning(
                                "Veri tabanına manuel müdahele tespit edildi. Eğer müdahele edilmediyse geliştiriciye bildirin!"
                            )
                        break

                with open(file_full_name, "wb") as bin:
                    bin.write(file_binary)

                db_instance.add_file(int(file_url[file_url.find("?g") + 2 :]), file_full_name)

    def download_from_server(self, session,file_url: str):
        resp = session.get(file_url)
        file_name_offset = resp.headers["content-disposition"].index("filename=") + 9
        file_name = resp.headers["content-disposition"][file_name_offset:]
        return file_name, resp.content
