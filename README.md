# Plantheon Cataloguer

A professional desktop application for cataloguing products using barcode scanning, web product data enrichment, and Excel-based inventory management. Built with PyQt5 and computer vision.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Barcode Scanning** – Real‑time camera detection with ROI optimisation and multi‑stage decoding.
- **Manual Barcode Entry** – Fallback text input for problematic codes.
- **Product Data Fetching** – Automatically retrieves product name, author (where applicable), and cover image from [go‑upc.com](https://go-upc.com).
- **User Verification** – Confirmation dialog shows product image and name; allows barcode or name correction.
- **Excel Catalogue** – Stores barcode, author, and title in `.xlsx` files. Creates new files automatically with formatted headers.
- **Item List Viewer** – Browse all catalogued entries directly from the app.
- **Nord Dark UI** – Clean, eye‑friendly interface with sidebar navigation.

## Installation

### Prerequisites
- Python 3.8 or higher
- A working webcam (for scanning)

### Clone & Setup
```bash
git clone https://github.com/Bubo4400/Plantheon.git
cd Plantheon
```

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

1. **Run the application**
   ```bash
   python main.py
   ```
2. **Set the Excel filename** – Enter a name in the *Excel file name* field (e.g., `inventory`). A file `inventory.xlsx` will be created automatically.

3. **Add items**
   - **Scan** – Click *Scan* and show a barcode to the camera. The application will detect it, fetch product info, and show a confirmation dialog.
   - **Manual Entry** – Click *Manual Entry* and type the barcode digits.

4. **Verify / Correct** – After fetching, the product image and name are displayed. You can:
   - Accept (Yes) → store as is.
   - Reject (No) → correct the barcode or manually enter the product name.

5. **View All Items** – Click *View All Items* to see every entry in the current Excel file.

## Project Structure
```
Plantheon/
├── main.py # Application entry point
├── src/
│ ├── display.py # Main GUI window (PyQt5)
│ ├── barcode.py # Camera scanning, ROI detection, decoding
│ ├── product.py # Web scraping (go-upc.com) for name, author, image
│ ├── cataloguer.py # Excel file handling (openpyxl)
│ └── check.py # Verification dialogs and correction logic
├── logo.png # Optional: application logo (shown in GUI)
└── README.md
```

## How It Works

1. **Barcode acquisition** – The camera feed is processed with:
   - Blackhat morphology & Sobel gradients to locate barcode regions.
   - CLAHE contrast enhancement, sharpening, and upscaling before decoding.
   - Confidence‑based detection (requires 4 consistent reads).

2. **Product lookup** – The barcode is sent to `https://go-upc.com/search?q={barcode}`. BeautifulSoup extracts:
   - Product name (from `<h1 class="product-name">`)
   - Author (from the `table.table-striped`)
   - Cover image (saved to `/tmp/Plantheon/{barcode}.jpg`)

3. **Excel management** – `openpyxl` writes to `{filename}.xlsx` with three columns: *Barcode*, *Author*, *Title*. Headers are bold and column widths are preset.

## Configuration & Notes

- **Camera settings** – The scanner disables auto‑exposure and sets a manual exposure value (`-5`) for better contrast. Modify `barcode.py` if your camera behaves differently.
- **Temporary images** – Downloaded product images are stored in `/tmp/Plantheon/`. They are not deleted automatically.
- **Internet required** – Product information is fetched live from go‑upc.com. No API key is needed, but scraping may be rate‑limited.
- **Excel file location** – Files are saved in the same directory as the application. No external database is used.
- **Logo** – Place a `logo.png` in the root folder to display a custom image in the main window.

---

## Disclaimer

The (`display.py`, `check.py`) modules were generated with the assistance of an AI language model.

---

**Plantheon Cataloguer** – Simplify your inventory, one scan at a time.
