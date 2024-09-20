#Bismillahirrahmanirrahim

from __future__ import annotations
from typing import List, Tuple
from collections import namedtuple
from bs4 import BeautifulSoup
import requests  # HTTP istekleri için kullanılacak

from logger import Logger
from manager import Manager

Course = namedtuple("Course", "code name link")
COURSE_TITLE_OFFSET = 8

class CourseManager:

    def __init__(self, session: requests.Session):
        self.session = session
        self.courses: tuple[Course] = []
        self.logger = Logger()

    def get_course_list(self) -> Tuple[Course]:

        page = BeautifulSoup(self.session.get(Manager.URL.value + "/Kampus1").content.decode("utf-8"), "lxml")
        erisim_agaci = page.select(".menuErisimAgaci>ul>li")
        
        for element in erisim_agaci:
            link = element.find("a")["href"]
            ders_info = BeautifulSoup(
                self.session.get(Manager.URL.value + link + "/SinifBilgileri").content.decode("utf-8"), "lxml"
            )
            ders_info = ders_info.find(class_="formAbetGoster")
            ders_info = ders_info.select("tr")
            code = ders_info[0].select("td")[1].text.strip()
            name = ders_info[1].select("td")[2].text.strip()

            self.courses.append(Course(code, name, link))

        #print(self.courses)
        #return tuple(self.courses)

    def filter_courses(self) -> Tuple[Course]:
        for i, course in enumerate(self.courses):
            print(f"{i} - {course.code} | {course.name}")
        
        user_response = input(
            """İndirmek istediğiniz derslerin numarlarını, aralarında boşluk bırakarak girin
Tüm dersleri indirmek için boş bırakın ve enter'a basın
    > """
        )
        
        user_response = user_response.strip()
        if user_response:
            courses_filtered = []
            selected_indexes_raw = user_response.split(" ")
            for selected_index in selected_indexes_raw:
                try:
                    courses_filtered.append(self.courses[int(selected_index)])
                except ValueError:
                    self.logger.warning(f"Girilen '{selected_index}' bir sayı değil. Yok sayılacak.")
                except IndexError:
                    self.logger.warning(f"Girilen '{selected_index}' herhangi bir kursun numarası değil. Yok sayılacak.")
            courses_filtered = tuple(courses_filtered)

            indirilecek_dersler = ", ".join(course.name for course in courses_filtered)
            print(f"{indirilecek_dersler} dersleri indirilecek.")
            return courses_filtered
        else:
            print("Tüm dersler indirilecek.")
            return tuple(self.courses)

