import cv2
import numpy as np
from pyzbar import pyzbar


# ---------------------------------------------------------
# 1. Improved ROI detection
# ---------------------------------------------------------

def find_barcode_roi(gray):
    height, width = gray.shape

    # Blackhat morphology highlights dark barcode lines
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)

    # Gradient to emphasize vertical barcode lines
    gradX = cv2.Sobel(blackhat, cv2.CV_32F, 1, 0, ksize=3)
    gradX = cv2.convertScaleAbs(gradX)

    # Blur + threshold
    blurred = cv2.GaussianBlur(gradX, (9, 9), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Close gaps between barcode bars
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

    # Remove small noise
    closed = cv2.erode(closed, None, iterations=2)
    closed = cv2.dilate(closed, None, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Sort by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in contours[:5]:
        x, y, w, h = cv2.boundingRect(cnt)

        # Reject tiny or huge regions
        if w * h < (width * height * 0.002):
            continue
        if w < 40 or h < 20:
            continue

        # Expand ROI slightly
        pad = 10
        x = max(0, x - pad)
        y = max(0, y - pad)
        w = min(width - x, w + pad * 2)
        h = min(height - y, h + pad * 2)

        return x, y, w, h

    return None


# ---------------------------------------------------------
# 2. Stronger preprocessing for decoding
# ---------------------------------------------------------

def preprocess_image_for_barcode(roi_img):
    if len(roi_img.shape) == 3:
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi_img.copy()

    # CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Sharpening
    sharpen_kernel = np.array([
        [-1, -1, -1],
        [-1, 10, -1],
        [-1, -1, -1]
    ])
    sharp = cv2.filter2D(enhanced, -1, sharpen_kernel)

    # Upscale for better decoding
    upscale = cv2.resize(sharp, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)

    return upscale


# ---------------------------------------------------------
# 3. Improved camera scanner
# ---------------------------------------------------------

def barcodeCamera():
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Manual exposure helps barcode contrast
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    cam.set(cv2.CAP_PROP_EXPOSURE, -5)

    detection_history = []
    frame_count = 0

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame_count += 1

        # Resize for speed
        small = cv2.resize(frame, None, fx=0.6, fy=0.6)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        roi = None
        if frame_count % 2 == 0:
            roi = find_barcode_roi(gray)

        if roi:
            x, y, w, h = roi
            roi_img = gray[y:y+h, x:x+w]

            if roi_img.size > 0:
                processed = preprocess_image_for_barcode(roi_img)

                # Try multiple decoding passes
                attempts = [
                    processed,
                    cv2.GaussianBlur(processed, (3, 3), 0),
                    cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 11, 2),
                    cv2.Canny(processed, 50, 150)
                ]

                decoded = []
                for img in attempts:
                    barcodes = pyzbar.decode(img)
                    if barcodes:
                        decoded = barcodes
                        break

                if decoded:
                    value = decoded[0].data.decode("utf-8")
                    detection_history.append(value)

                    # Keep last 6 detections
                    if len(detection_history) > 6:
                        detection_history.pop(0)

                    # Confidence check
                    if detection_history.count(value) >= 4:
                        cam.release()
                        cv2.destroyAllWindows()
                        return value

                # Draw ROI
                cv2.rectangle(small, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(small, "ESC to quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Fast Barcode Scanner", small)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    return None


# ---------------------------------------------------------
# 4. Static image decoding
# ---------------------------------------------------------

def decode_barcode_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    processed = preprocess_image_for_barcode(gray)

    attempts = [
        gray,
        processed,
        cv2.GaussianBlur(processed, (3, 3), 0),
        cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                              cv2.THRESH_BINARY, 11, 2),
        cv2.Canny(processed, 50, 150)
    ]

    results = []
    for img in attempts:
        barcodes = pyzbar.decode(img)
        for b in barcodes:
            value = b.data.decode("utf-8")
            if value not in results:
                results.append(value)

    return results

