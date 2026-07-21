"""Draggable, stackable floating windows that show the media/data payload
attached to a Source/Event, opened by clicking an item in the Events Feed or
a marker on the Map (see ui/main_window.py's _open_media_popup). Content
renders per Event.type: photo -> QPixmap, video/audio -> QMediaPlayer,
fft/float_sequence -> a pyqtgraph line plot of the decoded sequence.

Opened media viewers (MediaSlot) live inside one shared PopupGroup window
rather than each owning its own top-level window -- multiple incidents opened
one after another used to scatter independent floating windows around the
screen; grouping them behind a single title bar means dragging it moves the
whole set together.
"""
import base64
import json
import os
import subprocess
import tempfile

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QUrl, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSlider,
    QSizePolicy, QScrollArea, QSizeGrip, QFrame, QStackedWidget,
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
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        outer.addWidget(self.content, stretch=1)
        outer.addWidget(self._build_resize_bar())

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

    def _build_resize_bar(self) -> QWidget:
        # Frameless windows (Qt.FramelessWindowHint) lose the OS's own
        # edge-drag resize entirely -- this reserves a strip for a QSizeGrip
        # so there's still a way to resize by hand, not just via
        # PopupGroup's own auto-fit-to-grid sizing.
        bar = QWidget()
        bar.setFixedHeight(14)
        bar.setStyleSheet("background: #26405e;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(QSizeGrip(bar), 0, Qt.AlignBottom | Qt.AlignRight)
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


class MediaSlot(QWidget):
    """One event's rendered media, as a bordered panel meant to sit inside a
    PopupGroup's grid rather than own a top-level window itself. Clicking its
    title bar (not the close button) emits `selected` -- lets the operator
    locate an event on the map/feed starting from its media instead of only
    the other way around.
    """
    closeRequested = pyqtSignal(str)
    selected = pyqtSignal(str)

    def __init__(self, event: Event, parent=None):
        super().__init__(parent)
        self.event_id = event.id
        self._tmp_path = None
        self._player = None
        self._video_stack = None
        # Same size the standalone popup used to default to (480x360) -- the
        # grid shouldn't make individual viewers smaller or stretch them,
        # just arrange several of that same size next to each other.
        self.setFixedSize(480, 360)
        self.setStyleSheet(
            "MediaSlot { border: 1px solid #3a5a7e; background: #16232f; }"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        outer.addWidget(self._build_slot_bar(event))

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        outer.addWidget(self.content, stretch=1)

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

    def _build_slot_bar(self, event: Event) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(22)
        bar.setStyleSheet("background: #203349;")
        bar.setCursor(Qt.PointingHandCursor)
        bar.mousePressEvent = lambda e: self.selected.emit(self.event_id)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(6, 0, 4, 0)
        layout.addWidget(QLabel(f"<b>{event.type} — {event.id}</b>"))
        layout.addStretch(1)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(18, 18)
        close_btn.clicked.connect(lambda: self.closeRequested.emit(self.event_id))
        layout.addWidget(close_btn)
        return bar

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
        # Default notify interval is 1000ms -- positionChanged (which drives
        # the progress slider) only fires once a second. Several clips here
        # are only 1-2 seconds long, so the slider was getting 0-1 updates
        # for the whole clip: looked static for audio, and like a few
        # discrete jumps ("begin, middle, end") for slightly longer video.
        player.setNotifyInterval(50)
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
                if self._video_stack is not None:
                    self._video_stack.setCurrentIndex(1)  # swap poster frame -> live video widget
                player.play()
                play_btn.setText("⏸")

        def on_status_changed(status):
            if status == QMediaPlayer.EndOfMedia:
                player.setPosition(0)
                play_btn.setText("▶")
                if self._video_stack is not None:
                    self._video_stack.setCurrentIndex(0)  # back to the poster frame, not a frozen last frame

        play_btn.clicked.connect(toggle)
        player.mediaStatusChanged.connect(on_status_changed)

        slider = QSlider(Qt.Horizontal)
        player.durationChanged.connect(slider.setMaximum)
        player.positionChanged.connect(slider.setValue)
        slider.sliderMoved.connect(player.setPosition)

        controls.addWidget(play_btn)
        controls.addWidget(slider, stretch=1)
        self.content_layout.addLayout(controls)

    def _extract_poster_frame(self, video_path: str) -> QPixmap | None:
        """Grab a single frame from the middle of the video via ffmpeg, to
        show as a poster before playback starts instead of QVideoWidget's
        default blank/black area. Best-effort: falls back to no poster (just
        the blank video widget, same as before) if ffmpeg is missing or the
        probe/extract fails for any reason -- never worth failing the whole
        popup over.
        """
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True, timeout=5,
            )
            duration = float(probe.stdout.strip())
        except Exception:
            duration = 0.0

        fd, thumb_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", str(max(duration / 2, 0.0)), "-i", video_path,
                 "-frames:v", "1", thumb_path],
                capture_output=True, timeout=10,
            )
            if result.returncode != 0:
                return None
            pixmap = QPixmap(thumb_path)
            return pixmap if not pixmap.isNull() else None
        except Exception:
            return None
        finally:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

    def _show_video(self, raw: bytes):
        player = self._make_player(raw, ".mp4")
        video_widget = QVideoWidget()
        video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        player.setVideoOutput(video_widget)

        poster = self._extract_poster_frame(self._tmp_path)
        if poster is not None:
            poster_label = QLabel()
            poster_label.setAlignment(Qt.AlignCenter)
            poster_label.setStyleSheet("background: black;")
            poster_label.setPixmap(poster.scaled(440, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            self._video_stack = QStackedWidget()
            self._video_stack.addWidget(poster_label)  # index 0 -- shown until Play
            self._video_stack.addWidget(video_widget)  # index 1
            self.content_layout.addWidget(self._video_stack, stretch=1)
        else:
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

    def cleanup(self):
        if self._player is not None:
            self._player.stop()
        if self._tmp_path and os.path.exists(self._tmp_path):
            os.remove(self._tmp_path)


class PopupGroup(FloatingWindow):
    """Single draggable window holding one MediaSlot per open incident, laid
    out in a fixed-width grid (wraps to a new row past _COLS) behind one
    title bar -- so opening several incidents in a row doesn't scatter
    independent windows around the screen; dragging the one title bar moves
    the whole set together. The window grows to fit its grid -- width is
    naturally bounded by _COLS, height isn't bounded at all (the scroll area
    only kicks in once it no longer fits the screen, not before).
    """
    eventSelected = pyqtSignal(str)

    _COLS = 3
    _SLOT_SIZE = (480, 360)  # must match MediaSlot's fixed size

    def __init__(self, parent=None):
        super().__init__(title="", parent=parent)
        self.resize(*self._SLOT_SIZE)
        self._slots: dict[str, MediaSlot] = {}
        self._order: list[str] = []  # insertion order -- grid position derives from this

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(4)
        # Without this, QScrollArea's setWidgetResizable(True) below stretches
        # _grid_host (and so the grid's row/column) to fill the whole viewport
        # whenever there are fewer slots than fit it -- which then stretched
        # each MediaSlot up to fill that leftover space instead of leaving it
        # at its fixed size. Anchoring the grid itself top-left keeps any
        # extra space as blank space instead of being distributed into cells.
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.NoFrame)  # its own bevel clashed with FloatingWindow's border
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(self._grid_host)
        scroll.setStyleSheet("""
            QScrollBar:horizontal, QScrollBar:vertical {
                background: #16232f;
                margin: 0;
            }
            QScrollBar:horizontal { height: 12px; }
            QScrollBar:vertical { width: 12px; }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: #3a5a7e;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal { min-width: 24px; }
            QScrollBar::handle:vertical { min-height: 24px; }
            QScrollBar::handle:hover { background: #5a86b8; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
            QScrollBar::add-page, QScrollBar::sub-page { background: none; }
        """)
        self.content_layout.addWidget(scroll, stretch=1)

    def has_event(self, event_id: str) -> bool:
        return event_id in self._slots

    def add_slot(self, event: Event):
        slot = MediaSlot(event)
        slot.closeRequested.connect(self.remove_slot)
        slot.selected.connect(self.eventSelected)
        self._slots[event.id] = slot
        self._order.append(event.id)
        self._relayout()

    def remove_slot(self, event_id: str):
        slot = self._slots.pop(event_id, None)
        if slot is None:
            return
        self._order.remove(event_id)
        slot.cleanup()
        slot.setParent(None)
        slot.deleteLater()
        if not self._slots:
            self.close()
        else:
            self._relayout()

    def _relayout(self):
        # Simplest correct way to keep a gap-free grid after a mid-list
        # removal: clear the layout's item list (this does not delete the
        # widgets) and re-add everything in insertion order.
        while self._grid.count():
            self._grid.takeAt(0)
        for i, event_id in enumerate(self._order):
            row, col = divmod(i, self._COLS)
            self._grid.addWidget(self._slots[event_id], row, col, Qt.AlignTop | Qt.AlignLeft)
        self._resize_to_fit()

    def _resize_to_fit(self):
        # Pure arithmetic from known constants -- no sizeHint() involved.
        # sizeHint() queried right after addWidget() in the same call was
        # returning a stale, one-step-behind value (Qt's layout size cache
        # not yet recomputed), which is exactly the "lags by one slot" bug
        # this was producing. Fixed quantities only, so there's nothing left
        # to race.
        n = len(self._order)
        if n == 0:
            return
        cols = min(self._COLS, n)
        rows = -(-n // self._COLS)  # ceil division
        slot_w, slot_h = self._SLOT_SIZE
        grid_spacing = 4    # must match self._grid.setSpacing(4)
        grid_margin = 4     # must match self._grid.setContentsMargins(4,4,4,4), each side
        title_bar_h = 26
        resize_bar_h = 14
        outer_border = 2    # FloatingWindow's own 1px border, each side
        slack = 30          # extra headroom so the scroll area's scrollbar never eats into content

        grid_w = cols * slot_w + (cols - 1) * grid_spacing + 2 * grid_margin
        grid_h = rows * slot_h + (rows - 1) * grid_spacing + 2 * grid_margin

        width = grid_w + outer_border + slack
        height = grid_h + outer_border + title_bar_h + resize_bar_h + slack
        self.resize(width, height)

    def closeEvent(self, event):
        # Closing the whole group (its own × button) skips remove_slot for
        # whatever's still open -- clean those up here instead.
        for slot in self._slots.values():
            slot.cleanup()
        self._slots.clear()
        self._order.clear()
        super().closeEvent(event)
