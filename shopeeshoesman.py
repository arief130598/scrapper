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

# Pengaturan Chrome Driver
chrome_options = Options()
chrome_options.add_argument('--headless')
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

# Menjalankan driver
produkdriver = webdriver.Chrome(executable_path='/home/ubuntu/chromedriver', chrome_options=chrome_options)

# Mengulang sebanyak 100 kali, karna maximum page yang dapat di load di Shopee cuma 100
for a in range(0, 100):
    # Membuka halaman page dengan driver
    url = 'https://shopee.co.id/Sepatu-Pria-cat.35?page=' + a.__str__() + '&sortBy=pop'
    produkdriver.get(url)
    time.sleep(2)

    # Driver harus di scroll terlebih dahulu baru keluar karena Javascript
    # Jika scroll error refresh halaman
    status = 1
    while status == 1:
        try:
            bottomscroll = produkdriver.find_element_by_class_name('shopee-footer-section')
            actions = ActionChains(produkdriver)
            actions.move_to_element(bottomscroll).perform()
            status = 0
        except Exception as e:
            print(e)
            produkdriver.get(url)
            time.sleep(2)

    # Parsing page dengan BeautifulSoup
    home = BeautifulSoup(produkdriver.page_source, "lxml")
    data = home.findAll('script', type="application/ld+json")

    # Data tiap produk didalam 1 page dimasukan ke dalam list
    listproduk = []
    for x, i in enumerate(data):
        if x == 0 or x == 1:
            print(i)
        else:
            listproduk.append(json.loads(i.text))

    # Membaca setiap produk
    for i in listproduk:
        # Membuka koneksi database
        conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=ecommerceta.database.windows.net;DATABASE'
                              '=ecommerceta;UID=knight;PWD=Arief-1305')
        cursor = conn.cursor()

        # Mendapatkan nama produk sekaligus preprocessing
        namatemp = i.get('name')
        namatemp = namatemp.__str__().lower()  # Membuat string menjadi huruf pendek
        namatemp = namatemp.translate(str.maketrans("", "", string.punctuation))  # Menghapus punctuation
        namatemp = re.sub(' +', ' ', namatemp)  # Spasi yang berlebihan akibat punctuation menjadi 1 saja
        namatemp = unidecode.unidecode(namatemp)  # Normalisasi huruf unicode

        # remove duplicate
        def unique_list(l):
            ulist = []
            [ulist.append(v) for v in l if v not in ulist]
            return ulist

        # Menghapus kata yang ada dalam dictionary
        nama = ' '.join(unique_list(namatemp.split()))
        word = pd.read_csv('/home/ubuntu/shopeeshoesman.csv', encoding='cp1252', names=["words"])
        word_replace = word['words'].values.tolist()
        wordtest = nama.split()

        for z in wordtest:
            if z in word_replace:
                nama = nama.replace(z, '')

        nama = re.sub(' +', ' ', nama)
        nama = nama.strip()

        # Jika nama hasil preprocess dictionary terhapus semau maka lanjut produk selanjutnya
        if nama.__len__() <= 2:
            continue

        # Mendapatkan harga produk
        hargaarr = i.get('offers').get('price')
        if hargaarr is None:
            hargaarr = i.get('offers').get('lowPrice')

        hargaspl = hargaarr.split(sep='.')
        harga = int(hargaspl[0])

        # Membuka halaman produk untuk mendapatkan informasi lebih detail
        urlproduk = i.get('url')
        produkdriver.get(urlproduk)
        time.sleep(2)

        produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
        kategori = produkpage.findAll('a', class_='JFOy4z')

        # Cek jika element kategori di scrape atau tidak, jika tidak coba scrape ulang
        while kategori.__len__() == 0:
            produkdriver.get(urlproduk)
            time.sleep(2)

            produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
            kategori = produkpage.findAll('a', class_='JFOy4z')

        # Jika kategori tidak sesuai lanjut ke produk selanjutnya
        if kategori[1].text != 'Sepatu Pria' or kategori[2].text == 'Aksesoris & Perawatan Sepatu' or kategori[2].text == 'Sandal':
            continue

        toko = produkpage.find('div', class_='_3Lybjn').text  # Mendapatkan nama toko

        # Mendapatkan asal toko
        asaltokoelement = produkpage.findAll('div', class_='kIo6pj')

        asaltoko = ''
        for j in asaltokoelement:
            if j.label.text == 'Dikirim Dari':
                asaltoko = j.div.text
                asaltoko = asaltoko.split(sep='-')[0][:-1]

        # Mendapatkan data jumlah terjual
        jumlahterjualelement = produkpage.find('div', class_='_22sp0A').text
        jumlahterjualrplc1 = jumlahterjualelement.replace(',', '')
        jumlahterjualrplc2 = jumlahterjualrplc1.replace('RB', '00')
        jumlahterjual = int(jumlahterjualrplc2)

        # Mendapatkan jumlah ulasan element
        jumlahulasanelement = produkpage.findAll('div', class_='_3Oj5_n')

        # Jika jumlah ulasan 0 maka tidak perlu input data ulasan dan langsung ke produk selanjutnya
        if jumlahulasanelement.__len__() == 0:
            jumlahulasan = 0
            # Input data umum toko ke DB
            try:
                cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_shopeesepatupria WHERE toko=? and url=?",
                               toko, urlproduk)
                cektoko = cursor.fetchall()
                cektoko = cektoko[0][0]

                # Cek jika informasi toko sebelumnya di db jika ada update data saja
                if cektoko != 0:
                    cursor.execute(
                        "UPDATE dbo.ecommercetrends_shopeesepatupria SET harga = ?, terjual= ?, jumlahulasan = ?, produk=?, asaltoko=? WHERE toko=? and url=?",
                        harga, jumlahterjual, jumlahulasan, nama, asaltoko, toko, urlproduk)
                else:
                    cursor.execute(
                        "INSERT INTO dbo.ecommercetrends_shopeesepatupria([toko],[terjual],[jumlahulasan],[harga],[produk],[url],[asaltoko]) values (?,?,?,?,?,?,?)",
                        toko, jumlahterjual, jumlahulasan, harga, nama, urlproduk, asaltoko)
                conn.commit()
            except Exception as E:
                print('Input DB 1 : ' + E.__str__())
            continue

        # Mendapatkan data jumlah ulasan
        jumlahulasanelement = jumlahulasanelement[1].text
        jumlahulasanrplc1 = jumlahulasanelement.replace(',', '')
        jumlahulasanrplc2 = jumlahulasanrplc1.replace('RB', '00')
        jumlahulasan = int(jumlahulasanrplc2)

        # Input data umum toko ke DB
        try:
            cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_shopeesepatupria WHERE toko=? and url=?", toko,
                           urlproduk)
            cektoko = cursor.fetchall()
            cektoko = cektoko[0][0]

            # Cek jika informasi toko sebelumnya di db jika ada update data saja
            if cektoko != 0:
                cursor.execute(
                    "UPDATE dbo.ecommercetrends_shopeesepatupria SET harga = ?, terjual= ?, jumlahulasan = ?, produk=?, asaltoko=? WHERE toko=? and url=?",
                    harga, jumlahterjual, jumlahulasan, nama, asaltoko, toko, urlproduk)
            else:
                cursor.execute(
                    "INSERT INTO dbo.ecommercetrends_shopeesepatupria([toko],[terjual],[jumlahulasan],[harga],[produk],[url],[asaltoko]) values (?,?,?,?,?,?,?)",
                    toko, jumlahterjual, jumlahulasan, harga, nama, urlproduk, asaltoko)
            conn.commit()
        except Exception as E:
            print('Input DB 1 : ' + E.__str__())
            continue

        # Page harus discroll kebawah agar data ulasan muncul
        status = 1
        while status == 1:
            try:
                bottomscroll = produkdriver.find_element_by_class_name('_2u0jt9')
                actions = ActionChains(produkdriver)
                actions.move_to_element(bottomscroll).perform()
                time.sleep(2)
                status = 0
            except Exception as e:
                print(e)
                urlproduk = i.get('url')
                produkdriver.get(urlproduk)
                time.sleep(2)

        produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
        ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

        # Mengambil data ulasan sebelumnya untuk mencegah duplikat ulasan yang sama
        try:
            SQL_Query = pd.read_sql_query(
                "SELECT CONCAT_WS(',', nama, variasi, rating, tanggal, review) as data FROM dbo.ecommercetrends_shopeesepatupriaulasan WHERE toko='%s' and url='%s'" % (
                    toko, urlproduk), conn)

            datasebelumnya = pd.DataFrame(SQL_Query)
            datasebelumnya = datasebelumnya['data'].to_list()
        except Exception as Exc:
            print('Latest Date' + Exc.__str__())
            continue


        def getdataulasan(data):
            # Membuka koneksi
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};SERVER=ecommerceta.database.windows.net;DATABASE'
                '=ecommerceta;UID=knight;PWD=Arief-1305')
            cursor = conn.cursor()

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

                # Cek jika ulasan yang sama sudah ada, jika tidak input ke DB
                if datatemp not in datasebelumnya:
                    try:
                        cursor.execute(
                            "INSERT INTO dbo.ecommercetrends_shopeesepatupriaulasan([nama],[variasi],[rating],[tanggal],[toko],[produk],[review],[url]) values (?,?,?,?,?,?,?,?)",
                            namapengulas, variasi, rating, tanggal, toko, nama, review, urlproduk)
                        print(datatemp)
                    except Exception as Exc:
                        print('Fail Insert Review :' + Exc.__str__())

            conn.commit()
            return namapengulas

        # Mengambil nama pengulas terakhir buat dibandingkan dengan page ulasan selanjutnya
        status = 1
        while status == 1:
            try:
                namatemp = ulasan[ulasan.__len__() - 1].find('div', class_='shopee-product-rating__author-name').text
                status = 0
            except Exception as E:
                print(E)
                time.sleep(2)
                produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
                ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

        namapengulas = ''

        print(urlproduk)

        # Jika sama berarti nama pengulas tersebut adalah pengulas terakhir
        while namatemp != namapengulas:

            namapengulas = getdataulasan(ulasan)

            status = 1
            while status == 1:
                try:
                    produkdriver.find_element_by_class_name('shopee-icon-button--right').click()
                    status = 0
                except Exception as e:
                    print(e)
                    time.sleep(2)
                    produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
                    ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

            time.sleep(2)
            produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
            ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

            status = 1
            stattemp = 0
            while status == 1:
                try:
                    namatemp = ulasan[ulasan.__len__() - 1].find('div', class_='shopee-product-rating__author-name').text
                    status = 0
                    stattemp = stattemp + 1
                except Exception as E:
                    print(E)
                    time.sleep(2)
                    produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
                    ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')

                    if stattemp == 3:
                        try:
                            produkdriver.find_element_by_class_name('shopee-icon-button--left').click()
                            time.sleep(2)
                            produkdriver.find_element_by_class_name('shopee-icon-button--right').click()
                            time.sleep(2)
                            status2 = 0
                        except Exception as e:
                            print(e)
                            time.sleep(2)
                            produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
                            ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')
                        stattemp = 0

        cursor.close()
        conn.close()

produkdriver.close()
