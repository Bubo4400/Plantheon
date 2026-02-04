import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import cataloguer
import barcode
import product
import check


# ---------------- Sheet info card ----------------

class SheetInfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        title = QLabel("📦 Current Sheet")
        title.setStyleSheet("font-size:13px;color:#88c0d0;")
        layout.addWidget(title)

        self.name_label = QLabel("Not opened yet")
        self.name_label.setStyleSheet("""
            QLabel {
                font-size:16px;
                font-weight:bold;
                color:white;
            }
        """)
        layout.addWidget(self.name_label)

        self.setStyleSheet("""
            QWidget {
                background:#2e3440;
                border-radius:10px;
                padding:10px;
            }
        """)

    def update_info(self, sheet_name, item_count):
        if item_count > 0:
            self.name_label.setText(f"{sheet_name}.xlsx ({item_count} items)")
        else:
            self.name_label.setText(f"{sheet_name}.xlsx")


# ---------------- Manual barcode dialog ----------------

class ManualBarcodeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Barcode Entry")
        self.setFixedSize(300, 140)

        self.barcode = None

        layout = QVBoxLayout(self)

        label = QLabel("Enter barcode manually:")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Barcode")
        layout.addWidget(self.input)

        btn = QPushButton("Confirm")
        btn.clicked.connect(self.confirm)
        layout.addWidget(btn)

    def confirm(self):
        text = self.input.text().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Barcode cannot be empty")
            return
        self.barcode = text
        self.accept()


# ---------------- Items list dialog ----------------

class ItemsListDialog(QDialog):
    def __init__(self, items):
        super().__init__()
        self.setWindowTitle("Items Added")
        self.setFixedSize(420, 400)

        layout = QVBoxLayout(self)

        title = QLabel("📋 All Items in Excel File")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget {
                background:#2e3440;
                color:white;
                border-radius:8px;
                padding:6px;
            }
            QListWidget::item {
                padding:8px;
            }
            QListWidget::item:selected {
                background:#4c566a;
            }
        """)

        for name, barcode_val, author in items:
            text = f"{name}\nBarcode: {barcode_val}"
            if author:
                text += f"\nAuthor: {author}"
            list_widget.addItem(QListWidgetItem(text))

        layout.addWidget(list_widget)


# ---------------- Main window ----------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Plantheon Cataloguer")
        self.setFixedSize(560, 650)

        self.items_added = []  # Items added in current session

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)

        # Logo
        logo = QLabel()
        pixmap = QPixmap("logo.png")
        logo.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Excel name
        layout.addWidget(QLabel("Excel file name"))
        self.excel_input = QLineEdit("test")
        self.excel_input.setStyleSheet("padding:8px;font-size:14px;border-radius:6px;")
        self.excel_input.textChanged.connect(self.update_sheet_info)
        layout.addWidget(self.excel_input)

        # Sheet info
        self.sheet_info = SheetInfoWidget()
        layout.addWidget(self.sheet_info)

        # Buttons
        btn_layout = QHBoxLayout()

        scan_btn = QPushButton("Scan")
        manual_btn = QPushButton("Manual Entry")
        list_btn = QPushButton("View All Items")

        for btn in (scan_btn, manual_btn, list_btn):
            btn.setStyleSheet("""
                QPushButton {
                    padding:12px;
                    font-size:14px;
                    border-radius:8px;
                    background:#2e3440;
                    color:white;
                }
                QPushButton:hover {
                    background:#4c566a;
                }
            """)

        scan_btn.clicked.connect(self.scan)
        manual_btn.clicked.connect(self.manual_entry)
        list_btn.clicked.connect(self.show_all_items)

        btn_layout.addWidget(scan_btn)
        btn_layout.addWidget(manual_btn)
        btn_layout.addWidget(list_btn)

        layout.addLayout(btn_layout)

        # Update sheet info initially
        self.update_sheet_info()

    # ---------------- Actions ----------------

    def scan(self):
        value = barcode.barcodeCamera()
        if value:
            self.process_barcode(value)

    def manual_entry(self):
        dialog = ManualBarcodeDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.process_barcode(dialog.barcode)

    def process_barcode(self, barcode_value):
        product_name, author = product.getProductInformation(barcode_value)

        final_name, final_barcode = check.check_product(
            product_name,
            f"/tmp/Plantheon/{barcode_value}.jpg",
            barcode_value
        )

        if not final_name or not final_barcode:
            return

        # Get sheet name from input
        sheet = self.excel_input.text().strip() or "default"
        
        # Get next row and ensure file exists
        next_row = cataloguer.get_next_row(sheet)
        
        # Add product to Excel
        cataloguer.addProduct(
            sheet,
            next_row,
            final_barcode,
            final_name,
            author
        )

        # Update the sheet info display
        self.update_sheet_info()
        
        # Add to session items
        self.items_added.append((final_name, final_barcode, author))

    def update_sheet_info(self):
        """Update the sheet info widget based on current filename"""
        sheet = self.excel_input.text().strip() or "default"
        filename = f"{sheet}.xlsx"
        
        if os.path.exists(filename):
            item_count = cataloguer.get_item_count(sheet)
            self.sheet_info.update_info(sheet, item_count)
        else:
            self.sheet_info.name_label.setText("Not opened yet")

    def show_all_items(self):
        # Get sheet name from input
        sheet = self.excel_input.text().strip() or "default"
        filename = f"{sheet}.xlsx"
        
        if not os.path.exists(filename):
            QMessageBox.information(self, "No file", f"The file {filename} does not exist.")
            return
            
        # Get ALL items from the Excel file
        all_items = cataloguer.get_all_items(sheet)
        
        if not all_items:
            QMessageBox.information(self, "No items", "No items in the Excel file yet.")
            return

        dialog = ItemsListDialog(all_items)
        dialog.exec_()


# ---------------- Entry point ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
