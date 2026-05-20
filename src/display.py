import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QDialog, QMessageBox, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize


from src import cataloguer, product, barcode, check


# ---------------- Sheet info card ----------------

class SheetInfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 12, 14, 12)

        title = QLabel("Current Sheet")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #88c0d0;")
        layout.addWidget(title)

        self.name_label = QLabel("Not opened yet")
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #eceff4;
            }
        """)
        layout.addWidget(self.name_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #2b3038;
                border-radius: 10px;
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
        self.setFixedSize(320, 160)

        self.barcode = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        label = QLabel("Enter barcode manually:")
        label.setStyleSheet("font-size: 14px;")
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
        self.setWindowTitle("All Items")
        self.setFixedSize(520, 540)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e222a;
            }
            QLabel {
                color: #eceff4;
            }
            QScrollArea {
                background-color: #2b3038;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("All Items in Excel File")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#eceff4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Scrollable area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setSpacing(12)

        for name, barcode_val, author in items:
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background-color: #2b3038;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)

            name_label = QLabel(f"<b>{name}</b>")
            name_label.setWordWrap(True)
            barcode_label = QLabel(f"<span style='color:#88c0d0;'>Barcode:</span> {barcode_val}")
            author_label = QLabel(f"<span style='color:#88c0d0;'>Author:</span> {author or '—'}")

            for lbl in (name_label, barcode_label, author_label):
                lbl.setTextFormat(Qt.RichText)
                lbl.setWordWrap(True)
                card_layout.addWidget(lbl)

            scroll_layout.addWidget(card)

        container.setLayout(scroll_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

# ---------------- Main window ----------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Plantheon Cataloguer")
        self.setFixedSize(780, 520)

        # Global Nord-style application stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e222a;
            }

            QLabel {
                color: #eceff4;
                font-size: 14px;
            }

            QLineEdit {
                background: #2b3038;
                border: 1px solid #3a404a;
                border-radius: 6px;
                padding: 8px;
                color: #eceff4;
                font-size: 14px;
            }

            QPushButton {
                background: #2b3038;
                border: 1px solid #3a404a;
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 14px;
                color: #eceff4;
            }

            QPushButton:hover {
                background: #3a404a;
                border: 1px solid #4c566a;
            }

            QPushButton:pressed {
                background: #4c566a;
            }

            QDialog {
                background-color: #1e222a;
            }

            QMessageBox {
                background-color: #1e222a;
            }
        """)

        self.items_added = []  # Items added in current session

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ----- Sidebar -----
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # ----- Main content -----
        main_content = self._build_main_content()
        root_layout.addWidget(main_content, 1)

        # Update sheet info initially
        self.update_sheet_info()

    # ---------------- Sidebar construction ----------------

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2b3038;
                border-right: 1px solid #3a404a;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        # App title
        title = QLabel("Plantheon")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #eceff4;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Cataloguer")
        subtitle.setStyleSheet("font-size: 13px; color: #88c0d0;")
        layout.addWidget(subtitle)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #3a404a;")
        layout.addWidget(line)

        # Sidebar buttons
        self.scan_btn = QPushButton("Scan")
        self.manual_btn = QPushButton("Manual Entry")
        self.list_btn = QPushButton("View All Items")

        for btn in (self.scan_btn, self.manual_btn, self.list_btn):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(34)

        self.scan_btn.clicked.connect(self.scan)
        self.manual_btn.clicked.connect(self.manual_entry)
        self.list_btn.clicked.connect(self.show_all_items)

        layout.addWidget(self.scan_btn)
        layout.addWidget(self.manual_btn)
        layout.addWidget(self.list_btn)

        layout.addStretch(1)

        # Footer info
        footer = QLabel("Nord dark UI")
        footer.setStyleSheet("font-size: 11px; color: #616e88;")
        footer.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        layout.addWidget(footer)

        return sidebar

    # ---------------- Main content construction ----------------

    def _build_main_content(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(20)

        # Header
        header = QLabel("Plantheon Cataloguer")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #eceff4;
        """)
        layout.addWidget(header)

        # Logo centered
        logo_wrapper = QWidget()
        logo_layout = QHBoxLayout(logo_wrapper)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)

        logo = QLabel()
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo, alignment=Qt.AlignCenter)

        layout.addWidget(logo_wrapper)

        # Excel file card
        excel_card = QWidget()
        excel_card.setStyleSheet("""
            QWidget {
                background-color: #2b3038;
                border-radius: 10px;
            }
        """)
        excel_layout = QVBoxLayout(excel_card)
        excel_layout.setContentsMargins(14, 12, 14, 12)
        excel_layout.setSpacing(8)

        label = QLabel("Excel file name")
        label.setStyleSheet("font-size: 13px; color: #d8dee9;")
        excel_layout.addWidget(label)

        self.excel_input = QLineEdit("test")
        self.excel_input.textChanged.connect(self.update_sheet_info)
        excel_layout.addWidget(self.excel_input)

        layout.addWidget(excel_card)

        # Sheet info card
        self.sheet_info = SheetInfoWidget()
        layout.addWidget(self.sheet_info)

        layout.addStretch(1)

        return container

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

        final_name, final_barcode = check.checkProduct(
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

