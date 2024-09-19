from os import mkdir
from os.path import join, exists
from threading import Thread
from zlib import crc32
from bs4 import BeautifulSoup, element
from database import DB, FILE_STATUS
from course_selector import Course
import logger  # Logger sınıfını import et

MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD = 5  # in MB
SINIF_DOSYALARI_URL_EXTENSION = "/SinifDosyalari"
DERS_DOSYALARI_URL_EXTENSION = "/DersDosyalari"

thread_list: list[Thread] = []

class Downloader:

    def __init__(self, base_path: str, session):
        self.BASE_PATH = base_path
        self.session = session
        self.thread_list: list[Thread] = []
        self.logger = logger.Logger()  # Logger nesnesi oluştur

    def download_all_in_course(self, course: Course) -> None:
        subdir_name = join(self.BASE_PATH, course.code)

        try:
            mkdir(subdir_name)
        except FileExistsError:
            self.logger.verbose(f"{subdir_name} dizini zaten mevcut.")
        
        self._download_or_traverse(course.link + SINIF_DOSYALARI_URL_EXTENSION, subdir_name, "Sınıf Dosyaları")
        self._download_or_traverse(course.link + DERS_DOSYALARI_URL_EXTENSION, subdir_name, "Ders Dosyaları")

        for thread in self.thread_list:
            thread.join()

    def _download_or_traverse(self, url: str, destination_folder: str, folder_name: str) -> None:
        try:
            raw_html = self.session.get(url).content.decode("utf-8")
            rows = BeautifulSoup(raw_html, "lxml")
            rows = rows.select_one(".dosyaSistemi table.data").find_all("tr")
        except Exception as e:
            self.logger.warning(f"Sayfa yüklenirken hata oluştu: {e}")
            return  # Eğer dosya başka bir sayfaya yönlendirilirse

        rows.pop(0)  # Başlık satırını çıkar

        for row in rows:
            info = self._parse_file_info(row)
            if info:
                file_link, file_size, is_folder, file_name = info
                if is_folder:
                    self._traverse_folder(file_link, destination_folder, file_name)
                elif file_size > MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD:  # MB cinsinden
                    large_file_thread = Thread(
                        target=self._download_file,
                        args=(file_link, destination_folder, DB.get_new_cursor()),
                    )
                    large_file_thread.start()
                    self.thread_list.append(large_file_thread)
                else:
                    self._download_file(file_link, destination_folder, DB.get_new_cursor())

    def _parse_file_info(self, row: element.Tag):
        try:
            file_info = row.find_all("td")
            file_a_tag = file_info[0].find("a")
            file_name = file_a_tag.text
            file_size = self._get_mb_file_size_from_string(file_info[1].text)
            is_folder = file_info[0].find("img")["src"].endswith("/folder.png")
            file_link = file_a_tag["href"]
        except Exception as e:
            self.logger.warning(f"Dosya bilgileri ayrıştırılırken hata oluştu: {e}")
            return None

        return file_link, file_size, is_folder, file_name

    def _traverse_folder(self, folder_url: str, current_folder: str, new_folder_name: str):
        resp = self.session.get(folder_url)
        subdir_name = join(current_folder, new_folder_name)
        try:
            mkdir(subdir_name)
        except FileExistsError:
            self.logger.verbose(f"{subdir_name} dizini zaten mevcut.")

        folder_thread = Thread(
            target=self._download_or_traverse,
            args=(folder_url, subdir_name),
        )
        folder_thread.start()
        self.thread_list.append(folder_thread)

    def _download_file(self, file_url: str, destination_folder: str, cursor):
        file_status = DB.check_file_status(int(file_url[file_url.find("?g") + 2:]), cursor)
        if file_status == FILE_STATUS.NEW:
            file_name, file_binary = self._download_from_server(file_url)
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
                    break

            with open(file_full_name, "wb") as bin_file:
                bin_file.write(file_binary)

            DB.add_file(int(file_url[file_url.find("?g") + 2:]), file_full_name)

    def _download_from_server(self, file_url: str):
        resp = self.session.get(file_url)
        file_name_offset = resp.headers["content-disposition"].index("filename=") + 9
        file_name = resp.headers["content-disposition"][file_name_offset:]
        return file_name, resp.content

    def _get_mb_file_size_from_string(self, raw_file_size: str) -> float:
        size_info = raw_file_size.strip().split(" ")
        size_as_float = float(size_info[0])
        if size_info[1] == "KB":
            size_as_float /= 1024  # KB'yi MB'ye dönüştür
        return size_as_float

# Kullanım
# downloader = Downloader(base_path="path/to/base", session=session)
# downloader.download_all_in_course(course)
