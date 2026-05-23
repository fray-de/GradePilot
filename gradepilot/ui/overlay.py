"""Fullscreen translucent overlay for picking a screen rectangle or a click point.

PyQt6 is imported lazily so the M1 commands (--version / --check-config /
--init-db) don't pay the Qt import cost.
"""
from __future__ import annotations

import ctypes
import sys

from gradepilot.profiles import Point, Rect


_DPI_AWARENESS_SET = False


def _ensure_dpi_aware() -> None:
    """Match PyAutoGUI's coordinate space (physical pixels) on Windows HiDPI.

    Without this, a 125% scaled laptop screen would make Qt-reported coords
    differ from pyautogui's by 1.25x, breaking clicks on the saved profile.
    """
    global _DPI_AWARENESS_SET
    if _DPI_AWARENESS_SET or sys.platform != "win32":
        return
    user32 = ctypes.windll.user32
    # Win10 1703+: Per-Monitor-V2
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            _DPI_AWARENESS_SET = True
            return
    except (AttributeError, OSError):
        pass
    # Win8.1+: PROCESS_PER_MONITOR_DPI_AWARE = 2
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        _DPI_AWARENESS_SET = True
        return
    except (AttributeError, OSError):
        pass
    # Vista+: system-DPI aware
    try:
        user32.SetProcessDPIAware()
        _DPI_AWARENESS_SET = True
    except (AttributeError, OSError):
        pass


class UserCancelled(Exception):
    """User pressed Esc during profile capture."""


def _make_overlay(prompt: str, mode: str):
    """Lazy-import PyQt6 and build the overlay widget class on demand."""
    from PyQt6.QtCore import QEventLoop, QPoint, QRect, Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
    from PyQt6.QtWidgets import QApplication, QWidget

    class SelectionOverlay(QWidget):
        finished = pyqtSignal()

        def __init__(self) -> None:
            super().__init__()
            self._mode = mode  # "rect" or "point"
            self._prompt = prompt
            self._start: QPoint | None = None
            self._current: QPoint | None = None
            self.result: QRect | QPoint | None = None

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setCursor(Qt.CursorShape.CrossCursor)

            # Span every monitor.
            virtual = QApplication.primaryScreen().virtualGeometry()
            self.setGeometry(virtual)

        def keyPressEvent(self, event):  # noqa: N802 (Qt naming)
            if event.key() == Qt.Key.Key_Escape:
                self.result = None
                self._finish()

        def mousePressEvent(self, event):  # noqa: N802
            if event.button() != Qt.MouseButton.LeftButton:
                return
            pos = event.position().toPoint()
            if self._mode == "point":
                self.result = pos
                self._finish()
            else:
                self._start = pos
                self._current = pos
                self.update()

        def mouseMoveEvent(self, event):  # noqa: N802
            if self._start is not None:
                self._current = event.position().toPoint()
                self.update()

        def mouseReleaseEvent(self, event):  # noqa: N802
            if event.button() != Qt.MouseButton.LeftButton or self._mode != "rect":
                return
            if self._start and self._current:
                rect = QRect(self._start, self._current).normalized()
                if rect.width() >= 8 and rect.height() >= 8:
                    self.result = rect
                    self._finish()
                else:
                    # Too small — treat as misclick, let user try again.
                    self._start = None
                    self._current = None
                    self.update()

        def _finish(self) -> None:
            self.hide()
            self.finished.emit()

        def paintEvent(self, event):  # noqa: N802
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

            if self._mode == "rect" and self._start and self._current:
                rect = QRect(self._start, self._current).normalized()
                # Cut out the selection so the user sees through to the UI underneath.
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                pen = QPen(QColor(0, 200, 255))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(rect)
                label = f"{rect.x()},{rect.y()}  {rect.width()}x{rect.height()}"
                painter.setPen(QColor(0, 200, 255))
                font = QFont()
                font.setPointSize(11)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(rect.topLeft() + QPoint(0, -8), label)

            painter.setPen(QColor(255, 255, 255))
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            painter.setFont(title_font)
            metrics = QFontMetrics(title_font)
            text_rect = self.rect().adjusted(40, 40, -40, -40)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                self._prompt + "\n(Esc to cancel)",
            )
            _ = metrics  # silence unused warning

    return SelectionOverlay, QApplication, QEventLoop


def _run_overlay(prompt: str, mode: str):
    _ensure_dpi_aware()
    SelectionOverlay, QApplication, QEventLoop = _make_overlay(prompt, mode)
    app = QApplication.instance() or QApplication(sys.argv)
    overlay = SelectionOverlay()
    loop = QEventLoop()
    overlay.finished.connect(loop.quit)
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    loop.exec()
    return overlay.result, app


def pick_region(prompt: str) -> Rect | None:
    """Show overlay, let the user drag a rectangle, return it (None on Esc)."""
    result, _ = _run_overlay(prompt, "rect")
    if result is None:
        return None
    return Rect(result.x(), result.y(), result.width(), result.height())


def pick_point(prompt: str) -> Point | None:
    """Show overlay, let the user click a point, return it (None on Esc)."""
    result, _ = _run_overlay(prompt, "point")
    if result is None:
        return None
    return Point(result.x(), result.y())


def screen_size() -> tuple[int, int]:
    """Primary screen size in physical pixels (after DPI awareness is set)."""
    _ensure_dpi_aware()
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    geom = app.primaryScreen().geometry()
    return geom.width(), geom.height()
