import sys, math, xml.etree.ElementTree as ET
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QImage, QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt

class RasterizationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №3")
        self.resize(950, 700)
        self.segments = []
        self.current_pixels = set()
        self.zoom_level = 4.0 

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)

        row1 = QHBoxLayout()
        self.w_entry, self.h_entry = QLineEdit("420"), QLineEdit("260")
        self.w_entry.setFixedWidth(45)
        self.h_entry.setFixedWidth(45)
        
        btn_create = QPushButton("Создать холст")
        btn_create.clicked.connect(self.create_canvas)
        btn_load = QPushButton("Загрузить SVG")
        btn_load.clicked.connect(self.load_svg)
        self.svg_status = QLabel("SVG не загружен")
        self.svg_status.setStyleSheet("color: gray;")
        btn_save = QPushButton("Сохранить PBM")
        btn_save.clicked.connect(self.save_pbm)
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.clear_canvas)

        row1.addWidget(QLabel("Ширина:")); row1.addWidget(self.w_entry)
        row1.addWidget(QLabel("Высота:")); row1.addWidget(self.h_entry)
        row1.addWidget(btn_create); row1.addSpacing(20)
        row1.addWidget(btn_load); row1.addWidget(self.svg_status)
        row1.addStretch()
        row1.addWidget(btn_save); row1.addWidget(btn_clear)

        row2 = QHBoxLayout()
        btn_dda = QPushButton("ЦДА (Красный)")
        btn_dda.clicked.connect(lambda: self.draw_layer("dda"))
        btn_bres_float = QPushButton("Брезенхем (Зеленый)")
        btn_bres_float.clicked.connect(lambda: self.draw_layer("bres_float"))
        btn_bres_int = QPushButton("Целочисленный (Синий)")
        btn_bres_int.clicked.connect(lambda: self.draw_layer("bres_int"))
        btn_builtin = QPushButton("Встроенные (Черный)")
        btn_builtin.clicked.connect(lambda: self.draw_layer("builtin"))
        
        self.compare_label = QLabel("Различия: —")
        self.compare_label.setStyleSheet("font-weight: bold; color: #0055aa;")

        row2.addWidget(QLabel("<b>Наложение слоев:</b>"))
        row2.addWidget(btn_dda); row2.addWidget(btn_bres_float)
        row2.addWidget(btn_bres_int); row2.addWidget(btn_builtin)
        row2.addStretch(); row2.addWidget(self.compare_label)

        row3 = QHBoxLayout()
        btn_zoom_in = QPushButton("Увеличить (+)")
        btn_zoom_in.clicked.connect(lambda: self.change_zoom(1.5))
        btn_zoom_out = QPushButton("Уменьшить (-)")
        btn_zoom_out.clicked.connect(lambda: self.change_zoom(0.6))
        self.zoom_label = QLabel("Масштаб: x4")
        
        row3.addWidget(QLabel("<b>Вид:</b>"))
        row3.addWidget(btn_zoom_in); row3.addWidget(btn_zoom_out)
        row3.addWidget(self.zoom_label)
        row3.addStretch()

        top_layout.addLayout(row1)
        top_layout.addLayout(row2)
        top_layout.addLayout(row3)
        main_layout.addWidget(top_panel)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background-color: #ddd; border: 1px solid #ccc;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, False) # Без размытия
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.view.wheelEvent = self.view_wheel_event # Перехватываем колесико для зума
        
        main_layout.addWidget(self.view, stretch=1)

        self.create_canvas()

    @staticmethod
    def sgn(v): return (v > 0) - (v < 0)
    @staticmethod
    def rhu(v): return int(math.floor(v + 0.5)) if v >= 0 else int(math.ceil(v - 0.5))

    @classmethod
    def dda_line(cls, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L = max(abs(dx), abs(dy))
        if L == 0: return [(x1, y1)]
        sx, sy = dx / L, dy / L
        x, y, pts = float(x1), float(y1), []
        for _ in range(L + 1):
            pts.append((cls.rhu(x), cls.rhu(y))); x += sx; y += sy
        return pts

    @classmethod
    def bres_line(cls, x1, y1, x2, y2, is_int=False):
        if x1 == x2 and y1 == y2: return [(x1, y1)]
        sx, sy = cls.sgn(x2 - x1), cls.sgn(y2 - y1)
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        x, y, swap = x1, y1, dy > dx
        if swap: dx, dy = dy, dx
        err = (2 * dy - dx) if is_int else (dy / dx - 0.5)
        pts = []
        for _ in range(dx + 1):
            pts.append((x, y))
            if err >= 0:
                if swap: x += sx
                else: y += sy
                err -= (2 * dx) if is_int else 1.0
            if swap: y += sy
            else: x += sx
            err += (2 * dy) if is_int else (dy / dx)
        return pts

    def get_size(self):
        try:
            w, h = int(self.w_entry.text()), int(self.h_entry.text())
            if w >= 50 and h >= 50: return w, h
        except ValueError: pass
        QMessageBox.critical(self, "Ошибка", "Ширина/высота должны быть целыми числами (>50).")
        return None, None

    def create_canvas(self):
        w, h = self.get_size()
        if not w: return
        self.qimage = QImage(w, h, QImage.Format.Format_RGB32)
        self.qimage.fill(QColor("white"))
        self.current_pixels = set()
        self.update_view()
        self.setWindowTitle("Лабораторная работа №3")

    def clear_canvas(self):
        if hasattr(self, 'qimage'):
            self.qimage.fill(QColor("white"))
            self.update_view()

    def update_view(self):
        # Перерисовываем сцену
        self.scene.clear()
        pixmap = QPixmap.fromImage(self.qimage)
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.apply_zoom()

    def change_zoom(self, factor):
        self.zoom_level *= factor
        if self.zoom_level < 0.5: self.zoom_level = 0.5
        if self.zoom_level > 20.0: self.zoom_level = 20.0
        self.apply_zoom()

    def apply_zoom(self):
        transform = self.view.transform()
        transform.reset()
        transform.scale(self.zoom_level, self.zoom_level)
        self.view.setTransform(transform)
        self.zoom_label.setText(f"Масштаб: x{self.zoom_level:.1f}")

    def view_wheel_event(self, event):
        if event.angleDelta().y() > 0:
            self.change_zoom(1.15)
        else:
            self.change_zoom(0.85)

    @staticmethod
    def _name(t): return t.split("}")[-1]
    
    @staticmethod
    def _num(v):
        v = str(v).strip()
        for s in ("px", "pt", "cm", "mm", "in"):
            if v.endswith(s): v = v[:-len(s)]; break
        return float(v)

    @classmethod
    def parse_svg(cls, filename):
        segs = []
        for el in ET.parse(filename).getroot().iter():
            tag = cls._name(el.tag)
            if tag == "line":
                try:
                    c = [cls._num(el.attrib[k]) for k in ("x1", "y1", "x2", "y2")]
                    segs.append(((cls.rhu(c[0]), cls.rhu(c[1])), (cls.rhu(c[2]), cls.rhu(c[3]))))
                except (KeyError, ValueError): continue
            elif tag in ("polyline", "polygon") and "points" in el.attrib:
                vals = [cls._num(v) for v in el.attrib["points"].replace(",", " ").split()]
                pts = [(cls.rhu(vals[i]), cls.rhu(vals[i+1])) for i in range(0, len(vals)-1, 2)]
                segs.extend([(pts[i], pts[i+1]) for i in range(len(pts)-1)])
                if tag == "polygon" and len(pts) > 2: segs.append((pts[-1], pts[0]))
        if not segs: raise ValueError("В SVG не найдены линии.")
        return segs

    def load_svg(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Открыть SVG", "", "SVG (*.svg);;Все файлы (*.*)")
        if not fn: return
        try:
            self.segments = self.parse_svg(fn)
            self.svg_status.setText(f"Загружено: {len(self.segments)} лин.")
            self.svg_status.setStyleSheet("color: green;")
            
            dda = self.get_pts(self.dda_line)
            bf = self.get_pts(lambda *a: self.bres_line(*a, False))
            bi = self.get_pts(lambda *a: self.bres_line(*a, True))
            diff_text = f"<b>Различия:</b> ЦДА/Брез — {len(dda ^ bf)}, Брез/целочисл — {len(bf ^ bi)}, ЦДА/целочисл — {len(dda ^ bi)}."
            self.compare_label.setText(diff_text)
            
            self.create_canvas() 
            self.draw_layer("dda") 
        except Exception as e: QMessageBox.critical(self, "Ошибка SVG", str(e))

    def get_pts(self, algo):
        pts = set()
        for p1, p2 in self.segments: pts.update(algo(*p1, *p2))
        return pts

    def draw_layer(self, method):
        if not self.segments: return QMessageBox.warning(self, "Нет SVG", "Сначала загрузите SVG.")
        if not hasattr(self, 'qimage'): return

        w, h = self.qimage.width(), self.qimage.height()
        painter = QPainter(self.qimage)
        
        if method == "dda":
            painter.setPen(QColor(255, 0, 0))
            pts = self.get_pts(self.dda_line)
        elif method == "bres_float":
            painter.setPen(QColor(0, 180, 0))
            pts = self.get_pts(lambda *a: self.bres_line(*a, False))
        elif method == "bres_int":
            painter.setPen(QColor(0, 0, 255))
            pts = self.get_pts(lambda *a: self.bres_line(*a, True))
        elif method == "builtin":
            painter.setPen(QColor(0, 0, 0))
            for p1, p2 in self.segments:
                painter.drawLine(p1[0], p1[1], p2[0], p2[1])
            pts = self.get_pts(lambda *a: self.bres_line(*a, True))
        else:
            return

        if method != "builtin":
            for x, y in pts:
                if 0 <= x < w and 0 <= y < h: painter.drawPoint(x, y)
            
        painter.end()
        self.current_pixels = pts
        self.update_view()

    def save_pbm(self):
        if not self.current_pixels: 
            return QMessageBox.warning(self, "Нет результата", "Сначала нарисуйте линии.")
        
        fn, _ = QFileDialog.getSaveFileName(self, "Сохранить PBM", "", "Portable Bitmap (*.pbm)")
        if not fn: return
        try:
            w, h = self.qimage.width(), self.qimage.height()
            with open(fn, "w", encoding="ascii") as f:
                f.write(f"P1\n# Lab 3\n{w} {h}\n")
                for y in range(h):
                    f.write(" ".join("1" if (x, y) in self.current_pixels else "0" for x in range(w)) + "\n")
            QMessageBox.information(self, "Готово", "Сохранено в PBM P1.")
        except Exception as e: QMessageBox.critical(self, "Ошибка", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RasterizationApp()
    window.show()
    sys.exit(app.exec())