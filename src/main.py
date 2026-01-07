import cataloguer
import product
import barcode
import display

row = 2

def searchProduct(barcode):
    name = product.getProductInformation(barcode)
    return name

def scan(sheetName):
    global row
    
    barcodeInfo = barcode.barcodeCamera()
    if not barcodeInfo:
        return

    correct = False
    while not correct:
        productName, author = searchProduct(barcodeInfo)        

        newProductName, barcodeCheck = display.check_product(productName, f"/tmp/Plantheon/{barcodeInfo}.jpg", barcodeInfo)

        if barcodeInfo == barcodeCheck:
            correct = True

    cataloguer.addProduct(sheetName, row, barcodeInfo, productName, author)
    row += 1

def main():
    global row

    row = cataloguer.createSheet("test")
    print(f"The starting row is: {row}")

    scanning = 1
    
    while scanning:
        scan("test")

main()
