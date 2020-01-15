import json

from bs4 import BeautifulSoup
import requests

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "cookie": '_gcl_au=1.1.1823793498.1570803319; _fbp=fb.2.1570803319229.963816320; SPC_IA=-1; '
              'SPC_F=lzdTdFn9lDaLVnKWRnboUIDX4Fk7ojc1; REC_T_ID=9494fbe0-ec31-11e9-a888-b496914fea38; '
              '_gcl_aw=GCL.1572880920.Cj0KCQiAtf_tBRDtARIsAIbAKe12O8hCcDKowKHsotaObvhR-1pGcw_K1PaJqoWsyYytuXUVV'
              '-KtSjkaAposEALw_wcB; _ga=GA1.3.1049602029.1572880972; '
              '_gac_UA-61904553-8=1.1572880996.Cj0KCQiAtf_tBRDtARIsAIbAKe12O8hCcDKowKHsotaObvhR'
              '-1pGcw_K1PaJqoWsyYytuXUVV-KtSjkaAposEALw_wcB; cto_lwid=a20d9c0d-fb1b-4071-a893-7816fb16b75c; SPC_EC=-; '
              'SPC_U=-; csrftoken=Ec3x5ybfXSLam3qf8WbmEU7OWrSxlUz1; welcomePkgShown=true; '
              'SPC_SI=3c5gm5q4f342d6jdvo1jewe18azzha5q; _gid=GA1.3.2126539921.1578298224; REC_MD_20=1578302628; '
              'REC_MD_30_2000613063=1578303051; AMP_TOKEN=%24NOT_FOUND; SPC_T_IV="wp7Fs4/R33Uoq3AA5hIweg=="; '
              'SPC_T_ID="8gmGJxb0q5Zwsv3w0bwpVBmyI+Ts+eI0y55q1ESSpizGKuI8Tb1mppP7UhAHy/odU2QDYmF72xLlY/SFAPF8xm6gCjz'
              '+prZ9KUxLLtTRSbg="',
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 "
                  "Safari/537.36"}

url = "https://shopee.co.id/api/v2/search_items/?by=pop&limit=50&match_id=35&newest=0&order=desc&page_type=search&version=2"

homesource = requests.get(url, headers=headers).text
home = json.loads(homesource)

nexturl = home.find('li', class_='a-last').a['href']

pagination = True
while pagination:
    produkurl = home.findAll('h2', class_=['a-size-mini', 'a-spacing-none', 'a-color-base', 's-line-clamp-4'])

    for i in produkurl:
        fixprodukurl = 'https://www.amazon.com' + i.a['href']
        print(fixprodukurl)
        try:
            produksource = requests.get(fixprodukurl, headers=headers).text
        except Exception as ex:
            print('Product cant load', ex)
            continue

        produkpage = BeautifulSoup(produksource, "lxml")

        kategoriproduk = produkpage.select('a.a-link-normal.a-color-tertiary')

        statusman = False
        statusshoes = False
        if kategoriproduk.__len__() is not 0:
            listkategori = [i.text for i in kategoriproduk]
            for o, p in enumerate(listkategori):
                listkategori[o] = ''.join(e for e in p if e.isalnum())

            for e in listkategori:
                if e == 'Men':
                    statusman = True
                elif e == 'Shoes':
                    statusshoes = True

        if statusman is False or statusshoes is False:
            continue

        ulasanurl = produkpage.select('a.a-link-emphasis.a-text-bold')

        if ulasanurl.__len__() is not 0:
            fixulasanurl = 'https://www.amazon.com' + ulasanurl[0]['href']
            try:
                ulasansource = requests.get(fixulasanurl, headers=headers).text
            except Exception as ex:
                print("Review cant load", ex)
                continue
            ulasanpage = BeautifulSoup(ulasansource, "lxml")

            paginationulasan = True
            while paginationulasan:

                produktitle = ulasanpage.find('a', class_='a-link-normal').string
                toko = ulasanpage.find('div', class_=['a-row product-by-line']).a.string
                price = ulasanpage.find('span', class_=['a-color-price', 'arp-price']).string

                reviewtempsource = ulasanpage.select('div.a-section.review.aok-relative')

                for w in reviewtempsource:
                    user = w.find('span', class_='a-profile-name').text
                    rating = w.find('span', class_='a-icon-alt').text[0]
                    review = w.find('a', class_='review-title').span.text
                    date = w.find('span', class_='review-date').text
                    sizecolor = w.find('a', class_='a-color-secondary').text
                    size = None
                    color = None
                    if sizecolor != 'Report abuse':
                        for k, j in enumerate(sizecolor):
                            if j == 'C':
                                if k == 0:
                                    size = None
                                else:
                                    size = sizecolor[:k]
                                    size = size.split()[1]
                                if k == len(sizecolor):
                                    color = None
                                else:
                                    color = sizecolor[k:]
                                    color = color.split()
                                    temp = ""
                                    for m, n in enumerate(color):
                                        if m != 0:
                                            temp = temp + n + " "
                                    color = temp
                                break

                    print(user, rating, review, date, size, color, produktitle, toko, price, "\n")

                try:
                    nextulasan = ulasanpage.find('li', class_='a-last').a['href']
                except Exception as ex:
                    print('This is the last review', ex)
                    break

                fixulasanurl = 'https://www.amazon.com' + nextulasan
                try:
                    ulasansource = requests.get(fixulasanurl, headers=headers).text
                except Exception as ex:
                    print("Review cant load", ex)
                    continue
                ulasanpage = BeautifulSoup(ulasansource, "lxml")
        else:
            continue

    url = 'https://www.amazon.com' + nexturl
    try:
        homesource = requests.get(url, headers=headers).text
    except Exception as ex:
        print("Page cant load", ex)
        continue
    home = BeautifulSoup(homesource, "lxml")
    try:
        nexturl = home.find('li', class_='a-last').a['href']
    except Exception as ex:
        print('This is the last page', ex)
        break
