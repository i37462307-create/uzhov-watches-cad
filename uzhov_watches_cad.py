#!/usr/bin/env python3
"""
Uzhov Watches CAD — Parametric 3D Watch Model Generator
Generates FreeCAD .FCStd files from GUI parameters
"""

import sys
import os
import json
import math
import struct
import zlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QFileDialog, QGroupBox, QScrollArea, QSplitter,
    QStatusBar, QFrame, QSizePolicy, QToolBar, QAction, QActionGroup,
    QMessageBox, QRadioButton, QButtonGroup, QGridLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QLinearGradient,
    QRadialGradient, QImage, QVector3D, QMatrix4x4, QPainterPath,
    QFontDatabase, QIcon
)
import math

# ─────────────────────────── COLOUR PALETTE ────────────────────────────
BG        = "#0d0f14"
BG2       = "#13161e"
BG3       = "#1a1e2a"
PANEL     = "#1e2230"
BORDER    = "#2a3045"
GOLD      = "#c9a84c"
GOLD2     = "#e8c56a"
GOLD_DIM  = "#7a6230"
TEXT      = "#d8dae8"
TEXT_DIM  = "#6a7090"
ACCENT    = "#4a7fc1"
RED       = "#c14a4a"
GREEN     = "#4ac17a"

STYLE = f"""
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: 'Courier New', monospace;
    font-size: 12px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {BG2};
}}
QTabBar::tab {{
    background: {BG3};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 8px 18px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QTabBar::tab:selected {{
    background: {PANEL};
    color: {GOLD};
    border-bottom: 2px solid {GOLD};
}}
QTabBar::tab:hover {{
    color: {GOLD2};
}}
QLineEdit {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 3px;
    color: {TEXT};
    padding: 4px 8px;
    selection-background-color: {GOLD_DIM};
}}
QLineEdit:focus {{
    border: 1px solid {GOLD_DIM};
}}
QComboBox {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 3px;
    color: {TEXT};
    padding: 4px 8px;
}}
QComboBox QAbstractItemView {{
    background: {BG2};
    border: 1px solid {BORDER};
    color: {TEXT};
    selection-background-color: {GOLD_DIM};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QPushButton {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 3px;
    color: {TEXT};
    padding: 6px 14px;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    border-color: {GOLD_DIM};
    color: {GOLD};
}}
QPushButton:pressed {{
    background: {PANEL};
}}
QPushButton#gold_btn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7a5820, stop:1 #a87830);
    border: 1px solid {GOLD};
    color: {GOLD2};
    font-weight: bold;
    letter-spacing: 2px;
}}
QPushButton#gold_btn:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #9a7030, stop:1 #c89040);
}}
QPushButton#mode_btn {{
    background: {BG3};
    border: 1px solid {BORDER};
    color: {TEXT_DIM};
    padding: 5px 20px;
    border-radius: 2px;
}}
QPushButton#mode_btn[active="true"] {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2a3045, stop:1 #1e2230);
    border: 1px solid {GOLD_DIM};
    color: {GOLD};
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    color: {GOLD_DIM};
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
    font-size: 10px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}
QLabel {{
    color: {TEXT_DIM};
    font-size: 11px;
}}
QLabel#section_label {{
    color: {GOLD_DIM};
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {BG};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {GOLD_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QStatusBar {{
    background: {BG2};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    font-size: 11px;
    font-family: 'Courier New', monospace;
}}
QSplitter::handle {{
    background: {BORDER};
    width: 1px;
}}
QFrame#divider {{
    color: {BORDER};
    max-height: 1px;
    background: {BORDER};
}}
"""

# ──────────────────────────── HELPERS ──────────────────────────────────

def field(label, default="", unit="mm"):
    """Return (QLabel, QLineEdit) pair."""
    lbl = QLabel(f"{label}:")
    edit = QLineEdit(str(default))
    edit.setFixedWidth(90)
    return lbl, edit

def labeled_combo(label, options):
    lbl = QLabel(f"{label}:")
    cb = QComboBox()
    cb.addItems(options)
    return lbl, cb

def section_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("section_label")
    return lbl

def image_upload_button(label="Upload Image"):
    btn = QPushButton(f"📂  {label}")
    btn._path = None
    btn._pixmap = None
    return btn

def make_form_row(lbl, widget, unit_lbl=None):
    row = QHBoxLayout()
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(widget)
    if unit_lbl:
        u = QLabel(unit_lbl)
        u.setFixedWidth(24)
        row.addWidget(u)
    return row

# ──────────────────────────── 3D VIEWPORT ──────────────────────────────

