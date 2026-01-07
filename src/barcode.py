from pyzbar import pyzbar

import cv2

def readBarcodes(frame):
    global previousBarcode
    
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y, w, h = barcode.rect
        barcodeInfo = barcode.data.decode('utf-8')
        return frame, barcodeInfo

    return frame, ""

def barcodeCamera():
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    barcodeInfo = ""
    while ret:
        ret, frame = camera.read()
        frame, barcodeInfo = readBarcodes(frame)
        cv2.imshow('Real Time Barcode Scanner', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

        if barcodeInfo != "":
            ret = False
            
    camera.release()
    cv2.destroyAllWindows()
    return barcodeInfo
