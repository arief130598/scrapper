import datetime
import json
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pyodbc
import string
import re
import unidecode
import pandas as pd

chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/77.0.3865.90 Safari/537.36")
chrome_options.add_argument("Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
                            "*/*;q=0.8,application/signed-exchange;v=b3")
chrome_options.add_argument("Accept-Encoding: gzip, deflate, br")
chrome_options.add_argument("Accept-Language: en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7")
chrome_options.add_argument('cookie: _gcl_au=1.1.1823793498.1570803319; _fbp=fb.2.1570803319229.963816320; SPC_IA=-1; '
                            'SPC_F=lzdTdFn9lDaLVnKWRnboUIDX4Fk7ojc1; REC_T_ID=9494fbe0-ec31-11e9-a888-b496914fea38; '
                            '_gcl_aw=GCL.1572880920.Cj0KCQiAtf_tBRDtARIsAIbAKe12O8hCcDKowKHsotaObvhR'
                            '-1pGcw_K1PaJqoWsyYytuXUVV-KtSjkaAposEALw_wcB; _ga=GA1.3.1049602029.1572880972; '
                            '_gac_UA-61904553-8=1.1572880996.Cj0KCQiAtf_tBRDtARIsAIbAKe12O8hCcDKowKHsotaObvhR'
                            '-1pGcw_K1PaJqoWsyYytuXUVV-KtSjkaAposEALw_wcB; '
                            'cto_lwid=a20d9c0d-fb1b-4071-a893-7816fb16b75c; _med=affiliates; SPC_EC=-; SPC_U=-; '
                            'SPC_SI=o2jprtgr5ie9g907h0wvof4gi277y7qh; _gid=GA1.3.1661687575.1575346405; '
                            'csrftoken=iz7UQvbgu60crCYlaSBVRphT357auSj7; AMP_TOKEN=%24NOT_FOUND; '
                            'REC_MD_20=1575438194; _dc_gtm_UA-61904553-8=1; SPC_T_IV="7SoYJr/leMwZQwVgx8Yw9Q=="; '
                            'SPC_T_ID="zIQZlbAQ/rPOVv5hOdZRkRiAyc/ivMhK8cdMTwuy4NCfkIZICbCMeA4qXe5kDtB4TlK5ncnZ+D6'
                            '+SB6LBkaIE31yD6tFulQEpUEnZeemjHE="')

driver = webdriver.Chrome(executable_path='/root/PycharmProjects/scrapper/chromedriver', chrome_options=chrome_options)

dataakhir = []

for a in range(0, 100):
    url = 'https://shopee.co.id/Makanan-Minuman-cat.157?page=' + a.__str__() + '&sortBy=pop'
    driver.get(url)
    time.sleep(2)
    status = 1

    while status == 1:
        try:
            bottomscroll = driver.find_element_by_class_name('shopee-footer-section')
            actions = ActionChains(driver)
            actions.move_to_element(bottomscroll).perform()
            status = 0
        except Exception as e:
            print(e)
            driver.get(url)
            time.sleep(2)

    home = BeautifulSoup(driver.page_source, "lxml")
    data = home.findAll('script', type="application/ld+json")

    listproduk = []
    for x, i in enumerate(data):
        if x == 0 or x == 1:
            print(i)
        else:
            listproduk.append(json.loads(i.text))

    for i in listproduk:
        nama = i.get('name')

        namatemp = nama

        namatemp = namatemp.__str__().lower()  # Membuat string menjadi huruf pendek
        namatemp = namatemp.translate(
            str.maketrans(string.punctuation, ' ' * len(string.punctuation)))  # Menghapus punctuation
        namatemp = re.sub(r'\b[0-9]+\b\s*', '', namatemp)  # Menghapus kata yang cuma angka
        namatemp = re.sub(r'\w*\d\w*', '', namatemp).strip()  # Menghapus angka dalam kata
        namatemp = re.sub(' +', ' ', namatemp)  # Spasi yang berlebihan akibat punctuation menjadi 1 saja
        namatemp = unidecode.unidecode(namatemp)  # Normalisasi huruf unicode


        # remove duplicate
        def unique_list(l):
            ulist = []
            [ulist.append(v) for v in l if v not in ulist]
            return ulist


        # Menghapus kata yang ada dalam dictionary
        nama = ' '.join(unique_list(namatemp.split()))
        word = pd.read_csv('/root/PycharmProjects/scrapper/shopeemakanan.csv', encoding='cp1252', names=["words"])
        word_replace = word['words'].values.tolist()
        wordtest = nama.split()

        for z in wordtest:
            if z in word_replace:
                nama = nama.replace(z, '')

        nama = re.sub(' +', ' ', nama)
        nama = nama.strip()
        dataakhir.append(nama)
        datamakanan = pd.DataFrame(data=dataakhir)

driver.close()