class Viewport3D(QWidget):
    """Software 3D renderer — draws watch parts as projected geometry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        self._yaw   = 30.0
        self._pitch = -25.0
        self._zoom  = 1.0
        self._last  = None
        self._params = {}
        self._mode   = "assembly"    # assembly | exploded | parts
        self._anim_t = 0.0
        self._anim_dir = 0           # 0=static, 1=exploding, -1=assembling

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    # ── Public API ──────────────────────────────────────────────────
    def set_params(self, params: dict):
        self._params = params
        self.update()

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == "assembly":
            self._anim_dir = -1
        elif mode == "exploded":
            self._anim_dir = 1
        elif mode == "parts":
            self._anim_t = 1.0
            self._anim_dir = 0
        self.update()

    # ── Animation ───────────────────────────────────────────────────
    def _tick(self):
        if self._anim_dir != 0:
            speed = 0.04
            self._anim_t = max(0.0, min(1.0, self._anim_t + self._anim_dir * speed))
            if self._anim_t in (0.0, 1.0):
                self._anim_dir = 0
            self.update()

    # ── Mouse interaction ────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._last = e.pos()

    def mouseMoveEvent(self, e):
        if self._last and e.buttons() & Qt.LeftButton:
            dx = e.x() - self._last.x()
            dy = e.y() - self._last.y()
            self._yaw   += dx * 0.5
            self._pitch += dy * 0.5
            self._pitch  = max(-89, min(89, self._pitch))
            self._last   = e.pos()
            self.update()

    def mouseReleaseEvent(self, e):
        self._last = None

    def wheelEvent(self, e):
        delta = e.angleDelta().y() / 120
        self._zoom *= (1.1 ** delta)
        self._zoom  = max(0.2, min(5.0, self._zoom))
        self.update()

    # ── Projection helpers ───────────────────────────────────────────
    def _project(self, x, y, z, cx, cy, scale):
        yaw   = math.radians(self._yaw)
        pitch = math.radians(self._pitch)

        # Rotate Y (yaw)
        x1 =  x * math.cos(yaw) + z * math.sin(yaw)
        z1 = -x * math.sin(yaw) + z * math.cos(yaw)
        # Rotate X (pitch)
        y2 = y * math.cos(pitch) - z1 * math.sin(pitch)
        z2 = y * math.sin(pitch) + z1 * math.cos(pitch)

        # Perspective
        fov = 600
        factor = fov / (fov + z2 * scale)
        sx = cx + x1 * scale * factor
        sy = cy - y2 * scale * factor
        return sx, sy, z2

    def _poly(self, pts3d, cx, cy, scale):
        return [self._project(x, y, z, cx, cy, scale)[:2] for x, y, z in pts3d]

    # ── Draw shapes ──────────────────────────────────────────────────
    def _draw_circle_face(self, painter, cx, cy, scale, r, z_offset, color, segments=48):
        pts = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            pts.append((r * math.cos(a), r * math.sin(a), z_offset))
        proj = self._poly(pts, cx, cy, scale)
        path = QPainterPath()
        path.moveTo(*proj[0])
        for p in proj[1:]:
            path.lineTo(*p)
        path.closeSubpath()
        painter.fillPath(path, QBrush(QColor(color)))
        painter.drawPath(path)

    def _draw_cylinder(self, painter, cx, cy, scale,
                        r, z_bottom, z_top, fill_color, edge_color, segments=48):
        step = 2 * math.pi / segments
        angles = [step * i for i in range(segments)]

        # Side faces — draw visible ones only (dot product check)
        for i in range(segments):
            a0 = angles[i]
            a1 = angles[(i + 1) % segments]
            mid_a = (a0 + a1) / 2
            # Normal dot view — simplified
            nx = math.cos(mid_a)
            nz = math.sin(mid_a)
            yaw = math.radians(self._yaw)
            vx = math.sin(yaw)
            vz = math.cos(yaw)
            dot = nx * vx + nz * vz
            if dot < 0:
                continue
            shade = max(0.3, min(1.0, dot))
            c = QColor(fill_color)
            c = QColor(
                int(c.red()   * shade),
                int(c.green() * shade),
                int(c.blue()  * shade),
            )
            quad = [
                (r * math.cos(a0), r * math.sin(a0), z_bottom),
                (r * math.cos(a1), r * math.sin(a1), z_bottom),
                (r * math.cos(a1), r * math.sin(a1), z_top),
                (r * math.cos(a0), r * math.sin(a0), z_top),
            ]
            proj = self._poly(quad, cx, cy, scale)
            path = QPainterPath()
            path.moveTo(*proj[0])
            for p in proj[1:]:
                path.lineTo(*p)
            path.closeSubpath()
            painter.setPen(QPen(QColor(edge_color), 0.5))
            painter.fillPath(path, QBrush(c))
            painter.drawPath(path)

    def _draw_ring(self, painter, cx, cy, scale,
                   r_out, r_in, z_bottom, z_top, fill_color, segments=48):
        """Draw a hollow cylinder (ring/tube)."""
        self._draw_cylinder(painter, cx, cy, scale, r_out, z_bottom, z_top, fill_color, BORDER, segments)
        # Inner cylinder drawn darker
        c = QColor(fill_color)
        dark = QColor(c.red()//3, c.green()//3, c.blue()//3)
        self._draw_cylinder(painter, cx, cy, scale, r_in, z_bottom, z_top,
                            dark.name(), BORDER, segments)

    # ── Main paint ───────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Background gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#0a0c12"))
        grad.setColorAt(1, QColor("#080a0e"))
        painter.fillRect(0, 0, w, h, grad)

        # Grid
        painter.setPen(QPen(QColor("#1a1e2a"), 1))
        grid_step = 40
        for gx in range(0, w, grid_step):
            painter.drawLine(gx, 0, gx, h)
        for gy in range(0, h, grid_step):
            painter.drawLine(0, gy, w, gy)

        p = self._params
        cx, cy = w // 2, h // 2
        scale = 3.5 * self._zoom

        t = self._anim_t  # 0=assembled, 1=exploded

        # ── Extract params with defaults ────────────────────────
        case_r  = float(p.get("case_radius", 20))
        case_h  = float(p.get("case_h", 12))
        dial_r  = float(p.get("dial_radius", case_r - 1.5))
        dial_h  = float(p.get("dial_h", 2))
        back_r  = float(p.get("backplate_radius", case_r))
        back_h  = float(p.get("back_h", 2))
        seat_r  = float(p.get("dial_seat_radius", case_r - 1.5))
        lug_l   = float(p.get("lug_length", 8))
        mech_r  = float(p.get("mech_seat_radius", 14))
        mech_d  = float(p.get("mech_seat_depth", 4))

        explode_gap = 10 * t

        # Draw order: back → case → dial → hands
        # Z layout: back=0, case_bottom=back_h, dial top = back_h + case_h - dial_h
        z_back_bot = 0
        z_back_top = back_h

        z_case_bot = z_back_top + explode_gap
        z_case_top = z_case_bot + case_h

        z_dial_bot = z_case_top - dial_h - 0.5 + explode_gap * 1.5
        z_dial_top = z_dial_bot + dial_h

        z_glass_bot = z_dial_top + explode_gap * 0.5
        z_glass_top = z_glass_bot + 1.5

        z_hands   = z_glass_bot + explode_gap * 0.2

        # Offset for Parts mode — separate components horizontally
        if self._mode == "parts":
            offsets = [
                (-case_r * 2.8, 0),   # backplate
                (0, 0),               # case
                (case_r * 2.8, 0),    # dial
            ]
        else:
            offsets = [(0, 0), (0, 0), (0, 0)]

        painter.setRenderHint(QPainter.Antialiasing)

        # ── 1. Backplate ────────────────────────────────────────
        ox, oy = offsets[0]
        self._draw_cylinder(painter, cx + int(ox*scale*0.5), cy + int(oy*scale*0.5),
                            scale, back_r, z_back_bot, z_back_top,
                            "#4a4035", "#2a2520")
        # Top face
        self._draw_circle_face(painter, cx + int(ox*scale*0.5), cy + int(oy*scale*0.5),
                               scale, back_r, z_back_top, "#5a5040")

        # ── 2. Case ─────────────────────────────────────────────
        ox, oy = offsets[1]
        bcx = cx + int(ox * scale * 0.5)
        bcy = cy + int(oy * scale * 0.5)
        # Outer case wall
        self._draw_cylinder(painter, bcx, bcy, scale,
                            case_r, z_case_bot, z_case_top, "#b8a070", "#6a5830")
        # Inner cavity (darker)
        inner_r = seat_r
        self._draw_cylinder(painter, bcx, bcy, scale,
                            inner_r, z_case_bot, z_case_top, "#3a3028", "#1a1510")
        # Bottom face of case
        self._draw_circle_face(painter, bcx, bcy, scale, case_r, z_case_bot, "#7a6840")
        # Top rim face
        self._draw_circle_face(painter, bcx, bcy, scale, case_r, z_case_top, "#c8b080")
        self._draw_circle_face(painter, bcx, bcy, scale, inner_r, z_case_top, "#2a2018")

        # Lugs — simple rectangular approximation
        lug_w = float(p.get("strap_width", 20)) / 2
        lug_h_3d = case_h * 0.7
        lug_z_mid = z_case_bot + lug_h_3d / 2
        for sign in (+1, -1):
            lug_pts_bot = [
                (sign * (case_r),       -lug_w/2,  z_case_bot + case_h*0.15),
                (sign * (case_r+lug_l), -lug_w/2,  z_case_bot + case_h*0.15),
                (sign * (case_r+lug_l),  lug_w/2,  z_case_bot + case_h*0.15),
                (sign * (case_r),        lug_w/2,  z_case_bot + case_h*0.15),
            ]
            lug_pts_top = [
                (sign * (case_r),       -lug_w/2,  z_case_bot + lug_h_3d),
                (sign * (case_r+lug_l), -lug_w/2,  z_case_bot + lug_h_3d),
                (sign * (case_r+lug_l),  lug_w/2,  z_case_bot + lug_h_3d),
                (sign * (case_r),        lug_w/2,  z_case_bot + lug_h_3d),
            ]
            # Top face of lug
            proj = self._poly(lug_pts_top, bcx, bcy, scale)
            path = QPainterPath()
            path.moveTo(*proj[0])
            for pp in proj[1:]: path.lineTo(*pp)
            path.closeSubpath()
            painter.setPen(QPen(QColor("#6a5830"), 0.5))
            painter.fillPath(path, QBrush(QColor("#c8b080")))
            painter.drawPath(path)
            # Side face
            side = [lug_pts_bot[0], lug_pts_bot[1],
                    lug_pts_top[1], lug_pts_top[0]]
            proj2 = self._poly(side, bcx, bcy, scale)
            path2 = QPainterPath()
            path2.moveTo(*proj2[0])
            for pp in proj2[1:]: path2.lineTo(*pp)
            path2.closeSubpath()
            painter.setPen(QPen(QColor("#6a5830"), 0.5))
            painter.fillPath(path2, QBrush(QColor("#a89060")))
            painter.drawPath(path2)

        # Crown (winding crown)
        crown_l = float(p.get("crown_length", 5))
        crown_w = float(p.get("crown_width", 3.5))
        self._draw_cylinder(painter, bcx, bcy, scale,
                            crown_w / 2,
                            z_case_bot + case_h * 0.35,
                            z_case_bot + case_h * 0.35 + crown_l,
                            "#9a8050", "#4a3820")

        # ── 3. Dial ─────────────────────────────────────────────
        ox, oy = offsets[2]
        dcx = cx + int(ox * scale * 0.5)
        dcy = cy + int(oy * scale * 0.5)
        self._draw_cylinder(painter, dcx, dcy, scale,
                            dial_r, z_dial_bot, z_dial_top, "#f0ead8", "#d0c8a8")
        self._draw_circle_face(painter, dcx, dcy, scale, dial_r, z_dial_top, "#f8f4e8")
        # Hour markers on dial face
        for mk in range(12):
            a = 2 * math.pi * mk / 12
            mr = dial_r * 0.85
            mx = mr * math.cos(a)
            my = mr * math.sin(a)
            dot_pts = []
            for di in range(8):
                da = 2*math.pi*di/8
                dot_pts.append((mx + 0.6*math.cos(da), my + 0.6*math.sin(da), z_dial_top + 0.1))
            proj = self._poly(dot_pts, dcx, dcy, scale)
            path = QPainterPath()
            path.moveTo(*proj[0])
            for pp in proj[1:]: path.lineTo(*pp)
            path.closeSubpath()
            c = QColor("#c8a040") if mk % 3 == 0 else QColor("#a08030")
            painter.fillPath(path, QBrush(c))

        # Hands
        z_h = z_hands if self._mode != "parts" else z_dial_top + 0.5
        for hand_idx, (hand_l, hand_w, hand_color) in enumerate([
            (dial_r*0.55, 1.8, "#202020"),  # hour
            (dial_r*0.78, 1.2, "#282828"),  # minute
            (dial_r*0.82, 0.6, "#c04030"),  # second
        ]):
            angle = math.radians(30 * hand_idx - 90 + self._anim_t * 45)
            hx = hand_l * math.cos(angle)
            hy = hand_l * math.sin(angle)
            hand_pts = [
                (-hand_w/2 * math.sin(angle), hand_w/2 * math.cos(angle), z_h),
                ( hand_w/2 * math.sin(angle), -hand_w/2 * math.cos(angle), z_h),
                (hx + hand_w/2*math.sin(angle), hy - hand_w/2*math.cos(angle), z_h),
                (hx - hand_w/2*math.sin(angle), hy + hand_w/2*math.cos(angle), z_h),
            ]
            proj = self._poly(hand_pts, dcx, dcy, scale)
            path = QPainterPath()
            path.moveTo(*proj[0])
            for pp in proj[1:]: path.lineTo(*pp)
            path.closeSubpath()
            painter.fillPath(path, QBrush(QColor(hand_color)))

        # Glass (transparent blue tint)
        glass_color = QColor(160, 200, 240, 35)
        painter.setPen(QPen(QColor(120, 160, 200, 60), 0.5))
        self._draw_circle_face(painter, dcx, dcy, scale, seat_r, z_glass_top, "#A0C8F0")
        # Tinted glass overlay
        pts = []
        for i in range(48):
            a = 2*math.pi*i/48
            pts.append((seat_r*math.cos(a), seat_r*math.sin(a), z_glass_top))
        proj = self._poly(pts, dcx, dcy, scale)
        path = QPainterPath()
        path.moveTo(*proj[0])
        for pp in proj[1:]: path.lineTo(*pp)
        path.closeSubpath()
        painter.fillPath(path, QBrush(glass_color))

        # ── Crosshair / info overlay ─────────────────────────────
        painter.setPen(QPen(QColor(GOLD_DIM), 1))
        painter.setFont(QFont("Courier New", 9))
        painter.drawText(10, h - 10,
            f"YAW {self._yaw:+.0f}°  PITCH {self._pitch:+.0f}°  ZOOM {self._zoom:.2f}×  "
            f"MODE: {self._mode.upper()}")

        # Axis indicator
        ax, ay = 50, h - 50
        axis_len = 25
        for ax_dir, col, lbl in [
            ((1,0,0), "#c04040", "X"),
            ((0,1,0), "#40c040", "Y"),
            ((0,0,1), "#4040c0", "Z"),
        ]:
            ex, ey, _ = self._project(
                ax_dir[0]*axis_len, ax_dir[1]*axis_len, ax_dir[2]*axis_len,
                ax, ay, 1)
            painter.setPen(QPen(QColor(col), 1.5))
            painter.drawLine(int(ax), int(ay), int(ex), int(ey))
            painter.setFont(QFont("Courier New", 8))
            painter.drawText(int(ex)+2, int(ey)+2, lbl)

        painter.end()


# ──────────────────────────── TABS ─────────────────────────────────────

def _scrolled(widget):
    sa = QScrollArea()
    sa.setWidget(widget)
    sa.setWidgetResizable(True)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return sa

def _vbox(*widgets, spacing=6, margin=16):
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setSpacing(spacing)
    lay.setContentsMargins(margin, margin, margin, margin)
    for ww in widgets:
        if isinstance(ww, QLayout):
            lay.addLayout(ww)
        else:
            lay.addWidget(ww)
    lay.addStretch()
    return w

def _hrow(lbl_widget, edit_widget, unit="mm"):
    row = QHBoxLayout()
    row.addWidget(lbl_widget)
    row.addStretch()
    row.addWidget(edit_widget)
    if unit:
        u = QLabel(unit)
        u.setFixedWidth(22)
        row.addWidget(u)
    return row


class ImageUploadWidget(QWidget):
    def __init__(self, label="Upload Image", parent=None):
        super().__init__(parent)
        self.path = None
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(4)
        self._btn = QPushButton(f"📂  {label}")
        self._preview = QLabel("No file selected")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setFixedHeight(70)
        self._preview.setStyleSheet(
            f"border:1px dashed {BORDER}; color:{TEXT_DIM}; border-radius:3px;")
        self._btn.clicked.connect(self._pick)
        self._lay.addWidget(self._btn)
        self._lay.addWidget(self._preview)

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.svg *.pdf)")
        if path:
            self.path = path
            px = QPixmap(path)
            if not px.isNull():
                px = px.scaled(200, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._preview.setPixmap(px)
            else:
                self._preview.setText(os.path.basename(path))


# ── Tab 1: Case ─────────────────────────────────────────────────────────
class CaseTab(QWidget):
    def __init__(self):
        super().__init__()
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(8)
        lay.setContentsMargins(16, 16, 16, 16)

        # Geometry group
        geo = QGroupBox("Geometry")
        glay = QVBoxLayout(geo)

        self.case_radius     = QLineEdit("20")
        self.case_h          = QLineEdit("12")
        self.dial_seat_radius= QLineEdit("18.5")
        self.mech_seat_radius= QLineEdit("14")
        self.mech_seat_depth = QLineEdit("4")

        for lbl_txt, widget, unit in [
            ("Case Radius",            self.case_radius,      "mm"),
            ("H (thickness)",          self.case_h,           "mm"),
            ("Dial & Glass Seat Radius", self.dial_seat_radius,"mm"),
            ("Mechanical Seat Radius", self.mech_seat_radius, "mm"),
            ("Mechanical Seat Depth",  self.mech_seat_depth,  "mm"),
        ]:
            glay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))

        lay.addWidget(geo)

        # Lugs group
        lugs = QGroupBox("Lugs")
        llay = QVBoxLayout(lugs)

        self.lug_length   = QLineEdit("8")
        self.lug_to_lug   = QLineEdit("47")
        self.strap_width  = QLineEdit("20")
        self.spring_bar_r = QLineEdit("0.75")

        self.left_lug_form  = QComboBox()
        self.right_lug_form = QComboBox()
        for cb in (self.left_lug_form, self.right_lug_form):
            cb.addItems(["straight", "curved", "angled"])

        for lbl_txt, widget, unit in [
            ("Lug Length",       self.lug_length,   "mm"),
            ("Lug-to-Lug",       self.lug_to_lug,   "mm"),
            ("Strap Width",      self.strap_width,   "mm"),
            ("Spring Bar Holes Radius", self.spring_bar_r, "mm"),
        ]:
            llay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))

        llay.addLayout(_hrow(QLabel("Left Lugs Form:"),  self.left_lug_form,  ""))
        llay.addLayout(_hrow(QLabel("Right Lugs Form:"), self.right_lug_form, ""))

        lay.addWidget(lugs)

        # Thread & Sealing group
        seal = QGroupBox("Thread & Sealing")
        slay = QVBoxLayout(seal)

        self.thread_radius_seat   = QLineEdit("19.2")
        self.seal_outer_r         = QLineEdit("19.0")
        self.seal_inner_r         = QLineEdit("18.0")
        self.seal_thickness       = QLineEdit("1.0")

        for lbl_txt, widget, unit in [
            ("Thread Radius Seat",            self.thread_radius_seat, "mm"),
            ("Sealing Rubber Outer Radius",   self.seal_outer_r,       "mm"),
            ("Sealing Rubber Inner Radius",   self.seal_inner_r,       "mm"),
            ("Sealing Rubber Thickness",      self.seal_thickness,     "mm"),
        ]:
            slay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))

        lay.addWidget(seal)

        # Crown group
        crown = QGroupBox("Crown (Winding Head)")
        clay = QVBoxLayout(crown)
        self.crown_length = QLineEdit("5")
        self.crown_width  = QLineEdit("3.5")
        for lbl_txt, widget, unit in [
            ("Crown Length", self.crown_length, "mm"),
            ("Crown Width",  self.crown_width,  "mm"),
        ]:
            clay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))
        lay.addWidget(crown)

        # Reference images group
        imgs = QGroupBox("Reference Images")
        ilay = QVBoxLayout(imgs)
        self.img_cg    = ImageUploadWidget("Computer Graphics Drawing")
        self.img_paper = ImageUploadWidget("Paper Drawing of Watch")
        self.img_draft = ImageUploadWidget("Paper Draft of Watch")
        ilay.addWidget(self.img_cg)
        ilay.addWidget(self.img_paper)
        ilay.addWidget(self.img_draft)
        lay.addWidget(imgs)

        lay.addStretch()

        sa = QScrollArea()
        sa.setWidget(content)
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main.addWidget(sa)

    def get_params(self):
        return {
            "case_radius":       self.case_radius.text(),
            "case_h":            self.case_h.text(),
            "dial_seat_radius":  self.dial_seat_radius.text(),
            "mech_seat_radius":  self.mech_seat_radius.text(),
            "mech_seat_depth":   self.mech_seat_depth.text(),
            "lug_length":        self.lug_length.text(),
            "lug_to_lug":        self.lug_to_lug.text(),
            "strap_width":       self.strap_width.text(),
            "spring_bar_r":      self.spring_bar_r.text(),
            "left_lug_form":     self.left_lug_form.currentText(),
            "right_lug_form":    self.right_lug_form.currentText(),
            "thread_radius_seat":self.thread_radius_seat.text(),
            "seal_outer_r":      self.seal_outer_r.text(),
            "seal_inner_r":      self.seal_inner_r.text(),
            "seal_thickness":    self.seal_thickness.text(),
            "crown_length":      self.crown_length.text(),
            "crown_width":       self.crown_width.text(),
        }

    def load_params(self, d):
        mapping = {
            "case_radius": self.case_radius, "case_h": self.case_h,
            "dial_seat_radius": self.dial_seat_radius,
            "mech_seat_radius": self.mech_seat_radius,
            "mech_seat_depth": self.mech_seat_depth,
            "lug_length": self.lug_length, "lug_to_lug": self.lug_to_lug,
            "strap_width": self.strap_width, "spring_bar_r": self.spring_bar_r,
            "thread_radius_seat": self.thread_radius_seat,
            "seal_outer_r": self.seal_outer_r, "seal_inner_r": self.seal_inner_r,
            "seal_thickness": self.seal_thickness,
            "crown_length": self.crown_length, "crown_width": self.crown_width,
        }
        for k, w in mapping.items():
            if k in d: w.setText(str(d[k]))
        if "left_lug_form" in d:
            idx = self.left_lug_form.findText(d["left_lug_form"])
            if idx >= 0: self.left_lug_form.setCurrentIndex(idx)
        if "right_lug_form" in d:
            idx = self.right_lug_form.findText(d["right_lug_form"])
            if idx >= 0: self.right_lug_form.setCurrentIndex(idx)


# ── Tab 2: Dial ─────────────────────────────────────────────────────────
class DialTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        geo = QGroupBox("Geometry")
        glay = QVBoxLayout(geo)

        self.dial_radius  = QLineEdit("18.5")
        self.dial_h       = QLineEdit("2")
        self.center_hole  = QLineEdit("1.5")
        self.window_r     = QLineEdit("")

        for lbl_txt, widget, unit in [
            ("Dial Radius",                self.dial_radius, "mm"),
            ("H (thickness)",              self.dial_h,      "mm"),
            ("Central Hole Radius",        self.center_hole, "mm"),
            ("Deco Mech Viewing Window R (opt.)", self.window_r, "mm"),
        ]:
            glay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))

        lay.addWidget(geo)
        lay.addStretch()

    def get_params(self):
        return {
            "dial_radius": self.dial_radius.text(),
            "dial_h": self.dial_h.text(),
            "dial_center_hole": self.center_hole.text(),
            "dial_window_r": self.window_r.text(),
        }

    def load_params(self, d):
        m = {"dial_radius": self.dial_radius, "dial_h": self.dial_h,
             "dial_center_hole": self.center_hole, "dial_window_r": self.window_r}
        for k, w in m.items():
            if k in d: w.setText(str(d[k]))


# ── Tab 3: Backplate ─────────────────────────────────────────────────────
class BackplateTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        geo = QGroupBox("Geometry")
        glay = QVBoxLayout(geo)

        self.back_radius      = QLineEdit("20")
        self.back_h           = QLineEdit("2")
        self.thread_radius    = QLineEdit("19.2")
        self.thread_thickness = QLineEdit("0.5")
        self.seal_outer_r     = QLineEdit("19.0")
        self.seal_inner_r     = QLineEdit("18.0")

        for lbl_txt, widget, unit in [
            ("Backplate Radius",           self.back_radius,      "mm"),
            ("H (thickness)",              self.back_h,           "mm"),
            ("Thread Radius",              self.thread_radius,    "mm"),
            ("Thread Thickness",           self.thread_thickness, "mm"),
            ("Sealing Rubber Outer Radius",self.seal_outer_r,     "mm"),
            ("Sealing Rubber Inner Radius",self.seal_inner_r,     "mm"),
        ]:
            glay.addLayout(_hrow(QLabel(lbl_txt+":"), widget, unit))

        lay.addWidget(geo)

        imgs = QGroupBox("Reference Drafts")
        ilay = QVBoxLayout(imgs)
        self.img_draft = ImageUploadWidget("Paper Drafts")
        ilay.addWidget(self.img_draft)
        lay.addWidget(imgs)

        lay.addStretch()

    def get_params(self):
        return {
            "backplate_radius": self.back_radius.text(),
            "back_h": self.back_h.text(),
            "back_thread_radius": self.thread_radius.text(),
            "back_thread_thickness": self.thread_thickness.text(),
            "back_seal_outer_r": self.seal_outer_r.text(),
            "back_seal_inner_r": self.seal_inner_r.text(),
        }

    def load_params(self, d):
        m = {
            "backplate_radius": self.back_radius,
            "back_h": self.back_h,
            "back_thread_radius": self.thread_radius,
            "back_thread_thickness": self.thread_thickness,
            "back_seal_outer_r": self.seal_outer_r,
            "back_seal_inner_r": self.seal_inner_r,
        }
        for k, w in m.items():
            if k in d: w.setText(str(d[k]))


# ── Tab 4: Hands ─────────────────────────────────────────────────────────
class HandsTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        bal = QGroupBox("Counter Balance")
        blay = QHBoxLayout(bal)
        self.counter_balanced = QComboBox()
        self.counter_balanced.addItems(["Yes", "No"])
        blay.addWidget(QLabel("Counter Balanced?"))
        blay.addStretch()
        blay.addWidget(self.counter_balanced)
        lay.addWidget(bal)

        self._hands = {}
        for hand_name in ("Hour", "Minute", "Second"):
            grp = QGroupBox(f"{hand_name} Hand")
            glay = QVBoxLayout(grp)
            fields = {}
            defaults = {
                "Hour":   dict(front="11", back="3",  wide="3.0", h="1.2", hole="0.75"),
                "Minute": dict(front="16", back="4",  wide="2.0", h="1.0", hole="0.75"),
                "Second": dict(front="17", back="5",  wide="1.0", h="0.8", hole="0.75"),
            }[hand_name]
            for lbl_txt, key, default in [
                ("Frontward Length", "front", defaults["front"]),
                ("Backward Length",  "back",  defaults["back"]),
                ("Max Width",        "wide",  defaults["wide"]),
                ("H (thickness)",    "h",     defaults["h"]),
                ("Central Hole R",   "hole",  defaults["hole"]),
            ]:
                w = QLineEdit(default)
                fields[key] = w
                glay.addLayout(_hrow(QLabel(lbl_txt+":"), w, "mm"))
            self._hands[hand_name] = fields
            lay.addWidget(grp)

        lay.addStretch()

    def get_params(self):
        out = {"counter_balanced": self.counter_balanced.currentText()}
        for hand, fields in self._hands.items():
            for k, w in fields.items():
                out[f"hand_{hand.lower()}_{k}"] = w.text()
        return out

    def load_params(self, d):
        if "counter_balanced" in d:
            idx = self.counter_balanced.findText(d["counter_balanced"])
            if idx >= 0: self.counter_balanced.setCurrentIndex(idx)
        for hand, fields in self._hands.items():
            for k, w in fields.items():
                key = f"hand_{hand.lower()}_{k}"
                if key in d: w.setText(str(d[key]))


# ── Tab 5: Photos ────────────────────────────────────────────────────────
class PhotosTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        imgs = QGroupBox("Reference Material")
        ilay = QVBoxLayout(imgs)
        self.img_draft  = ImageUploadWidget("Paper Draft")
        self.img_design = ImageUploadWidget("Paper Design")
        self.img_cg     = ImageUploadWidget("Computer Graphics Designs")
        ilay.addWidget(self.img_draft)
        ilay.addWidget(self.img_design)
        ilay.addWidget(self.img_cg)
        lay.addWidget(imgs)
        lay.addStretch()


# ──────────────────────── FCSTD GENERATOR ──────────────────────────────
# Generates a minimal valid FreeCAD file (ZIP-based .FCStd)

def _float(v, default=0.0):
    try: return float(v)
    except: return default

def generate_fcstd(params: dict, mode: str, filepath: str):
    """
    Generate a minimal .FCStd file containing parametric watch parts.
    .FCStd is a ZIP archive containing Document.xml and other files.
    We write a proper FreeCAD Document.xml with Part::Cylinder objects.
    """
    import zipfile
    import io

    p = params
    case_r   = _float(p.get("case_radius", 20))
    case_h   = _float(p.get("case_h", 12))
    dial_r   = _float(p.get("dial_radius", case_r - 1.5))
    dial_h   = _float(p.get("dial_h", 2))
    back_r   = _float(p.get("backplate_radius", case_r))
    back_h   = _float(p.get("back_h", 2))
    seat_r   = _float(p.get("dial_seat_radius", case_r - 1.5))
    mech_r   = _float(p.get("mech_seat_radius", 14))
    mech_d   = _float(p.get("mech_seat_depth", 4))
    lug_l    = _float(p.get("lug_length", 8))
    lug_h    = case_h * 0.7
    strap_w  = _float(p.get("strap_width", 20))
    crown_l  = _float(p.get("crown_length", 5))
    crown_w  = _float(p.get("crown_width", 3.5))

    explode_gap = 8.0 if mode == "exploded" else 0.0

    z_back  = 0.0
    z_case  = back_h + explode_gap
    z_dial  = z_case + case_h - dial_h - 0.5 + explode_gap * 0.8

    # Parts offset for "parts" mode
    if mode == "parts":
        dx_back = -(case_r * 3)
        dx_case = 0
        dx_dial = case_r * 3
    else:
        dx_back = dx_case = dx_dial = 0

    # Build objects list: (name, label, radius, height, x, y, z)
    objects = [
        ("Backplate", "Backplate",   back_r,  back_h,  dx_back, 0, z_back),
        ("CaseBody",  "Case Body",   case_r,  case_h,  dx_case, 0, z_case),
        ("DialBody",  "Dial",        dial_r,  dial_h,  dx_dial, 0, z_dial),
        # Mechanical seat (cut from case — represented as separate object)
        ("MechSeat",  "Mech Seat",   mech_r,  mech_d,  dx_case, 0, z_case),
        # Crown
        ("Crown",     "Crown",       crown_w/2, crown_l,
         dx_case + case_r, 0, z_case + case_h*0.35),
    ]

    # --- Build Document.xml ---
    xml_objects = ""
    xml_links = ""
    for i, (name, label, rad, height, ox, oy, oz) in enumerate(objects):
        xml_objects += f"""
        <Object name="{name}" type="Part::Cylinder">
            <Properties>
                <Property name="Radius" type="App::PropertyLength">
                    <Float value="{rad}"/>
                </Property>
                <Property name="Height" type="App::PropertyLength">
                    <Float value="{height}"/>
                </Property>
                <Property name="Placement" type="App::PropertyPlacement">
                    <PropertyPlacement Px="{ox}" Py="{oy}" Pz="{oz}" Q0="0" Q1="0" Q2="0" Q3="1"/>
                </Property>
                <Property name="Label" type="App::PropertyString">
                    <String value="{label}"/>
                </Property>
                <Property name="Label2" type="App::PropertyString">
                    <String value=""/>
                </Property>
                <Property name="Visibility" type="App::PropertyBool">
                    <Bool value="true"/>
                </Property>
            </Properties>
        </Object>"""

    doc_xml = f"""<?xml version='1.0' encoding='utf-8'?>
