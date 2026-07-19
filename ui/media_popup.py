"""Draggable, stackable floating windows that show the media/data payload
attached to a Source/Event, opened by clicking an item in the Events Feed or
a marker on the Map (see ui/main_window.py's _open_media_popup). Content
renders per Event.type: photo -> QPixmap, video/audio -> QMediaPlayer,
fft/float_sequence -> a pyqtgraph line plot of the decoded sequence.
"""
import base64
import json
import os
import tempfile

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QUrl, QPoint
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy,
)

from common.schemas import Event

_OPEN_OFFSET = [0]  # cascades successive popups so they don't fully overlap


class FloatingWindow(QWidget):
    """Frameless, non-modal internal window: drag by its title bar, close via
    the × button, multiple instances stack (cascade-positioned, independently
    movable/closable) rather than replacing each other.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumSize(360, 240)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        outer.addWidget(self._build_title_bar(title))

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        outer.addWidget(self.content, stretch=1)

        self.setStyleSheet(
            "FloatingWindow { border: 1px solid #5a86b8; background: #1c2b3a; }"
        )
        self._drag_offset = None
        self._cascade_spawn()

    def _build_title_bar(self, title: str) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(26)
        bar.setStyleSheet("background: #26405e;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        layout.addStretch(1)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        bar.mousePressEvent = self._title_press
        bar.mouseMoveEvent = self._title_move
        return bar

    def _title_press(self, event):
        self._drag_offset = event.globalPos() - self.pos()

    def _title_move(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_offset)

    def _cascade_spawn(self):
        step = 32
        offset = (_OPEN_OFFSET[0] % 10) * step
        _OPEN_OFFSET[0] += 1
        parent = self.parentWidget()
        base = parent.mapToGlobal(QPoint(40, 40)) if parent else QPoint(200, 200)
        self.move(base + QPoint(offset, offset))


class MediaPopup(FloatingWindow):
    def __init__(self, event: Event, parent=None):
        super().__init__(title=f"{event.type} — {event.id}", parent=parent)
        self.resize(480, 360)
        self._tmp_path = None

        raw = base64.b64decode(event.data)
        if event.type == "photo":
            self._show_photo(raw)
        elif event.type == "video":
            self._show_video(raw)
        elif event.type == "audio":
            self._show_audio(raw)
        elif event.type == "fft":
            self._show_spectrum(raw)
        elif event.type == "float_sequence":
            self._show_sequence(raw)
        else:
            self.content_layout.addWidget(QLabel(f"No viewer for type '{event.type}'"))

        caption = QLabel(event.description)
        caption.setWordWrap(True)
        caption.setStyleSheet("padding: 6px;")
        self.content_layout.addWidget(caption)

    # ── renderers ──────────────────────────────────────────────────────────

    def _show_photo(self, raw: bytes):
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap()
        pixmap.loadFromData(raw)
        label.setPixmap(pixmap.scaled(440, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.content_layout.addWidget(label, stretch=1)

    def _make_player(self, raw: bytes, suffix: str) -> QMediaPlayer:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        self._tmp_path = path

        player = QMediaPlayer(self)
        player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        return player

    def _add_transport_controls(self, player: QMediaPlayer):
        controls = QHBoxLayout()
        play_btn = QPushButton("▶")
        play_btn.setFixedWidth(32)

        def toggle():
            if player.state() == QMediaPlayer.PlayingState:
                player.pause()
                play_btn.setText("▶")
            else:
                player.play()
                play_btn.setText("⏸")

        play_btn.clicked.connect(toggle)

        slider = QSlider(Qt.Horizontal)
        player.durationChanged.connect(slider.setMaximum)
        player.positionChanged.connect(slider.setValue)
        slider.sliderMoved.connect(player.setPosition)

        controls.addWidget(play_btn)
        controls.addWidget(slider, stretch=1)
        self.content_layout.addLayout(controls)

    def _show_video(self, raw: bytes):
        player = self._make_player(raw, ".mp4")
        video_widget = QVideoWidget()
        video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        player.setVideoOutput(video_widget)
        self.content_layout.addWidget(video_widget, stretch=1)
        self._add_transport_controls(player)
        self._player = player  # keep a live reference so it isn't GC'd

    def _show_audio(self, raw: bytes):
        player = self._make_player(raw, ".wav")
        self.content_layout.addStretch(1)
        self._add_transport_controls(player)
        self._player = player

    def _show_sequence(self, raw: bytes):
        values = json.loads(raw)
        plot = pg.PlotWidget(background="#1c2b3a")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.plot(values, pen=pg.mkPen("#5a86b8", width=1))
        self.content_layout.addWidget(plot, stretch=1)

    def _show_spectrum(self, raw: bytes):
        # classic SDR#/HDSDR layout: a live spectrum trace on top, a
        # scrolling waterfall below, deep navy background with a bright
        # cyan/white trace. Only one real FFT snapshot exists per event --
        # there's no actual time series to feed a real waterfall -- so the
        # waterfall is synthesized: many noisy, slightly-jittered copies of
        # that one real spectrum, which is what a steady RF signature
        # actually looks like over a few seconds on a genuine SDR waterfall.
        values = json.loads(raw)
        arr = np.array(values, dtype=float)

        spectrum_plot = pg.PlotWidget(background="#00081a")
        spectrum_plot.showGrid(x=True, y=True, alpha=0.25)
        spectrum_plot.getAxis("left").setPen(pg.mkPen("#2a4d6e"))
        spectrum_plot.getAxis("bottom").setPen(pg.mkPen("#2a4d6e"))
        spectrum_plot.setLabel("left", "Magnitude")
        spectrum_plot.setLabel("bottom", "Frequency bin")
        spectrum_plot.plot(
            arr,
            pen=pg.mkPen("#00e5ff", width=1),
            fillLevel=0,
            brush=pg.mkBrush(0, 229, 255, 60),
        )
        spectrum_plot.setMaximumHeight(150)
        self.content_layout.addWidget(spectrum_plot)

        n_frames = 90
        rng = np.random.default_rng()
        noise_floor = (np.abs(arr).max() * 0.06) if arr.size else 1.0
        waterfall = np.tile(arr, (n_frames, 1))
        waterfall += rng.normal(0, noise_floor, waterfall.shape)
        for i in range(n_frames):
            waterfall[i] = np.roll(waterfall[i], int(rng.integers(-2, 3)))
        waterfall = np.clip(waterfall, 0, None)

        waterfall_plot = pg.PlotWidget(background="#00081a")
        waterfall_plot.hideAxis("left")
        waterfall_plot.hideAxis("bottom")
        waterfall_plot.setMouseEnabled(x=False, y=False)
        img = pg.ImageItem(waterfall.T)
        cmap = pg.ColorMap(
            [0.0, 0.3, 0.55, 0.75, 1.0],
            [(0, 8, 26), (0, 40, 90), (0, 120, 180), (0, 200, 255), (255, 255, 255)],
        )
        img.setLookupTable(cmap.getLookupTable())
        img.setLevels([0, max(float(waterfall.max()), 1.0)])
        waterfall_plot.addItem(img)
        self.content_layout.addWidget(waterfall_plot, stretch=1)

    def closeEvent(self, event):
        if self._tmp_path and os.path.exists(self._tmp_path):
            os.remove(self._tmp_path)
        super().closeEvent(event)
