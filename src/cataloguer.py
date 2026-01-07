from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

import os

def createSheet(fileName):
    path = f"{fileName}.xlsx"

    if os.path.exists(path):
        workbook = load_workbook(path)
        worksheet = workbook.active
        
        row = 1
        while worksheet.cell(row=row, column=1).value:
            row += 1

        return row
    
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
    print(f"Created worksheet: {path}")
    return 2

def addProduct(fileName, row, barcodeInfo, productName, author):
    path = f"{fileName}.xlsx"
    
    workbook = load_workbook(path)
    worksheet = workbook.active

    worksheet.cell(row=row, column=1, value=barcodeInfo)
    worksheet.cell(row=row, column=2, value=author)
    worksheet.cell(row=row, column=3, value=productName)

    workbook.save(path)
    print("Successfully added product")
