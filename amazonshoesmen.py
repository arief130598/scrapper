from bs4 import BeautifulSoup
import requests

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "Cookie": "ad-id=A_8vZYnuQU0Bj-9RaUTT1nI; ad-privacy=0",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}

url = "https://www.amazon.com/s?i=fashion-mens-intl-ship&bbn=16225019011&rh=n%3A16225019011%2Cn%3A679255011&dc&page" \
      "=399&pf_rd_i=16225019011&pf_rd_m=ATVPDKIKX0DER&pf_rd_p=554625a3-8de1-4fdc-8877-99874d353388&pf_rd_r" \
      "=VGB06NBK532H1PB1MDWA&pf_rd_s=merchandised-search-4&pf_rd_t=101&qid=1575282332&ref=sr_pg_1 "

homesource = requests.get(url, headers=headers).text
home = BeautifulSoup(homesource, "lxml")

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
