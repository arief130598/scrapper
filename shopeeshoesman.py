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

driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=chrome_options)
produkdriver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=chrome_options)

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=ecommerceta.database.windows.net;DATABASE'
                      '=ecommerceta;UID=knight;PWD=Arief-1305')
cursor = conn.cursor()

for a in range(0, 100):
    url = 'https://shopee.co.id/Sepatu-Pria-cat.35?page=' + a.__str__() + '&sortBy=pop'
    driver.get(url)
    time.sleep(2)
    bottomscroll = driver.find_element_by_class_name('shopee-footer-section')
    actions = ActionChains(driver)
    actions.move_to_element(bottomscroll).perform()
    home = BeautifulSoup(driver.page_source, "lxml")
    data = home.findAll('script', type="application/ld+json")

    listproduk = []
    for x, i in enumerate(data):
        if x == 0 or x == 1:
            print(i)
        else:
            listproduk.append(json.loads(i.text))

    for i in listproduk:
        namatemp = i.get('name')
        namatemp = namatemp.__str__().lower()
        namatemp = namatemp.translate(str.maketrans("", "", string.punctuation))
        namatemp = re.sub(' +', ' ', namatemp)
        namatemp = unidecode.unidecode(namatemp)

        # remove duplicate
        def unique_list(l):
            ulist = []
            [ulist.append(v) for v in l if v not in ulist]
            return ulist

        nama = ' '.join(unique_list(namatemp.split()))

        word = pd.read_csv('/home/knight/Documents/shopeeshoesman.csv', encoding='cp1252', names=["words"])
        word_replace = word['words'].values.tolist()
        wordtest = nama.split()

        for z in wordtest:
            if z in word_replace:
                nama = nama.replace(z, '')

        nama = re.sub(' +', ' ', nama)
        nama = nama.strip()

        if nama.__len__() <= 2:
            continue

        hargaarr = i.get('offers').get('price')
        if hargaarr is None:
            hargaarr = i.get('offers').get('lowPrice')

        hargaspl = hargaarr.split(sep='.')
        harga = int(hargaspl[0])
        urlproduk = i.get('url')

        produkdriver.get(urlproduk)
        time.sleep(2)

        produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
        kategori = produkpage.findAll('a', class_='JFOy4z')

        if kategori.__len__() == 0:
            continue

        if kategori[1].text != 'Sepatu Pria' or kategori[2].text == 'Aksesoris & Perawatan Sepatu' or kategori[2].text == 'Sandal':
            continue

        toko = produkpage.find('div', class_='_3Lybjn').text
        asaltokoelement = produkpage.findAll('div', class_='kIo6pj')

        asaltoko = ''
        for j in asaltokoelement:
            if j.label.text == 'Dikirim Dari':
                asaltoko = j.div.text
                asaltoko = asaltoko.split(sep='-')[0][:-1]

        jumlahterjualelement = produkpage.find('div', class_='_22sp0A').text
        jumlahterjualrplc1 = jumlahterjualelement.replace(',', '')
        jumlahterjualrplc2 = jumlahterjualrplc1.replace('RB', '00')
        jumlahterjual = int(jumlahterjualrplc2)

        jumlahulasanelement = produkpage.findAll('div', class_='_3Oj5_n')

        if jumlahulasanelement.__len__() == 0:
            jumlahulasan = 0

            try:
                cursor.execute(
                    "INSERT INTO dbo.ecommercetrends_shopeetaswanita([toko],[terjual],[jumlahulasan],[harga],[produk],[url],[asaltoko]) values (?,?,?,?,?,?,?)",
                    toko, jumlahterjual, jumlahulasan, harga, nama, urlproduk, asaltoko)
                conn.commit()
            except Exception as exc:
                print('DB Error Jumlah Ulasan : ' + exc.__str__())

            continue

        jumlahulasanelement = jumlahulasanelement[1].text
        jumlahulasanrplc1 = jumlahulasanelement.replace(',', '')
        jumlahulasanrplc2 = jumlahulasanrplc1.replace('RB', '00')
        jumlahulasan = int(jumlahulasanrplc2)

        try:
            cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_shopeetaswanita WHERE toko=? and produk=?", toko,
                           nama)
            cektoko = cursor.fetchall()
            cektoko = cektoko[0][0]
            if cektoko != 0:
                cursor.execute(
                    "UPDATE dbo.ecommercetrends_shopeetaswanita SET harga = ?, terjual= ?, jumlahulasan = ?, url=?, asaltoko=? WHERE toko=? and produk=?",
                    harga, jumlahterjual, jumlahulasan, urlproduk, asaltoko, toko, nama)
            else:
                cursor.execute(
                    "INSERT INTO dbo.ecommercetrends_shopeetaswanita([toko],[terjual],[jumlahulasan],[harga],[produk],[url],[asaltoko]) values (?,?,?,?,?,?,?)",
                    toko, jumlahterjual, jumlahulasan, harga, nama, urlproduk, asaltoko)
            conn.commit()
        except Exception as E:
            print('Input DB 1 : ' + E.__str__())
            continue

        bottomscroll = produkdriver.find_element_by_class_name('_2u0jt9')
        actions = ActionChains(produkdriver)
        actions.move_to_element(bottomscroll).perform()
        time.sleep(2)

        produkpage = BeautifulSoup(produkdriver.page_source, "lxml")

        ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

        try:
            SQL_Query = pd.read_sql_query(
                "SELECT CONCAT_WS(',', nama, variasi, rating, tanggal, review) as data FROM dbo.ecommercetrends_shopeetaswanitaulasan WHERE toko='%s' and produk='%s'" % (
                    toko, nama), conn)

            datasebelumnya = pd.DataFrame(SQL_Query)
            datasebelumnya = datasebelumnya['data'].to_list()
        except Exception as Exc:
            print('Latest Date' + Exc.__str__())


        def getdataulasan(data):
            namapengulas = ''
            for s in data:
                namapengulas = s.find('div', class_='shopee-product-rating__author-name').text
                ratingelement = s.findAll('svg', class_='icon-rating-solid')
                rating = ratingelement.__len__()
                review = s.find('div', class_='shopee-product-rating__content').text
                tanggalstr = s.find('div', class_='shopee-product-rating__time').text
                tanggalstr = tanggalstr.split()[0]
                tanggal = datetime.datetime.strptime(tanggalstr, '%Y-%m-%d')

                try:
                    variasi = s.find('span', class_='shopee-product-rating__variation').text
                except Exception as Exc:
                    print('Variasi : ' + Exc.__str__())
                    variasi = None

                datatemp = namapengulas + "," + variasi + "," + rating.__str__() + "," + tanggalstr + "," + review

                # input ke db
                if datatemp not in datasebelumnya:
                    try:
                        cursor.execute(
                            "INSERT INTO dbo.ecommercetrends_shopeetaswanitaulasan([nama],[variasi],[rating],[tanggal],[toko],[produk],[review]) values (?,?,?,?,?,?,?)",
                            namapengulas, variasi, rating, tanggal, toko, nama, review)
                        print(namapengulas, rating, variasi, review, tanggal)
                    except Exception as Exc:
                        print('Fail Insert Review :' + Exc.__str__())

            conn.commit()
            return namapengulas


        try:
            namatemp = ulasan[ulasan.__len__() - 1].find('div', class_='shopee-product-rating__author-name').text
        except Exception as e:
            print('Pengulas Terakhir : ' + e.__str__())
            continue
        namapengulas = ''

        while namatemp != namapengulas:
            try:
                produkdriver.find_element_by_class_name('shopee-icon-button--right').click()
            except Exception as E:
                print('Elemen Button : ' + E.__str__())
                continue
            namapengulas = getdataulasan(ulasan)
            time.sleep(2)
            produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
            ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')
            try:
                namatemp = ulasan[ulasan.__len__() - 1].find('div', class_='shopee-product-rating__author-name').text
            except Exception as e:
                print('Pengulas Terakhir : ' + e.__str__())
                continue

cursor.close()
conn.close()
produkdriver.close()
driver.close()