<Document SchemaVersion="4" ProgramVersion="0.21" FileVersion="1">
    <Properties>
        <Property name="Label" type="App::PropertyString">
            <String value="UzhovWatch_{mode}"/>
        </Property>
        <Property name="Comment" type="App::PropertyString">
            <String value="Generated by Uzhov Watches CAD"/>
        </Property>
        <Property name="Company" type="App::PropertyString">
            <String value="Uzhov Watches"/>
        </Property>
    </Properties>
    <Objects>{xml_objects}
    </Objects>
    <ObjectData>
    </ObjectData>
</Document>
"""

    gui_xml = """<?xml version='1.0' encoding='utf-8'?>
<Document SchemaVersion="1">
    <ViewProviders>
    </ViewProviders>
</Document>
"""

    # Write .FCStd (ZIP)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Document.xml", doc_xml.encode("utf-8"))
        zf.writestr("GuiDocument.xml", gui_xml.encode("utf-8"))

    with open(filepath, "wb") as f:
        f.write(buf.getvalue())


# ──────────────────────────── MAIN WINDOW ──────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Uzhov Watches CAD")
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)
        self._mode = "assembly"

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top header bar ──────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background:{BG2}; border-bottom:1px solid {BORDER};")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("⌚  UZHOV WATCHES CAD")
        logo.setStyleSheet(
            f"color:{GOLD}; font-family:'Courier New',monospace; "
            f"font-size:15px; letter-spacing:3px; font-weight:bold;")
        hlay.addWidget(logo)
        hlay.addStretch()

        # Mode buttons
        self._mode_btns = {}
        for m, lbl in [("assembly","Assembly"), ("exploded","Exploded View"), ("parts","Parts")]:
            btn = QPushButton(lbl)
            btn.setObjectName("mode_btn")
            btn.setProperty("active", "false")
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, mm=m: self._set_mode(mm))
            self._mode_btns[m] = btn
            hlay.addWidget(btn)

        hlay.addSpacing(20)

        # Assemble/Disassemble button
        self._toggle_btn = QPushButton("Disassemble")
        self._toggle_btn.setFixedHeight(32)
        self._toggle_btn.clicked.connect(self._toggle_explode)
        hlay.addWidget(self._toggle_btn)

        root.addWidget(header)

        # ── Content splitter ────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # Left: tabs
        left = QWidget()
        left.setMinimumWidth(320)
        left.setMaximumWidth(520)
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 0, 0)
        llay.setSpacing(0)

        self._tabs = QTabWidget()
        self._tab_case      = CaseTab()
        self._tab_dial      = DialTab()
        self._tab_backplate = BackplateTab()
        self._tab_hands     = HandsTab()
        self._tab_photos    = PhotosTab()
        self._tabs.addTab(self._tab_case,      "Case")
        self._tabs.addTab(self._tab_dial,      "Dial")
        self._tabs.addTab(self._tab_backplate, "Backplate")
        self._tabs.addTab(self._tab_hands,     "Hands")
        self._tabs.addTab(self._tab_photos,    "Photos")
        self._tabs.currentChanged.connect(self._refresh_preview)
        llay.addWidget(self._tabs)

        # Bottom buttons
        btn_row = QWidget()
        btn_row.setStyleSheet(f"background:{BG2}; border-top:1px solid {BORDER};")
        blay = QHBoxLayout(btn_row)
        blay.setContentsMargins(12, 8, 12, 8)
        blay.setSpacing(8)

        self._btn_gen = QPushButton("⬡  Generate & Save  (.FCStd)")
        self._btn_gen.setObjectName("gold_btn")
        self._btn_gen.setFixedHeight(36)
        self._btn_gen.clicked.connect(self._generate)

        self._btn_save = QPushButton("💾  Save Project  (.json)")
        self._btn_save.setFixedHeight(36)
        self._btn_save.clicked.connect(self._save_project)

        self._btn_load = QPushButton("📂  Load Project")
        self._btn_load.setFixedHeight(36)
        self._btn_load.clicked.connect(self._load_project)

        blay.addWidget(self._btn_gen)
        blay.addWidget(self._btn_save)
        blay.addWidget(self._btn_load)

        llay.addWidget(btn_row)
        splitter.addWidget(left)

        # Right: 3D viewport
        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(0)

        vp_header = QWidget()
        vp_header.setFixedHeight(30)
        vp_header.setStyleSheet(
            f"background:{BG3}; border-bottom:1px solid {BORDER};")
        vphl = QHBoxLayout(vp_header)
        vphl.setContentsMargins(12, 0, 12, 0)
        vphl.addWidget(QLabel("3D Preview  —  drag to rotate  |  scroll to zoom"))
        vphl.addStretch()
        self._btn_refresh = QPushButton("⟳  Refresh")
        self._btn_refresh.setFixedHeight(22)
        self._btn_refresh.clicked.connect(self._refresh_preview)
        vphl.addWidget(self._btn_refresh)
        rlay.addWidget(vp_header)

        self._viewport = Viewport3D()
        rlay.addWidget(self._viewport)

        splitter.addWidget(right)
        splitter.setSizes([420, 860])
        root.addWidget(splitter)

        # ── Status bar ──────────────────────────────────────────
        self.statusBar().showMessage(
            "Ready  ·  Drag to rotate  ·  Scroll to zoom  ·  "
            "Fill parameters and click Generate & Save")

        # Init
        self._set_mode("assembly")

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_preview)
        self._refresh_timer.start(1500)

    # ── Mode management ─────────────────────────────────────────────
    def _set_mode(self, mode: str):
        self._mode = mode
        for m, btn in self._mode_btns.items():
            btn.setProperty("active", "true" if m == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if mode == "assembly":
            self._toggle_btn.setText("Disassemble")
        elif mode == "exploded":
            self._toggle_btn.setText("Assemble")
        else:
            self._toggle_btn.setVisible(False)
        self._toggle_btn.setVisible(mode != "parts")
        self._viewport.set_mode(mode)
        self.statusBar().showMessage(f"Mode: {mode.upper()}")

    def _toggle_explode(self):
        if self._mode == "assembly":
            self._set_mode("exploded")
        else:
            self._set_mode("assembly")

    # ── Collect all params ──────────────────────────────────────────
    def _collect_params(self):
        p = {}
        p.update(self._tab_case.get_params())
        p.update(self._tab_dial.get_params())
        p.update(self._tab_backplate.get_params())
        p.update(self._tab_hands.get_params())
        return p

    def _refresh_preview(self):
        p = self._collect_params()
        self._viewport.set_params(p)

    # ── Generate .FCStd ─────────────────────────────────────────────
    def _generate(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save FreeCAD Model", "UzhovWatch.FCStd",
            "FreeCAD Files (*.FCStd)")
        if not path:
            return
        if not path.endswith(".FCStd"):
            path += ".FCStd"
        try:
            params = self._collect_params()
            generate_fcstd(params, self._mode, path)
            QMessageBox.information(
                self, "Success",
                f"Model saved to:\n{path}\n\n"
                f"Open with FreeCAD to view and further edit the parametric model.")
            self.statusBar().showMessage(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate model:\n{e}")

    # ── Save/Load project JSON ──────────────────────────────────────
    def _save_project(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "UzhovWatch.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            data = {
                "version": "1.0",
                "mode": self._mode,
                "params": self._collect_params(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f"Project saved: {path}")
            QMessageBox.information(self, "Saved", f"Project saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            params = data.get("params", {})
            self._tab_case.load_params(params)
            self._tab_dial.load_params(params)
            self._tab_backplate.load_params(params)
            self._tab_hands.load_params(params)
            if "mode" in data:
                self._set_mode(data["mode"])
            self._refresh_preview()
            self.statusBar().showMessage(f"Project loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load:\n{e}")


# ──────────────────────────── ENTRY POINT ──────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Uzhov Watches CAD")
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
