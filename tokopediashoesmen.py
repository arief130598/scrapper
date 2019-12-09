from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent={0}'.format(user_agent))
driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=chrome_options)
driver.implicitly_wait(10)

url = 'https://shopee.co.id/Sepatu-Pria-cat.35'
driver.get(url)
home = BeautifulSoup(driver.page_source, "lxml")