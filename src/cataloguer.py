from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

import os

def get_next_row(fileName):
    """Get the next available row in an Excel file. Create file with headers if it doesn't exist."""
    path = f"{fileName}.xlsx"
    
    if not os.path.exists(path):
        # Create a new file with headers
        workbook = Workbook()
        worksheet = workbook.active

        worksheet["A1"] = "Barcode"
        worksheet["B1"] = "Author"
        worksheet["C1"] = "Title"

        worksheet["A1"].font = Font(bold=True, size=16)

        worksheet["B1"].font = Font(bold=True, size=16)
        worksheet["B1"].alignment = Alignment(horizontal="center")

        worksheet["C1"].font = Font(bold=True, size=16)
        worksheet["C1"].alignment = Alignment(horizontal="center")

        worksheet.column_dimensions["A"].width = 20
        worksheet.column_dimensions["B"].width = 30
        worksheet.column_dimensions["C"].width = 100

        workbook.save(path)
        print(f"Created new worksheet: {path}")
        return 2
    else:
        # Open existing file and find next empty row
        workbook = load_workbook(path)
        worksheet = workbook.active
        
        row = 1
        while worksheet.cell(row=row, column=1).value:
            row += 1
        
        print(f"Opened existing worksheet: {path}, next row: {row}")
        return row

def addProduct(fileName, row, barcodeInfo, productName, author):
    path = f"{fileName}.xlsx"
    
    workbook = load_workbook(path)
    worksheet = workbook.active

    worksheet.cell(row=row, column=1, value=barcodeInfo)
    worksheet.cell(row=row, column=2, value=author)
    worksheet.cell(row=row, column=3, value=productName)

    workbook.save(path)
    print(f"Successfully added product: {productName}")

def get_item_count(fileName):
    """Get the total number of items in the Excel file (excluding header)."""
    path = f"{fileName}.xlsx"
    
    if not os.path.exists(path):
        return 0
        
    workbook = load_workbook(path)
    worksheet = workbook.active
    
    count = 0
    row = 2  # Start from row 2 (after header)
    while worksheet.cell(row=row, column=1).value:
        count += 1
        row += 1
        
    return count

def get_all_items(fileName):
    """Get all items from the Excel file as a list of tuples (name, barcode, author)."""
    path = f"{fileName}.xlsx"
    
    if not os.path.exists(path):
        return []
        
    workbook = load_workbook(path)
    worksheet = workbook.active
    
    items = []
    row = 2  # Start from row 2 (after header)
    
    while worksheet.cell(row=row, column=1).value:
        barcode = worksheet.cell(row=row, column=1).value or ""
        author = worksheet.cell(row=row, column=2).value or ""
        name = worksheet.cell(row=row, column=3).value or ""
        
        items.append((name, barcode, author))
        row += 1
        
    return items
