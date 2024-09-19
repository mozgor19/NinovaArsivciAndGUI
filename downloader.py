from os import mkdir
from os.path import join, exists
from threading import Thread
from zlib import crc32
from bs4 import BeautifulSoup, element
from __future__ import annotations
from typing import TYPE_CHECKING
from collections import namedtuple

from logger import Logger
from manager import Manager
from login import Login

class DownloadCourses:
    
    MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD = 5  # in MB
    COURSE_TITLE_OFFSET = 8

    Course = namedtuple("Course", "code name link")


    def __init__(self, session, base_path):
        self.session = session
        self.base_path = base_path
        self.thread_list = []

    def get_course_list(): # returns the tuple of courses list
        course_list = []
        session = Login.login()
        page = BeautifulSoup(session.get(Manager.URL.value + "/Kampus1").content.decode("utf-8"), "lxml")

        erisim_agaci = page.select(".menuErisimAgaci>ul>li")
        for element in erisim_agaci:
            link = element.find("a")["href"]
            ders_info = BeautifulSoup(
                session.get(Manager.URL.value + link + "/SinifBilgileri").content.decode("utf-8"), "lxml"
            )
            ders_info = ders_info.find(class_="formAbetGoster")
            ders_info = ders_info.select("tr")
            code = ders_info[0].select("td")[1].text.strip()
            name = ders_info[1].select("td")[2].text.strip()

            course_list.append(Course(code, name, link))

        return tuple(course_list)


    def filter_courses(courses: tuple[Course]) -> tuple[Course]:
        for i, course in enumerate(courses):
            print(f"{i} - {course.code} | {course.name}")
        user_response = input(
            """İndirmek istediğiniz derslerin numarlarını, aralarında boşluk bırkarak girin
    Tüm dersleri indirmek için boş bırakın ve enter'a basın
        > """
        )
        user_response = user_response.strip()
        if user_response:
            courses_filtered = list()
            selected_indexes_raw = user_response.split(" ")
            for selected_index in selected_indexes_raw:
                try:
                    courses_filtered.append(courses[int(selected_index)])
                except ValueError:
                    logger.warning(
                        f"Girilen '{selected_index}' bir sayı değil. Yok sayılacak."
                    )
                except IndexError:
                    logger.warning(
                        f"Girilen '{selected_index}' herhangi bir kursun numarası değil. Yok sayılacak."
                    )
            courses_filtered = tuple(courses_filtered)

            indirilecek_dersler = ""
            for course in courses_filtered:
                indirilecek_dersler += course.name + ", "
            print(f"{indirilecek_dersler} dersleri indirilecek.")
            return courses_filtered
        else:
            print("Tüm dersler indirilecek.")
            return courses


    def download_all_in_course(self, course: Course) -> None:
        subdir_name = join(self.base_path, course.code)

        try:
            mkdir(subdir_name)
        except FileExistsError:
            pass

        raw_html = self.session.get(
            Manager.URL + course.link + self.SINIF_DOSYALARI_URL_EXTENSION
        ).content.decode("utf-8")

        try:
            klasor = join(subdir_name, "Sınıf Dosyaları")
            mkdir(klasor)
        except FileExistsError:
            pass

        self._download_or_traverse(raw_html, klasor)

        raw_html = self.session.get(
            Manager.URL + course.link + self.DERS_DOSYALARI_URL_EXTENSION
        ).content.decode("utf-8")

        try:
            klasor = join(subdir_name, "Ders Dosyaları")
            mkdir(klasor)
        except FileExistsError:
            pass

        self._download_or_traverse(raw_html, klasor)

        for thread in self.thread_list:
            thread.join()

    def _download_or_traverse(self, raw_html: str, destination_folder: str) -> None:
        try:
            rows = BeautifulSoup(raw_html, "lxml")
            rows = rows.select_one(".dosyaSistemi table.data").find_all("tr")
        except:
            return  # if the 'file' is a link to another page
        rows.pop(0)  # first row is the header of the table

        for row in rows:
            info = self._parse_file_info(row)
            if info:
                file_link, file_size, isFolder, file_name = info
                if isFolder:
                    self._traverse_folder(
                        Manager.URL + file_link, destination_folder, file_name
                    )
                elif file_size > self.MIN_FILE_SIZE_TO_LAUNCH_NEW_THREAD:  # MB
                    large_file_thread = Thread(
                        target=self._download_file,
                        args=(
                            Manager.URL + file_link,
                            destination_folder,
                            DB.get_new_cursor(),
                        ),
                    )
                    large_file_thread.start()
                    self.thread_list.append(large_file_thread)
                else:
                    self._download_file(
                        Manager.URL + file_link, destination_folder, DB.get_new_cursor()
                    )

    def _parse_file_info(self, row: element.Tag):
        try:
            file_info = row.find_all("td")
            file_a_tag = file_info[0].find("a")
            file_name = file_a_tag.text
            file_size = self._get_mb_file_size_from_string(file_info[1].text)
            isFolder = file_info[0].find("img")["src"].endswith("/folder.png")
            file_link = file_a_tag["href"]
        except:
            return None

        return file_link, file_size, isFolder, file_name

    def _traverse_folder(self, folder_url, current_folder, new_folder_name):
        resp = self.session.get(folder_url)
        subdir_name = join(current_folder, new_folder_name)
        try:
            mkdir(subdir_name)
        except FileExistsError:
            pass

        folder_thread = Thread(
            target=self._download_or_traverse,
            args=(resp.content.decode("utf-8"), subdir_name),
        )
        folder_thread.start()
        self.thread_list.append(folder_thread)

    def _download_file(self, file_url: str, destination_folder: str, cursor):
        file_status = DB.check_file_status(int(file_url[file_url.find("?g") + 2:]), cursor)
        match file_status:
            case FILE_STATUS.NEW:
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
                        if not globals.FIRST_RUN:
                            logger.warning(
                                "Veri tabanına manuel müdahele tespit edildi. Eğer müdahele edilmediyse geliştiriciye bildirin!"
                            )
                        break

                with open(file_full_name, "wb") as bin:
                    bin.write(file_binary)

                DB.add_file(int(file_url[file_url.find("?g") + 2:]), file_full_name)

    @logger.speed_measure("indirme işlemi", False, True)
    def _download_from_server(self, file_url: str):
        resp = self.session.get(file_url)
        file_name_offset = resp.headers["content-disposition"].index("filename=") + 9
        file_name = resp.headers["content-disposition"][file_name_offset:]
        return file_name, resp.content

    def _get_mb_file_size_from_string(self, raw_file_size: str) -> float:
        size_info = raw_file_size.strip().split(" ")
        size_as_float = float(size_info[0])
        if size_info[1] == "KB":
            size_as_float /= 1024
        return size_as_float
