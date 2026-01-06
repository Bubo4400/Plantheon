from pyzbar import pyzbar

import threading
import product
import cv2

previousBarcode = ""

def searchProduct(barcode):
    product.getProductInformation(barcode)

def read_barcodes(frame):
    global previousBarcode
    
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y, w, h = barcode.rect
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if previousBarcode != barcode_info:
            previousBarcode = barcode_info
            t = threading.Thread(target=searchProduct, args=(barcode_info,))
            t.start()

    return frame

def main():
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    while ret:
        ret, frame = camera.read()
        frame = read_barcodes(frame)
        cv2.imshow('Real Time Barcode Scanner', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
