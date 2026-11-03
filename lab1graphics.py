import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

class ImageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №1")
        self.resize(900, 650)

        self.image: QImage | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()

        self.btn_open = QPushButton("Открыть")
        self.btn_open.setFixedWidth(140)
        self.btn_open.clicked.connect(self.open_image)

        self.btn_process = QPushButton("Обработать")
        self.btn_process.setFixedWidth(140)
        self.btn_process.clicked.connect(self.process_image)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setFixedWidth(140)
        self.btn_save.clicked.connect(self.save_image)

        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_process)
        toolbar.addWidget(self.btn_save)
        toolbar.addStretch(1)

        root_layout.addLayout(toolbar)

        self.canvas = QLabel("Откройте изображение")
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setStyleSheet("background: white; color: gray; font-size: 16px;")
        self.canvas.setMinimumSize(1, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        root_layout.addWidget(scroll, 1)

    def open_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть изображение",
            "",
            "Изображения (*.png *.gif *.ppm *.pgm *.bmp *.jpg *.jpeg);;Все файлы (*.*)",
        )
        if not filename:
            return

        image = QImage(filename)
        if image.isNull():
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось открыть изображение.\n\n"
                "Возможно, формат не поддерживается.",
            )
            return

        self.image = image.convertToFormat(QImage.Format.Format_RGB32)
        self.redraw()

    def process_image(self):
        if self.image is None:
            QMessageBox.warning(self, "Нет изображения", "Сначала откройте изображение.")
            return

        width = self.image.width()
        height = self.image.height()

        self.image.setPixelColor(0, 0, QColor(0, 127, 64))
        self.image.setPixelColor(width // 2, height // 2, QColor(127, 0, 64))
        self.image.setPixelColor(width // 2, height - 1, QColor(191, 191, 191))

        self.redraw()

    def save_image(self):
        if self.image is None:
            QMessageBox.warning(self, "Нет изображения", "Сначала откройте изображение.")
            return

        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            "",
            "PNG (*.png);;PBM (*.pbm);;PPM (*.ppm)",
        )
        if not filename:
            return

        ext = Path(filename).suffix.lower()

        try:
            if ext == ".png":
                ok = self.image.save(filename, "PNG")
                if not ok:
                    raise OSError("QImage.save вернул False")
            else:
                self._save_pbm(filename)

            QMessageBox.information(
                self, "Готово", f"Изображение успешно сохранено ({ext})."
            )
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Ошибка сохранения", str(error))

    def _save_pbm(self, filename: str):
        width = self.image.width()
        height = self.image.height()

        with open(filename, "w", encoding="ascii") as file:
            file.write("P1\n")
            file.write(f"{width} {height}\n")

            for y in range(height):
                row = []
                for x in range(width):
                    color = self.image.pixelColor(x, y)
                    brightness = (
                        0.299 * color.red()
                        + 0.587 * color.green()
                        + 0.114 * color.blue()
                    )
                    row.append("1" if brightness < 128 else "0")
                file.write(" ".join(row) + "\n")

    def redraw(self):
        if self.image is None:
            self.canvas.setText("Откройте изображение")
            self.canvas.setPixmap(QPixmap())
            return

        self.canvas.setText("")
        self.canvas.setPixmap(QPixmap.fromImage(self.image))


def main():
    app = QApplication(sys.argv)
    window = ImageApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()