import cv2
import numpy as np
from pyzbar import pyzbar

def find_barcode_roi(gray):
    # Use multiple gradient methods for better detection
    # 1. Sobel gradient (original method)
    gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
    gradient = cv2.subtract(gradX, gradY)
    gradient = cv2.convertScaleAbs(gradient)
    
    # 2. Scharr gradient (more sensitive to edges)
    gradX2 = cv2.Scharr(gray, cv2.CV_32F, 1, 0)
    gradY2 = cv2.Scharr(gray, cv2.CV_32F, 0, 1)
    gradient2 = cv2.convertScaleAbs(cv2.subtract(gradX2, gradY2))
    
    # 3. Combine gradients for robustness
    combined_gradient = cv2.addWeighted(gradient, 0.7, gradient2, 0.3, 0)
    
    # Adaptive blur based on image size
    height, width = gray.shape
    blur_size = min(9, int(width * 0.01) // 2 * 2 + 1)  # Odd number, max 9
    blur_size = max(3, blur_size)
    blurred = cv2.GaussianBlur(combined_gradient, (blur_size, blur_size), 0)
    
    # Adaptive thresholding instead of fixed
    thresh_value = np.mean(blurred) + np.std(blurred) * 0.5
    thresh_value = max(100, min(225, thresh_value))  # Keep in reasonable range
    _, thresh = cv2.threshold(blurred, thresh_value, 255, cv2.THRESH_BINARY)
    
    # Also try adaptive threshold as fallback
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Combine both thresholding methods
    combined_thresh = cv2.bitwise_or(thresh, adaptive_thresh)
    
    # Adjust morphological kernel based on image size
    kernel_width = max(5, int(width * 0.02) // 2 * 2 + 1)
    kernel_height = max(3, int(height * 0.01) // 2 * 2 + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, kernel_height))
    
    closed = cv2.morphologyEx(combined_thresh, cv2.MORPH_CLOSE, kernel)
    
    # Multiple erosion/dilation cycles
    closed = cv2.erode(closed, None, iterations=2)
    closed = cv2.dilate(closed, None, iterations=4)
    closed = cv2.erode(closed, None, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(
        closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        # Try alternative approach with Canny edges
        edges = cv2.Canny(gray, 50, 150)
        edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(
            edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
    
    if not contours:
        return None
    
    # Filter contours by multiple criteria
    valid_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # Area filter (dynamic based on image size)
        min_area = width * height * 0.001  # 0.1% of image area
        max_area = width * height * 0.3    # 30% of image area
        
        if area < min_area or area > max_area:
            continue
        
        # Aspect ratio filter (barcodes are usually elongated)
        aspect_ratio = w / h if h > 0 else 0
        if aspect_ratio < 1.5 and aspect_ratio > 0.2:  # Allow some rotation
            # Could be vertical or slightly rotated barcode
            pass
        elif aspect_ratio > 10:  # Too elongated, might be noise
            continue
        
        # Solidity check (barcodes are relatively solid rectangles)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        if solidity < 0.5:  # Too fragmented
            continue
        
        valid_contours.append((contour, area))
    
    if not valid_contours:
        return None
    
    # Sort by area (largest first) and take the best
    valid_contours.sort(key=lambda x: x[1], reverse=True)
    
    # Try the top 3 contours for barcode detection
    for contour, _ in valid_contours[:3]:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Expand ROI slightly to ensure full barcode capture
        expand_x = int(w * 0.1)
        expand_y = int(h * 0.1)
        x = max(0, x - expand_x)
        y = max(0, y - expand_y)
        w = min(gray.shape[1] - x, w + 2 * expand_x)
        h = min(gray.shape[0] - y, h + 2 * expand_y)
        
        # Skip if too small even after expansion
        if w * h < 1000:
            continue
            
        return x, y, w, h
    
    return None

def preprocess_image_for_barcode(roi_img):
    """Apply preprocessing to improve barcode reading"""
    # Convert to grayscale if not already
    if len(roi_img.shape) == 3:
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi_img.copy()
    
    # Apply CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Apply bilateral filter to reduce noise while keeping edges
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
    
    # Sharpening to enhance barcode lines
    kernel_sharpen = np.array([[-1, -1, -1],
                               [-1, 9, -1],
                               [-1, -1, -1]])
    sharpened = cv2.filter2D(filtered, -1, kernel_sharpen)
    
    return sharpened

def barcodeCamera():
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Adjust camera settings for better barcode reading
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
    cam.set(cv2.CAP_PROP_EXPOSURE, -4)  # Adjust as needed
    cam.set(cv2.CAP_PROP_CONTRAST, 1.0)
    
    barcode_history = []  # Store recent detections for confirmation
    frame_count = 0
    
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Downscale for speed (adjust based on performance needs)
        scale_factor = 0.6  # Slightly larger for better detection
        small = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor)
        
        # Convert to grayscale and equalize histogram
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Try different ROI detection approaches every few frames
        roi = None
        if frame_count % 2 == 0:
            # Use the main gradient method
            roi = find_barcode_roi(gray)
        
        if not roi and frame_count % 5 == 0:
            # Try on edge-detected version
            edges = cv2.Canny(gray, 50, 150)
            # Find the largest connected component in edges
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                if w * h > gray.shape[0] * gray.shape[1] * 0.001:  # Minimum size
                    roi = (x, y, w, h)
        
        if roi:
            x, y, w, h = roi
            
            # Extract ROI with padding
            pad = 5
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(gray.shape[1], x + w + pad)
            y2 = min(gray.shape[0], y + h + pad)
            roi_img = gray[y1:y2, x1:x2]
            
            # Skip if ROI is too small
            if roi_img.size == 0 or roi_img.shape[0] < 20 or roi_img.shape[1] < 20:
                cv2.rectangle(small, (x, y), (x+w, y+h), (0, 0, 255), 2)
            else:
                # Preprocess ROI for better barcode reading
                processed_roi = preprocess_image_for_barcode(roi_img)
                
                # Try decoding multiple times with different preprocessing
                barcodes = pyzbar.decode(processed_roi)
                
                if not barcodes:
                    # Try original ROI as fallback
                    barcodes = pyzbar.decode(roi_img)
                
                if not barcodes:
                    # Try with different binarization
                    _, thresh_roi = cv2.threshold(processed_roi, 0, 255, 
                                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    barcodes = pyzbar.decode(thresh_roi)
                
                for barcode in barcodes:
                    value = barcode.data.decode("utf-8")
                    barcode_type = barcode.type
                    
                    # Confirm with multiple frames
                    barcode_history.append((value, barcode_type))
                    if len(barcode_history) > 5:
                        barcode_history.pop(0)
                    
                    # Check if same barcode detected in multiple frames
                    if len(barcode_history) >= 3:
                        recent_values = [v for v, t in barcode_history[-3:]]
                        if all(v == value for v in recent_values):
                            cam.release()
                            cv2.destroyAllWindows()
                            return value
                    
                    # Draw barcode data on frame
                    cv2.rectangle(small, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(small, f"{barcode_type}: {value}", 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.5, (0, 255, 0), 2)
                else:
                    # Draw ROI even if no barcode decoded
                    cv2.rectangle(small, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Display instructions
        cv2.putText(small, "ESC to quit", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Fast Barcode Scanner", small)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
        
        # Reset frame count to avoid overflow
        if frame_count > 1000:
            frame_count = 0
    
    cam.release()
    cv2.destroyAllWindows()
    return None

# Optional: Add a function to decode from static image
def decode_barcode_from_image(image_path):
    """Decode barcode from image file"""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Multiple preprocessing attempts
    results = []
    
    # Try direct decoding
    barcodes = pyzbar.decode(gray)
    for barcode in barcodes:
        results.append(barcode.data.decode("utf-8"))
    
    # Try with different preprocessing
    preprocessed = preprocess_image_for_barcode(gray)
    barcodes = pyzbar.decode(preprocessed)
    for barcode in barcodes:
        value = barcode.data.decode("utf-8")
        if value not in results:
            results.append(value)
    
    # Try with Otsu thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    barcodes = pyzbar.decode(thresh)
    for barcode in barcodes:
        value = barcode.data.decode("utf-8")
        if value not in results:
            results.append(value)
    
    return results
