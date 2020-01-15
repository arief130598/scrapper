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
# produkdriver = webdriver.Chrome(executable_path='/root/PycharmProjects/scrapper/chromedriver', chrome_options=chrome_options)
ecommerce = 'Shopee'

# Mengulang sebanyak 100 kali, karna maximum page yang dapat di load di Shopee cuma 100
for a in range(0, 10):
    # Membuka halaman page dengan driver
    url = 'https://shopee.co.id/Laptop-cat.134.1367?page=' + a.__str__() + '&sortBy=pop'
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
        conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=ecommerceanalysis.database.windows.net;DATABASE'
                              '=ecommerceanalysis;UID=knight;PWD=Arief-1305')
        cursor = conn.cursor()

        # Mendapatkan nama produk sekaligus preprocessing
        namatemp = i.get('name')
        namatemp = namatemp.__str__().lower()  # Membuat string menjadi huruf pendek
        namatemp = namatemp.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))  # Menghapus punctuation
        namatemp = re.sub(' +', ' ', namatemp)  # Spasi yang berlebihan akibat punctuation menjadi 1 saja
        namatemp = unidecode.unidecode(namatemp)  # Normalisasi huruf unicode

        # remove duplicate
        def unique_list(l):
            ulist = []
            [ulist.append(v) for v in l if v not in ulist]
            return ulist

        # Menghapus kata yang ada dalam dictionary
        nama = ' '.join(unique_list(namatemp.split()))
        word = pd.read_csv('/home/ubuntu/shopeelaptop.csv', encoding='cp1252', names=["words"])
        # word = pd.read_csv('/root/PycharmProjects/scrapper/shopeeshoesman.csv', encoding='cp1252', names=["words"])
        word_replace = word['words'].values.tolist()
        wordtest = nama.split()

        for z in wordtest:
            if z in word_replace:
                nama = nama.replace(z, '')

        nama = re.sub(' +', ' ', nama)
        nama = nama.strip()

        # Jika nama hasil preprocess dictionary terhapus semua maka lanjut produk selanjutnya
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
            print('Kategori not found')
            produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
            kategori = produkpage.findAll('a', class_='JFOy4z')

        # Jika kategori tidak sesuai lanjut ke produk selanjutnya
        if kategori[1].text != 'Komputer & Aksesoris' or kategori[2].text != 'Laptop':
            continue

        if kategori[2].text is not None:
            kategori = kategori[1].text + ' - ' + kategori[2].text
        else:
            kategori = kategori[1].text

        toko = produkpage.find('div', class_='_3Lybjn').text  # Mendapatkan nama toko
        urltoko = produkpage.find('a', class_='_136nGn')['href']  # Mendapatkan url toko

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
                cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_toko WHERE urltoko=?", urltoko)
                cektoko = cursor.fetchall()
                cektoko = cektoko[0][0]

                # Cek jika informasi toko sebelumnya di db jika ada update data saja
                if cektoko != 0:
                    cursor.execute(
                        "UPDATE dbo.ecommercetrends_toko SET nama_toko = ?, alamat= ?, ecommerce=? WHERE urltoko=?",
                        toko, asaltoko, ecommerce, urltoko)
                else:
                    cursor.execute(
                        "INSERT INTO dbo.ecommercetrends_toko([urltoko],[nama_toko],[alamat],[ecommerce]) values (?,?,?,?)",
                        urltoko, toko, asaltoko, ecommerce)

                cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_produk WHERE urlproduk=?", urlproduk)
                cekproduk = cursor.fetchall()
                cekproduk = cekproduk[0][0]

                # Cek jika informasi produk sebelumnya di db jika ada update data saja
                if cekproduk != 0:
                    cursor.execute(
                        "UPDATE dbo.ecommercetrends_produk SET nama_produk = ?, jumlah_terjual= ?, jumlah_ulasan=?, kategori=? WHERE urlproduk=?",
                        nama, jumlahterjual, jumlahulasan, kategori, urlproduk)
                else:
                    cursor.execute(
                        "INSERT INTO dbo.ecommercetrends_produk([urlproduk],[nama_produk],[jumlah_terjual],[jumlah_ulasan],[kategori],[toko_id]) values (?,?,?,?,?,?)",
                        urlproduk, nama, jumlahterjual, jumlahulasan, kategori, urltoko)
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
            cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_toko WHERE urltoko=?", urltoko)
            cektoko = cursor.fetchall()
            cektoko = cektoko[0][0]

            # Cek jika informasi toko sebelumnya di db jika ada update data saja
            if cektoko != 0:
                cursor.execute(
                    "UPDATE dbo.ecommercetrends_toko SET nama_toko = ?, alamat= ?, ecommerce=? WHERE urltoko=?",
                    toko, asaltoko, ecommerce, urltoko)
            else:
                cursor.execute(
                    "INSERT INTO dbo.ecommercetrends_toko([urltoko],[nama_toko],[alamat],[ecommerce]) values (?,?,?,?)",
                    urltoko, toko, asaltoko, ecommerce)

            cursor.execute("SELECT COUNT(1) FROM dbo.ecommercetrends_produk WHERE urlproduk=?", urlproduk)
            cekproduk = cursor.fetchall()
            cekproduk = cekproduk[0][0]

            # Cek jika informasi produk sebelumnya di db jika ada update data saja
            if cekproduk != 0:
                cursor.execute(
                    "UPDATE dbo.ecommercetrends_produk SET nama_produk = ?, jumlah_terjual= ?, jumlah_ulasan=?, kategori=? WHERE urlproduk=?",
                    nama, jumlahterjual, jumlahulasan, kategori, urlproduk)
            else:
                cursor.execute(
                    "INSERT INTO dbo.ecommercetrends_produk([urlproduk],[nama_produk],[jumlah_terjual],[jumlah_ulasan],[kategori],[toko_id]) values (?,?,?,?,?,?)",
                    urlproduk, nama, jumlahterjual, jumlahulasan, kategori, urltoko)
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
                "SELECT CONCAT_WS(',', nama_pengulas, variasi, rating, tanggal, ulasan) as data FROM dbo.ecommercetrends_ulasan WHERE produk_id='%s'" % (urlproduk), conn)

            datasebelumnya = pd.DataFrame(SQL_Query)
            datasebelumnya = datasebelumnya['data'].to_list()
        except Exception as Exc:
            print('Latest Date' + Exc.__str__())
            continue


        def xstr(s):
            if s is None:
                return ''
            return str(s)


        def getdataulasan(data):
            # Membuka koneksi
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};SERVER=ecommerceanalysis.database.windows.net;DATABASE'
                '=ecommerceanalysis;UID=knight;PWD=Arief-1305')
            cursor = conn.cursor()

            namapengulas = ''
            for s in data:
                namapengulas = s.find('div', class_='shopee-product-rating__author-name').text
                ratingelement = s.findAll('svg', class_='icon-rating-solid')
                rating = ratingelement.__len__()
                review = s.find('div', class_='shopee-product-rating__content').text
                tanggalstr = s.find('div', class_='shopee-product-rating__time').text
                tanggal = datetime.datetime.strptime(tanggalstr, '%Y-%m-%d %H:%M')

                try:
                    variasi = s.find('span', class_='shopee-product-rating__variation').text
                except Exception as Exc:
                    print('Variasi : ' + Exc.__str__())
                    variasi = None

                datatemp = xstr(namapengulas) + "," + xstr(variasi) + "," + xstr(rating) + "," + xstr(tanggalstr + ':00.0000000') + "," + xstr(review)

                # Cek jika ulasan yang sama sudah ada, jika tidak input ke DB
                if datatemp not in datasebelumnya:
                    try:
                        cursor.execute(
                            "INSERT INTO dbo.ecommercetrends_ulasan([nama_pengulas],[variasi],[rating],[tanggal],[ulasan],[produk_id]) values (?,?,?,?,?,?)",
                            namapengulas, variasi, rating, tanggal, review, urlproduk)
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
        nextproduk = 0
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
            errorindex = 0
            while status == 1:
                try:
                    namatemp = ulasan[ulasan.__len__() - 1].find('div', class_='shopee-product-rating__author-name').text
                    status = 0
                except Exception as E:
                    print(E)
                    produkdriver.find_element_by_class_name('shopee-icon-button--left').click()
                    time.sleep(2)
                    produkdriver.find_element_by_class_name('shopee-icon-button--right').click()
                    time.sleep(2)
                    produkpage = BeautifulSoup(produkdriver.page_source, "lxml")
                    ulasan = produkpage.findAll('div', class_='shopee-product-rating__main')
                    errorindex = errorindex + 1

                    #Jika sudah error 15 kali reload
                    if errorindex == 15:
                        produkdriver.get(urlproduk)
                        time.sleep(2)

                        # Page harus discroll kebawah agar data ulasan muncul
                        statusnext = 1
                        while statusnext == 1:
                            try:
                                bottomscroll = produkdriver.find_element_by_class_name('_2u0jt9')
                                actions = ActionChains(produkdriver)
                                actions.move_to_element(bottomscroll).perform()
                                time.sleep(2)
                                statusnext = 0
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
                                "SELECT CONCAT_WS(',', nama_pengulas, variasi, rating, tanggal, ulasan) as data FROM dbo.ecommercetrends_ulasan WHERE produk_id='%s'" % (
                                    urlproduk), conn)

                            datasebelumnya = pd.DataFrame(SQL_Query)
                            datasebelumnya = datasebelumnya['data'].to_list()
                        except Exception as Exc:
                            print('Latest Date' + Exc.__str__())
                            continue
                        namapengulas = ''

                    elif errorindex > 25:
                        status = 0
                        nextproduk = 1
                        break

            if nextproduk == 1:
                break

        cursor.close()
        conn.close()

produkdriver.close()
