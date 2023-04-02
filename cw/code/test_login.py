import time, os

import pytest
from _pytest.fixtures import FixtureRequest
from selenium.webdriver.common.by import By

from ui.fixtures import get_driver
from ui.pages.base_page import BasePage, PageNotOpenedExeption


class BaseCase:
    authorize = True

    @pytest.fixture(scope='function', autouse=True)
    def setup(self, driver, config, request: FixtureRequest, logger):
        self.driver = driver
        self.config = config
        self.logger = logger

        self.login_page = LoginPage(driver)
        if self.authorize:
            cookies = request.getfixturevalue('cookies')
            for cookie in cookies:
                self.driver.add_cookie(cookie)

            self.driver.refresh()
            self.main_page = MainPage(driver)

class WrongValue(Exception):
    pass

@pytest.fixture(scope='session')
def credentials():
    script_dir = os.path.dirname(__file__)
    rel_path = "/creds"
    with open(script_dir + rel_path, 'r') as f:
        user = f.readline().strip()
        password = f.readline().strip()

    return user, password


@pytest.fixture(scope='session')
def cookies(credentials, config):
    driver = get_driver(config['browser'])
    driver.get(config['url'])
    login_page = LoginPage(driver)
    login_page.login(*credentials)

    cookies = driver.get_cookies()
    driver.quit()
    return cookies


class MainPage(BasePage):
    url = 'https://target-sandbox.my.com/'


class LoginPage(BasePage):
    url = 'https://target-sandbox.my.com/'

    def login(self, user, password):
        self.click((By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/div/div/div/div/div[2]/div/div[1]'), 15)
        self.find((By.NAME, 'email')).send_keys(user)
        self.find((By.NAME, 'password')).send_keys(password)

        self.click((By.XPATH, '/html/body/div[2]/div/div[2]/div/div[4]/div[1]'))

        return MainPage(self.driver)


class DashboardPage(BasePage):
    url = 'https://target-sandbox.my.com/dashboard'


class ContactsPage(BasePage):
    url = 'https://target-sandbox.my.com/profile/contacts'
    
    def __init__(self, driver):
        self.driver = driver
        self.driver.get(self.url)
        self.is_opened()



class TestLogin(BaseCase):
    authorize = False
    
    def test_login(self, credentials):
        login_page = LoginPage(self.driver)
        login_page.login(*credentials)
        

class TestHeader(BaseCase):
    authorize = True

    def test_header(self):
        timeout = 15
        page = DashboardPage(self.driver)

        url = 'https://target-sandbox.my.com/billing'
        page.click((By.XPATH, '/html/body/div[1]/div[1]/div/div/div/div[2]/ul/li[3]/a'), timeout)
        if not page.driver.current_url.startswith(url):
            raise PageNotOpenedExeption(f'{url} did not open in {timeout} sec, current url {self.driver.current_url}')

        url = 'https://target-sandbox.my.com/profile'
        page.click((By.XPATH, '/html/body/div[1]/div[1]/div/div/div/div[2]/ul/li[6]/a'), timeout)
        if not page.driver.current_url.startswith(url):
            raise PageNotOpenedExeption(f'{url} did not open in {timeout} sec, current url {self.driver.current_url}')


class TestContacts(BaseCase):
    authorize = True

    def test_contacts_change(self):
        timeout = 15
        page = ContactsPage(self.driver)
        new_fullname = "fullname"

        fullname_field =  page.find((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div/ul/li[2]/div[1]/div/div/input'), timeout)
        fullname = fullname_field.get_attribute("value")

        if fullname == new_fullname:
            new_fullname = "newFullname"

        fullname_field.clear()
        fullname_field.send_keys(new_fullname)
        page.click((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div/div[4]/button/div'), timeout)

        page.refresh()
        fullname = page.find((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/div/ul/li[2]/div[1]/div/div/input'), timeout).get_attribute("value")
        if fullname != new_fullname:
            raise WrongValue(f'fullname must be {new_fullname} but it is {fullname}')


