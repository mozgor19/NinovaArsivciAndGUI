# Bismillahirrahmanirrahim

from src.manager import Manager
from src.logger import Logger

from bs4 import BeautifulSoup
import requests


class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.logger = Logger()

    def check_connectivity(self) -> bool:
        try_URL = "http://www.example.com"
        try:
            requests.get(try_URL)
            return True
        except:
            return False

    def login(self) -> requests.session:
        _URL = Manager.URL.value + "/Kampus1"
        HEADERS = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0",
        }

        # Requesting and parsing the page
        session = requests.Session()
        page = session.get(_URL, headers=HEADERS)
        # try:
        #     page = session.get(_URL, headers=HEADERS)
        # except Exception as e:
        #     self.logger.warning("Ninova sunucusuna bağlanılamadı.")
        #     if self.check_connectivity():
        #         self.logger.fail("Internet var ancak Ninova'ya bağlanılamıyor.")
        #     else:
        #         self.logger.fail("Internete erişim yok. Bağlantınızı kontrol edin.")

        page = BeautifulSoup(page.content, "lxml")

        post_data = {}
        for field in page.find_all("input"):
            post_data[field.get("name")] = field.get("value")
        post_data["ctl00$ContentPlaceHolder1$tbUserName"] = self.username
        post_data["ctl00$ContentPlaceHolder1$tbPassword"] = self.password

        page = self._login_request(session, post_data, page)

        page = BeautifulSoup(page.content, "lxml")
        if page.find(id="ctl00_Header1_tdLogout") is None:
            raise PermissionError("Kullanıcı adı veya şifre yanlış!")
        return session

    def _login_request(
        self, session: requests.Session, post_data: dict, page: BeautifulSoup
    ) -> requests.session.post:
        page = session.post(
            "https://girisv3.itu.edu.tr" + page.form.get("action")[1:], data=post_data
        )
        return page
