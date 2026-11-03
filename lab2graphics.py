import sys
import math

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QPolygon
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

class ImageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №2")
        self.resize(1120, 650)

        self.source: QImage | None = None
        self.result: QImage | None = None
        self.outline = None  # (sx0, sy0, size)

        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)

        row = QHBoxLayout()
        self.w_edit = QLineEdit("300")
        self.h_edit = QLineEdit("220")
        self.s_edit = QLineEdit("120")
        for label, edit in [("Ширина:", self.w_edit), ("Высота:", self.h_edit),
                            ("Размер:", self.s_edit)]:
            row.addWidget(QLabel(label))
            edit.setFixedWidth(60)
            row.addWidget(edit)
        row.addStretch(1)
        lay.addLayout(row)

        btns = QHBoxLayout()
        for text, slot in [("Создать", self.create), ("Открыть", self.open),
                           ("Перенести", self.copy), ("Координаты", self.axes),
                           ("График", self.graph), ("Сохранить PBM", self.save)]:
            b = QPushButton(text)
            b.setFixedWidth(140)
            b.clicked.connect(slot)
            btns.addWidget(b)
        btns.addStretch(1)
        lay.addLayout(btns)

        body = QHBoxLayout()
        self.src_label = self._make_canvas("Откройте исходное изображение")
        self.res_label = self._make_canvas("Создайте новое изображение")
        for title, lbl in [("Исходное", self.src_label), ("Новое", self.res_label)]:
            col = QVBoxLayout()
            col.addWidget(QLabel(title), alignment=Qt.AlignmentFlag.AlignCenter)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(lbl)
            col.addWidget(scroll, 1)
            body.addLayout(col, 1)
        lay.addLayout(body, 1)

    @staticmethod
    def _make_canvas(text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("background: gray; color: gray;")
        label.setMinimumSize(1, 1)
        return label

    def create(self):
        try:
            w, h = int(self.w_edit.text()), int(self.h_edit.text())
        except ValueError:
            return QMessageBox.critical(self, "Ошибка", "Ширина и высота — целые числа.")
        if w < 100 or h < 100:
            return QMessageBox.critical(self, "Ошибка", "Слишком маленькое изображение.")
        self.result = QImage(w, h, QImage.Format.Format_RGB32)
        self.result.fill(QColor(255, 255, 255))
        self._show_result()

    def open(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Открыть", "",
            "Изображения (*.png *.gif *.ppm *.pgm *.bmp *.jpg);;Все файлы (*.*)")
        if not fn:
            return
        img = QImage(fn)
        if img.isNull():
            return QMessageBox.critical(self, "Ошибка", "Не удалось открыть.")
        self.source = img.convertToFormat(QImage.Format.Format_RGB32)
        self.outline = None
        self._show_source()

    def copy(self):
        if self.result is None:
            return QMessageBox.warning(self, "Нет изображения", "Сначала создайте новое.")
        if self.source is None:
            return QMessageBox.warning(self, "Нет изображения", "Сначала откройте исходное.")

        try:
            size = int(self.s_edit.text())
        except ValueError:
            return QMessageBox.warning(self, "Ошибка", "Размер — целое число.")
        sw, sh = self.source.width(), self.source.height()
        size = min(size, sw, sh)
        if size < 10:
            return QMessageBox.warning(self, "Ошибка", "Слишком маленький треугольник.")

        sx0, sy0 = sw - size, sh - size            # правый нижний угол исходника
        rw, rh = self.result.width(), self.result.height()
        dx0, dy0 = rw // 2 - size // 2, rh - size  # низ по центру

        # равнобедренный прямоугольный, прямой угол — левый нижний
        for ly in range(size):
            for lx in range(size):
                if ly >= lx:                        # внутри треугольника
                    x, y = dx0 + lx, dy0 + ly
                    if 0 <= x < rw and 0 <= y < rh:
                        self.result.setPixelColor(x, y,
                            self.source.pixelColor(sx0 + lx, sy0 + ly))

        self.outline = (sx0, sy0, size)
        self._show_source()
        self._show_result()

    def axes(self):
        if self.result is None:
            return QMessageBox.warning(self, "Нет изображения", "Сначала создайте новое.")
        w, h = self.result.width(), self.result.height()
        x0, y0 = w // 2, h // 2

        p = QPainter(self.result)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawLine(10, h - 10, 10, 10)                    # OY
        p.drawLine(10, y0, w - 10, y0)                    # OX
        p.drawLine(10, 10, 5, 20)                    # стрелка Y
        p.drawLine(10, 10, 15, 20)
        p.drawLine(w - 10, y0, w - 20, y0 - 5)            # стрелка X
        p.drawLine(w - 10, y0, w - 20, y0 + 5)
        for x in range(30, w - 20, 20):              # засечки X
            p.drawLine(x, y0 - 3, x, y0 + 3)
        for x in range(30, 20, -20):
            p.drawLine(x, y0 - 3, x, y0 + 3)
        for y in range(y0 + 20, h - 20, 20):              # засечки Y
            p.drawLine(7, y, 13, y)
        for y in range(y0 - 20, 20, -20):
            p.drawLine(7, y, 13, y)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawText(2, y0 + 18, "0")
        p.drawText(w - 18, y0 - 6, "x")
        p.drawText(16, 14, "y")
        p.end()
        self._show_result()

    def graph(self):
        if self.result is None:
            return QMessageBox.warning(self, "Нет изображения", "Сначала создайте новое.")
        w, h = self.result.width(), self.result.height()
        x0, y0 = w // 2, h // 2
        x_scale = max((w - 20 - x0) / 10.0, 1.0)  # ~10 радиан вправо
        y_scale = max(y0 - 20, 1)

        p = QPainter(self.result)
        p.setPen(QPen(QColor(0, 0, 204), 1))
        prev = None
        for px in range(10, w - 10):
            x = (px - x0) / x_scale
            y = math.sin(x) ** 2
            py = y0 - round(y * y_scale)
            if 0 <= py < h:
                if prev:
                    p.drawLine(prev[0], prev[1], px, py)
                prev = (px, py)
            else:
                prev = None

        p.drawText(w-70, 12, "y = sin²(x)")
        p.end()
        self._show_result()

    def save(self):
        if self.result is None:
            return QMessageBox.warning(self, "Нет изображения", "Сначала создайте новое.")
        fn, _ = QFileDialog.getSaveFileName(self, "Сохранить", "", "PBM (*.pbm)")
        if not fn:
            return
        try:
            with open(fn, "w", encoding="ascii") as f:
                f.write(f"P1\n{self.result.width()} {self.result.height()}\n")
                for y in range(self.result.height()):
                    row = []
                    for x in range(self.result.width()):
                        c = self.result.pixelColor(x, y)
                        b = 0.299*c.red() + 0.587*c.green() + 0.114*c.blue()
                        row.append("1" if b < 128 else "0")
                    f.write(" ".join(row) + "\n")
            QMessageBox.information(self, "Готово", "Сохранено.")
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _show_source(self):
        if self.source is None:
            self.src_label.setText("Откройте исходное изображение")
            self.src_label.setPixmap(QPixmap())
            return
        pm = QPixmap.fromImage(self.source)
        if self.outline:
            sx0, sy0, size = self.outline
            p = QPainter(pm)
            p.setPen(QPen(QColor(255, 0, 0), 2))
            p.drawPolygon(QPolygon([
                QPoint(sx0, sy0 + size - 1),
                QPoint(sx0, sy0),
                QPoint(sx0 + size - 1, sy0 + size - 1),
            ]))
            p.end()
        self.src_label.setText("")
        self.src_label.setPixmap(pm)

    def _show_result(self):
        if self.result is None:
            self.res_label.setText("Создайте новое изображение")
            self.res_label.setPixmap(QPixmap())
            return
        self.res_label.setText("")
        self.res_label.setPixmap(QPixmap.fromImage(self.result))


def main():
    app = QApplication(sys.argv)
    w = ImageApp()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()