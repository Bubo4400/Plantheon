import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


# ---------------- Shared Nord Style ----------------

NORD_STYLE = """
    QDialog {
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
        padding: 8px 12px;
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
"""


# ---------------- Text Input Dialog ----------------

class TextInputDialog(QDialog):
    def __init__(self, title, label_text, default_text=""):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(360, 160)
        self.setStyleSheet(NORD_STYLE)

        self.value = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setText(default_text)
        layout.addWidget(self.input)

        btn = QPushButton("Confirm")
        btn.clicked.connect(self.confirm)
        layout.addWidget(btn, alignment=Qt.AlignRight)

    def confirm(self):
        text = self.input.text().strip()
        self.value = text if text else None
        self.accept()


# ---------------- Product Confirmation Dialog ----------------

class ProductConfirmDialog(QDialog):
    def __init__(self, product_name, image_path, barcode):
        super().__init__()
        self.setWindowTitle("Product Verification")
        self.setFixedSize(420, 540)
        self.setStyleSheet(NORD_STYLE)

        self.original_name = product_name
        self.original_barcode = barcode

        self.final_name = None
        self.final_barcode = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Product name
        name = QLabel(product_name)
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("font-size: 18px; font-weight: bold; color: #eceff4;")
        layout.addWidget(name)

        # Image container
        img_frame = QFrame()
        img_frame.setStyleSheet("""
            QFrame {
                background-color: #2b3038;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        img_layout = QVBoxLayout(img_frame)

        img = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            img.setPixmap(pixmap.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(img)

        layout.addWidget(img_frame)

        # Question
        question = QLabel("Is this product correct?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet("font-size: 15px; color: #d8dee9;")
        layout.addWidget(question)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        yes = QPushButton("Yes")
        no = QPushButton("No")

        yes.clicked.connect(self.accepted)
        no.clicked.connect(self.rejected)

        btn_layout.addWidget(yes)
        btn_layout.addWidget(no)

        layout.addLayout(btn_layout)

    def accepted(self):
        self.final_name = self.original_name
        self.final_barcode = self.original_barcode
        self.accept()

    def rejected(self):
        # Step 1: barcode correction
        barcode_dialog = TextInputDialog(
            title="Correct Barcode",
            label_text="Enter the correct barcode:",
            default_text=self.original_barcode
        )

        if barcode_dialog.exec_() != QDialog.Accepted or barcode_dialog.value is None:
            self.final_name = None
            self.final_barcode = None
            self.accept()
            return

        new_barcode = barcode_dialog.value

        # Step 2: if unchanged barcode → ask for name
        if new_barcode == self.original_barcode:
            name_dialog = TextInputDialog(
                title="Product Name Required",
                label_text="Barcode unchanged. Enter product name:",
                default_text=self.original_name
            )

            if name_dialog.exec_() != QDialog.Accepted or name_dialog.value is None:
                self.final_name = None
                self.final_barcode = None
            else:
                self.final_name = name_dialog.value
                self.final_barcode = self.original_barcode
        else:
            self.final_name = self.original_name
            self.final_barcode = new_barcode

        self.accept()


# ---------------- Helper Function ----------------

def checkProduct(product_name, image_path, barcode):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    dialog = ProductConfirmDialog(product_name, image_path, barcode)
    dialog.exec_()

    return dialog.final_name, dialog.final_barcode

