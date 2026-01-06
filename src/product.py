from urllib.request import urlopen
from bs4 import BeautifulSoup

import requests

def getProductName(soup):
    nameHeader = soup.find("h1", class_="product-name")
    name = nameHeader.get_text()

    print(f"Name of the product is : {name}")

    return name

def getProductImage(soup, barcode):
    figureHeader = soup.find("figure", class_="product-image non-mobile")
    imageHeader = figureHeader.find("img")
    imageSource = imageHeader["src"]

    print(f"Image Source : {imageSource}")

    savePath = f"images/{barcode}.jpg"
    image = requests.get(imageSource)
    if image.status_code == 200:
        with open(savePath, 'wb') as file:
            file.write(image.content)
        print(f"Image saved")
    else:
        print(f"Failed to download image.")


def getProductInformation(barcode):
    url = f"https://go-upc.com/search?q={barcode}"
    page = urlopen(url)
    soup = BeautifulSoup(page, "lxml")
    
    name = getProductName(soup)

    getProductImage(soup, barcode)

# barcode = input("What is the barcode: ")
# getProductInformation(barcode);
