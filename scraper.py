import json
import time
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from requests_html import HTMLSession
import schedule


def get_subjects():
    """Function to get subjects list from json file."""
    try:
        with open('subjects.json', 'r', encoding='utf8') as file:
            subjects = json.loads(file.read())
            return subjects
    except FileNotFoundError:
        print("No subjects file or wrong format.")
        exit()


def login():
    """Function to log into the website"""
    print("Running ...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome("chromedriver", options=options)
    driver.get("URL")
    time.sleep(1)
    driver.find_element_by_id("identifiant").send_keys("USERNAME")
    time.sleep(1)
    driver.find_element_by_id("mdp").send_keys("PASSWORD")
    time.sleep(1)
    driver.find_element_by_id("mdp").send_keys(Keys.ENTER)
    
    print("Logged in ...")
    session = HTMLSession()
    session.cookies.update({c["name"]: c["value"] for c in driver.get_cookies()})
    driver.close()
    return session


def telegram_message(message, s=HTMLSession()):
    s.get("https://api.telegram.org/BOT_TOKEN/sendMessage?chat_id=CHAT_ID&text={}".format(message))


class Scraper:
    """Check for updates on the website"""

    def __init__(self, session=None, current_subject=None, urls=None):
        self.session = session
        self.text_course = ""
        self.current_subject = current_subject
        self.urls = urls

    def update_file(self):
        self.get_page()
        self.create_file()

    def check(self):
        self.get_page()
        self.compare()

    def get_page(self):
        for url in self.urls:
            r = self.session.get(url)
            course = r.html.find(
                ".course-content", first=True
            )
            self.text_course += f'\n\n\n{course.text}'

    def create_file(self):
        with open(f"Cours/{self.current_subject}.txt", "w", encoding="utf-8") as file:
            file.write(self.text_course)

    def compare(self):
        with open(f"Cours/{self.current_subject}.txt", "r", encoding="utf-8") as file:
            old = file.read()
        if self.text_course.split(' ') == old.split(' '):
            pass
        else:
            telegram_message(f"📲  Nouvel ajout en {self.current_subject}\n\n")
            self.create_file()


class GradesScraper:
    def __init__(self):
        self.url = ('URL')
        self.s = HTMLSession()
        r = self.s.get(self.url)
        self.page = r.html.find('#m_c_GridViewAuditeur', first=True).text

    def check_page(self):
        headers = {"User-Agent": "MY_USER_AGENT"}
        try:
            r = self.s.get(self.url)
            self.new_page = r.html.find('#m_c_GridViewAuditeur', first=True).text

            if self.new_page != self.page:
                telegram_message(f"📲  Nouvelle note ajoutée !\n\n{self.url.replace('&', '%26')}", self.s)
                self.page = self.new_page
        except Exception:
            telegram_message(f"There was an error scraping grades.\n\n{self.url.replace('&', '%26')}", self.s)


def checker():
    my_session = login()
    for subject in all_subjects:
        scraper = Scraper(my_session, subject, all_subjects[subject])
        scraper.check()


def updater():
    count = 0
    my_session = login()
    for subject in all_subjects:
        scraper = Scraper(my_session, subject, all_subjects[subject])
        scraper.update_file()
        count += 1

    print(f"{count} fichiers mis à jour.")

    telegram_message("Scraper Running ...  🌐")


if __name__ == '__main__':

    all_subjects = get_subjects()
    grades = GradesScraper()

    updater()

    schedule.every(20).minutes.do(grades.check_page)
    schedule.every(5).hours.do(checker)

    while True:
        schedule.run_pending()
        time.sleep(1)
