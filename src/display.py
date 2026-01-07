import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class TextInputDialog(QDialog):
    def __init__(self, title, label_text, default_text=""):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(320, 140)

        self.value = None

        layout = QVBoxLayout(self)

        label = QLabel(label_text)
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setText(default_text)
        layout.addWidget(self.input)

        btn = QPushButton("Confirm")
        btn.clicked.connect(self.confirm)
        layout.addWidget(btn)

    def confirm(self):
        text = self.input.text().strip()
        self.value = text if text else None
        self.accept()


class ProductConfirmDialog(QDialog):
    def __init__(self, product_name, image_path, barcode):
        super().__init__()
        self.setWindowTitle("Product Verification")
        self.setFixedSize(400, 500)

        self.original_name = product_name
        self.original_barcode = barcode

        self.final_name = None
        self.final_barcode = None

        layout = QVBoxLayout(self)

        name = QLabel(product_name)
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(name)

        img = QLabel()
        pixmap = QPixmap(image_path)
        img.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
        img.setAlignment(Qt.AlignCenter)
        layout.addWidget(img)

        question = QLabel("Is this product correct?")
        question.setAlignment(Qt.AlignCenter)
        layout.addWidget(question)

        btn_layout = QHBoxLayout()

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


def check_product(product_name, image_path, barcode):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    dialog = ProductConfirmDialog(product_name, image_path, barcode)
    dialog.exec_()

    return dialog.final_name, dialog.final_barcode
