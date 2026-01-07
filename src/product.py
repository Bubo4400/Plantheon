from urllib.request import urlopen
from bs4 import BeautifulSoup

import requests
import os

def getProductName(soup):
    nameHeader = soup.find("h1", class_="product-name")
    name = nameHeader.get_text()

    print(f"Name of the product is : {name}")

    return name

def getProductImage(soup, barcode):
    if not os.path.exists("/tmp/Plantheon"):
        os.makedirs("/tmp/Plantheon")
        print(f"Folder '/tmp/Plantheon' created.")
    figureHeader = soup.find("figure", class_="product-image non-mobile")
    imageHeader = figureHeader.find("img")
    imageSource = imageHeader["src"]

    print(f"Image Source : {imageSource}")

    savePath = f"/tmp/Plantheon/{barcode}.jpg"
    image = requests.get(imageSource)
    if image.status_code == 200:
        with open(savePath, 'wb') as file:
            file.write(image.content)
        print(f"Image saved")
    else:
        print(f"Failed to download image.")

def getProductAuthor(soup):
    tableHeader = soup.find("table", class_ ="table table-striped")
    tableLines = tableHeader.find_all("tr")
    
    for line in tableLines:
        entries = line.find_all("td")
        
        if "Author" == entries[0].get_text():
            author = entries[1].get_text()

            print(f"The author is {author}")
            return author

    return None           

def getProductInformation(barcodeInfo):
    url = f"https://go-upc.com/search?q={barcodeInfo}"
    page = urlopen(url)
    soup = BeautifulSoup(page, "lxml")
    
    productName = getProductName(soup)

    author = getProductAuthor(soup)
        
    getProductImage(soup, barcodeInfo)
    
    return productName, author
