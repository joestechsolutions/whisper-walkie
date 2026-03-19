import os
import sys
import queue
import threading
import numpy as np
import sounddevice as sd
import pyperclip
from faster_whisper import WhisperModel
import scipy.signal
import flet as ft
import requests
import json
import time
import platform
import logging
import datetime

from platform_backend import get_backend

# Set up file logging so we can debug even when running via pythonw.exe
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "walkie.log")
logging.basicConfig(
    level=logging.WARNING,  # Suppress noisy Flet/httpx debug logs
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout) if sys.stdout else logging.FileHandler(LOG_FILE),
    ]
)
log = logging.getLogger("walkie")
log.setLevel(logging.DEBUG)  # Our own logger stays at DEBUG

# --- Configuration ---
DEFAULT_HOTKEY = 'right alt'
MODEL_SIZE = 'base'
SAMPLE_RATE = 16000
OLLAMA_URL = "http://localhost:11434/api"

# --- State Management ---
class AppState:
    def __init__(self):
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.device_sample_rate = 16000
        self.selected_device_index = None
        self.hotkey = DEFAULT_HOTKEY
        self.selected_ollama_model = None
        self.transcript_history = []
        self.status_text = "Ready"
        self.whisper_model = None
        self.gui_update_callback = None
        self.paste_target = None   # Snapshot of target at recording start
        self.key_handler = None    # Reference to the keyboard hook callback
        self.hook_ref = None       # Reference to the installed hook (for unhooking)

state = AppState()

# Initialize platform backend
backend = get_backend()

# --- Transcription Logic ---

def load_whisper():
    print(f"Loading '{MODEL_SIZE}' Whisper model...")
    device = "cpu" if platform.system() == "Darwin" else "cuda"
    compute_type = "float16" if device == "cuda" else "int8"

    try:
        state.whisper_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        print(f"Model loaded successfully on {device.upper()}.")
    except Exception as e:
        print(f"Failed to load on {device.upper()}, falling back to CPU. Error: {e}")
        state.whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        print("Model loaded successfully on CPU.")

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    if state.is_recording:
        state.audio_queue.put(indata.copy())

def start_recording(e=None):
    if not state.is_recording:
        log.info(">>> RECORDING STARTED")
        state.is_recording = True
        state.status_text = "Recording..."
        with state.audio_queue.mutex:
            state.audio_queue.queue.clear()
        # Drive the status card to "recording" state
        if state.gui_update_callback:
            state.gui_update_callback("recording")

def stop_recording(e=None):
    if state.is_recording:
        log.info(">>> RECORDING STOPPED")
        state.is_recording = False
        # DO NOT call gui_update_callback here - it steals focus from the user's window
        state.status_text = "Processing..."

        chunks = []
        while not state.audio_queue.empty():
            chunks.append(state.audio_queue.get())

        if not chunks:
            state.status_text = "No audio captured"
            if state.gui_update_callback: state.gui_update_callback("ready")
            return

        audio_data = np.concatenate(chunks, axis=0).flatten()

        if state.device_sample_rate != SAMPLE_RATE:
            num_samples = int(len(audio_data) * float(SAMPLE_RATE) / state.device_sample_rate)
            audio_data = scipy.signal.resample(audio_data, num_samples)

        # Signal processing state before launching the thread
        if state.gui_update_callback: state.gui_update_callback("processing")
        threading.Thread(target=process_audio, args=(audio_data,)).start()

def process_audio(audio_data):
    try:
        segments, info = state.whisper_model.transcribe(audio_data, beam_size=5)
        transcript = "".join([s.text for s in segments]).strip()

        if transcript:
            log.info(f"Transcribed: {transcript}")
            state.transcript_history.insert(0, transcript)
            if len(state.transcript_history) > 10: state.transcript_history.pop()

            # Paste into whatever window currently has focus.
            # Since we removed always_on_top, the user's target window stays focused.
            time.sleep(0.3)  # Wait for the Right Alt key-up to fully propagate

            fg_title = backend.get_foreground_window_title()
            log.info(f"Pasting to foreground window: {fg_title!r}")

            # On Windows, the keyboard hook intercepts synthetic keystrokes,
            # so we must remove it before typing and reinstall after.
            if backend.needs_unhook_for_injection:
                try:
                    backend.remove_key_hook()
                    log.info("Keyboard hook removed for typing")
                except Exception as ex:
                    log.warning(f"Failed to unhook keyboard: {ex}")
                time.sleep(0.05)

            # Platform-specific cleanup (dismisses Alt menus on Windows, no-op elsewhere)
            backend.pre_injection_cleanup()

            # Type text directly into the focused window
            backend.type_text(transcript + ' ')
            time.sleep(0.1)

            # Restore the keyboard hook if it was removed
            if backend.needs_unhook_for_injection:
                try:
                    if state.key_handler:
                        state.hook_ref = backend.reinstall_key_hook(state.key_handler)
                        log.info("Keyboard hook re-installed")
                except Exception as ex:
                    log.error(f"Failed to re-hook keyboard: {ex}")

            state.status_text = f"Typed: {transcript[:20]}..."
            # Update GUI with result AFTER typing is complete
            if state.gui_update_callback: state.gui_update_callback("result", transcript)
        else:
            state.status_text = "No speech detected"
            if state.gui_update_callback: state.gui_update_callback("ready")

    except Exception as e:
        state.status_text = f"Error: {str(e)}"
        log.error(f"process_audio error: {e}")
        if state.gui_update_callback: state.gui_update_callback("ready")


# --- Ollama API Integration ---

def get_ollama_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/tags", timeout=1)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
    except:
        pass
    return []


# ---------------------------------------------------------------------------
# Design tokens — single source of truth for every visual decision
# ---------------------------------------------------------------------------

class DS:
    """Design System tokens."""

    # Surface hierarchy (darkest -> lightest)
    BG_BASE        = "#0d0d14"   # true dark base — canvas behind everything
    BG_SURFACE     = "#13131f"   # main card/panel backgrounds
    BG_ELEVATED    = "#1a1a2e"   # raised panels, dropdowns
    BG_OVERLAY     = "#21213a"   # hover states, secondary controls

    # Brand palette — Indigo Spectrum
    PRIMARY        = "#6366f1"   # indigo-500 — primary actions, focus rings
    PRIMARY_DIM    = "#4338ca"   # indigo-700 — pressed states
    PRIMARY_GLOW   = "#818cf8"   # indigo-400 — highlights, glow edges
    ACCENT         = "#22d3ee"   # cyan-400 — accent dots, active states
    ACCENT_DIM     = "#0891b2"   # cyan-600 — accent pressed

    # State colors
    STATE_READY      = "#22d3ee"  # cyan — idle, ready
    STATE_RECORDING  = "#f43f5e"  # rose-500 — hot, active recording
    STATE_PROCESSING = "#f59e0b"  # amber-400 — thinking/spinning
    STATE_SUCCESS    = "#10b981"  # emerald-500 — result delivered

    # Typography
    TEXT_PRIMARY   = "#f1f5f9"   # slate-100
    TEXT_SECONDARY = "#94a3b8"   # slate-400
    TEXT_MUTED     = "#475569"   # slate-600
    TEXT_ACCENT    = "#818cf8"   # indigo-400

    # Border / divider
    BORDER         = "#1e1e3a"
    BORDER_BRIGHT  = "#2d2d54"

    # Radius tokens (applied via border_radius)
    RADIUS_SM  = 8
    RADIUS_MD  = 12
    RADIUS_LG  = 16
    RADIUS_XL  = 20

    # Spacing (used as padding/margin values)
    SP_XS  = 4
    SP_SM  = 8
    SP_MD  = 14
    SP_LG  = 20
    SP_XL  = 28


# ---------------------------------------------------------------------------
# Reusable micro-components
# ---------------------------------------------------------------------------

def _divider() -> ft.Container:
    return ft.Container(
        height=1,
        bgcolor=DS.BORDER,
        margin=ft.margin.symmetric(vertical=DS.SP_SM),
    )


def _section_label(text: str) -> ft.Text:
    return ft.Text(
        text.upper(),
        size=9,
        weight=ft.FontWeight.W_700,
        color=DS.TEXT_MUTED,
        letter_spacing=1.8,
    )


def _styled_dropdown(
    label: str,
    options: list,
    ref: ft.Ref,
    on_change=None,
    initial_value=None,
) -> ft.Container:
    """A branded dropdown with label and consistent styling.
    options: list of (key, text) tuples.
    """
    value = initial_value if initial_value is not None else (options[0][0] if options else None)
    dd = ft.Dropdown(
        ref=ref,
        options=[ft.DropdownOption(key=k, text=t) for k, t in options],
        on_select=on_change,
        value=value,
        bgcolor=DS.BG_ELEVATED,
        border_color=DS.BORDER_BRIGHT,
        focused_border_color=DS.PRIMARY,
        color=DS.TEXT_PRIMARY,
        text_size=13,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=DS.RADIUS_MD,
    )
    return ft.Column(
        spacing=DS.SP_XS,
        controls=[
            _section_label(label),
            dd,
        ],
    )


def _icon_button(icon, tooltip: str, on_click=None) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        icon_color=DS.TEXT_SECONDARY,
        icon_size=16,
        tooltip=tooltip,
        on_click=on_click,
        style=ft.ButtonStyle(
            overlay_color=DS.BG_OVERLAY,
            shape=ft.RoundedRectangleBorder(radius=DS.RADIUS_SM),
        ),
    )


# ---------------------------------------------------------------------------
# TranscriptionEntry — a single row in the history list
# ---------------------------------------------------------------------------

def _transcription_entry(
    text: str,
    timestamp: str,
    duration: str,
    index: int,
    on_copy=None,
) -> ft.Container:
    """Renders one transcription history row."""

    is_latest = (index == 0)
    accent_bar_color = DS.PRIMARY if is_latest else DS.BORDER_BRIGHT

    return ft.Container(
        bgcolor=DS.BG_ELEVATED if is_latest else DS.BG_SURFACE,
        border_radius=DS.RADIUS_MD,
        padding=ft.padding.symmetric(horizontal=DS.SP_MD, vertical=DS.SP_SM + 2),
        border=ft.border.all(1, DS.PRIMARY_GLOW if is_latest else DS.BORDER),
        margin=ft.margin.only(bottom=DS.SP_SM),
        content=ft.Row(
            spacing=DS.SP_MD,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                # Left accent bar
                ft.Container(
                    width=3,
                    height=48,
                    border_radius=2,
                    bgcolor=accent_bar_color,
                ),
                # Text block
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        ft.Text(
                            text,
                            size=13,
                            color=DS.TEXT_PRIMARY if is_latest else DS.TEXT_SECONDARY,
                            weight=ft.FontWeight.W_400,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            spacing=DS.SP_SM,
                            controls=[
                                ft.Text(timestamp, size=10, color=DS.TEXT_MUTED),
                                ft.Container(
                                    width=3, height=3,
                                    border_radius=2,
                                    bgcolor=DS.TEXT_MUTED,
                                ),
                                ft.Text(duration, size=10, color=DS.TEXT_MUTED),
                            ],
                        ),
                    ],
                ),
                # Copy icon (right side)
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY_ROUNDED,
                    icon_color=DS.TEXT_MUTED,
                    icon_size=14,
                    tooltip="Copy to clipboard",
                    on_click=on_copy,
                    style=ft.ButtonStyle(
                        overlay_color=DS.BG_OVERLAY,
                        shape=ft.RoundedRectangleBorder(radius=DS.RADIUS_SM),
                    ),
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Status card — the hero section of the UI
# ---------------------------------------------------------------------------

class StatusCard:
    """
    Builds the status hero card and exposes update methods
    to transition between Ready / Recording / Processing / Result states.
    """

    # State descriptors
    STATES = {
        "ready": {
            "label":     "Ready",
            "sublabel":  "Hold Right Alt to speak",
            "color":     DS.STATE_READY,
            "icon":      ft.Icons.MIC_NONE_ROUNDED,
            "badge_bg":  "#0a2a2e",
        },
        "recording": {
            "label":     "Recording",
            "sublabel":  "Release Right Alt when done",
            "color":     DS.STATE_RECORDING,
            "icon":      ft.Icons.MIC_ROUNDED,
            "badge_bg":  "#2a0a14",
        },
        "processing": {
            "label":     "Processing",
            "sublabel":  "Transcribing audio...",
            "color":     DS.STATE_PROCESSING,
            "icon":      ft.Icons.GRAPHIC_EQ_ROUNDED,
            "badge_bg":  "#2a1a00",
        },
        "result": {
            "label":     "Typed",
            "sublabel":  "Text inserted into active window",
            "color":     DS.STATE_SUCCESS,
            "icon":      ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            "badge_bg":  "#0a2a1a",
        },
    }

    def __init__(self):
        self._state_key = "ready"

        # Refs for live mutation
        self._outer_ring_ref   = ft.Ref()
        self._mid_ring_ref     = ft.Ref()
        self._dot_ref          = ft.Ref()
        self._mic_icon_ref     = ft.Ref()
        self._badge_ref        = ft.Ref()
        self._label_ref        = ft.Ref()
        self._sublabel_ref     = ft.Ref()
        self._result_row_ref   = ft.Ref()
        self._result_text_ref  = ft.Ref()
        self._live_timer_ref   = ft.Ref()

        # Live recording timer state
        self._timer_thread = None
        self._timer_running = False
        self._elapsed_sec = 0

    # ---- Build ----

    def build(self) -> ft.Container:
        s = self.STATES["ready"]

        # Concentric rings
        outer_ring = ft.Container(
            ref=self._outer_ring_ref,
            width=80, height=80,
            border_radius=40,
            bgcolor=s["color"],
            opacity=0.08,
        )
        mid_ring = ft.Container(
            ref=self._mid_ring_ref,
            width=60, height=60,
            border_radius=30,
            bgcolor=s["color"],
            opacity=0.18,
        )
        core_dot = ft.Container(
            ref=self._dot_ref,
            width=42, height=42,
            border_radius=21,
            bgcolor=s["color"],
            opacity=0.95,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(
                ref=self._mic_icon_ref,
                icon=s["icon"],
                color=ft.Colors.WHITE,
                size=20,
            ),
        )
        ring_stack = ft.Stack(
            width=80, height=80,
            controls=[
                ft.Container(width=80, height=80, alignment=ft.Alignment(0, 0), content=outer_ring),
                ft.Container(width=80, height=80, alignment=ft.Alignment(0, 0), content=mid_ring),
                ft.Container(width=80, height=80, alignment=ft.Alignment(0, 0), content=core_dot),
            ],
        )

        # State badge pill
        badge = ft.Container(
            ref=self._badge_ref,
            bgcolor=s["badge_bg"],
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            border=ft.border.all(1, s["color"] + "44"),
            content=ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.Container(
                        width=6, height=6,
                        border_radius=3,
                        bgcolor=s["color"],
                    ),
                    ft.Text(
                        ref=self._label_ref,
                        value=s["label"],
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=s["color"],
                    ),
                ],
            ),
        )

        # Live timer (hidden until recording)
        live_timer = ft.Text(
            ref=self._live_timer_ref,
            value="0:00",
            size=11,
            color=DS.STATE_RECORDING,
            weight=ft.FontWeight.W_500,
            visible=False,
        )

        sublabel = ft.Text(
            ref=self._sublabel_ref,
            value=s["sublabel"],
            size=12,
            color=DS.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )

        # Last result preview row (hidden by default)
        result_row = ft.Container(
            ref=self._result_row_ref,
            visible=False,
            bgcolor=DS.BG_ELEVATED,
            border_radius=DS.RADIUS_MD,
            padding=ft.padding.symmetric(horizontal=DS.SP_MD, vertical=DS.SP_SM),
            border=ft.border.all(1, DS.STATE_SUCCESS + "44"),
            margin=ft.margin.only(top=DS.SP_SM),
            content=ft.Row(
                spacing=DS.SP_SM,
                controls=[
                    ft.Icon(
                        icon=ft.Icons.FORMAT_QUOTE_ROUNDED,
                        color=DS.STATE_SUCCESS,
                        size=14,
                    ),
                    ft.Text(
                        ref=self._result_text_ref,
                        value="",
                        size=12,
                        color=DS.TEXT_PRIMARY,
                        italic=True,
                        expand=True,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )

        return ft.Container(
            bgcolor=DS.BG_SURFACE,
            border_radius=DS.RADIUS_LG,
            border=ft.border.all(1, DS.BORDER),
            padding=ft.padding.symmetric(horizontal=DS.SP_LG, vertical=DS.SP_XL),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=DS.SP_MD,
                controls=[
                    ring_stack,
                    badge,
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[sublabel, live_timer],
                    ),
                    result_row,
                ],
            ),
        )

    # ---- State transitions ----

    def _apply_color(self, color: str, badge_bg: str, label: str, sublabel: str, icon, page):
        """Mutate all color-bearing refs in one pass."""
        # Rings
        if self._outer_ring_ref.current:
            self._outer_ring_ref.current.bgcolor = color
        if self._mid_ring_ref.current:
            self._mid_ring_ref.current.bgcolor = color
        if self._dot_ref.current:
            self._dot_ref.current.bgcolor = color
        # Icon
        if self._mic_icon_ref.current:
            self._mic_icon_ref.current.icon = icon
        # Badge
        if self._badge_ref.current:
            self._badge_ref.current.bgcolor = badge_bg
            self._badge_ref.current.border = ft.border.all(1, color + "44")
            # The badge dot and text are inside badge.content.controls
            row = self._badge_ref.current.content
            if row and len(row.controls) >= 2:
                row.controls[0].bgcolor = color  # dot
                row.controls[1].color   = color  # text
        if self._label_ref.current:
            self._label_ref.current.value = label
        if self._sublabel_ref.current:
            self._sublabel_ref.current.value = sublabel

    def transition(self, state_key: str, result_text: str = "", page=None):
        """
        Call this from update_ui() to drive state transitions.
        state_key: "ready" | "recording" | "processing" | "result"
        """
        if state_key not in self.STATES:
            return
        self._state_key = state_key
        s = self.STATES[state_key]

        self._apply_color(
            color=s["color"],
            badge_bg=s["badge_bg"],
            label=s["label"],
            sublabel=s["sublabel"],
            icon=s["icon"],
            page=page,
        )

        # Timer visibility
        is_recording = (state_key == "recording")
        if self._live_timer_ref.current:
            self._live_timer_ref.current.visible = is_recording

        # Result preview
        if self._result_row_ref.current:
            self._result_row_ref.current.visible = (state_key == "result" and bool(result_text))
        if self._result_text_ref.current and result_text:
            self._result_text_ref.current.value = f'"{result_text}"'

        # Recording timer thread
        if is_recording:
            self._start_timer(page)
        else:
            self._stop_timer()

        if page:
            page.update()

    def _start_timer(self, page):
        self._stop_timer()
        self._elapsed_sec = 0
        self._timer_running = True

        def _tick():
            while self._timer_running:
                self._elapsed_sec += 1
                m, s = divmod(self._elapsed_sec, 60)
                label = f"{m}:{s:02d}"
                if self._live_timer_ref.current:
                    self._live_timer_ref.current.value = label
                if page:
                    try:
                        page.update()
                    except Exception:
                        break
                threading.Event().wait(1.0)

        self._timer_thread = threading.Thread(target=_tick, daemon=True)
        self._timer_thread.start()

    def _stop_timer(self):
        self._timer_running = False
        self._elapsed_sec = 0


# ---------------------------------------------------------------------------
# Custom GUI (Flet 0.81.0 Compatible) — Premium Design
# ---------------------------------------------------------------------------

def main_gui(page: ft.Page):
    """Main GUI entry point — integrates premium design with live backend state."""

    # ---- Window configuration ----
    page.window.width       = 450
    page.window.height      = 720
    page.window.min_width   = 420
    page.window.min_height  = 600
    page.window.resizable   = True
    page.window.always_on_top = False
    page.title              = "Whisper Walkie"

    # ---- Page theme ----
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor    = DS.BG_BASE
    page.padding    = 0
    page.fonts      = {}

    page.theme = ft.Theme(
        color_scheme_seed=DS.PRIMARY,
        use_material3=True,
        visual_density=ft.VisualDensity.COMPACT,
    )

    # ---- Status card ----
    status_card = StatusCard()

    # ---- Transcription log (live, starts empty) ----
    transcription_log: list[dict] = []

    # ---- History panel ref — for in-place refresh ----
    history_panel_ref = ft.Ref()

    # ---- Pin button refs — for toggling always-on-top ----
    pin_icon_ref = ft.Ref()
    pin_text_ref = ft.Ref()
    pin_chip_ref = ft.Ref()
    _pinned = [False]  # mutable flag in closure

    # ---- Footer hotkey chip ref — updates when hotkey changes ----
    footer_chip_ref = ft.Ref()

    # ----------------------------------------------------------------
    # History panel builder — called on every update
    # ----------------------------------------------------------------

    def _build_history_panel(entries: list) -> ft.Container:
        """Rebuild the full history panel container."""
        count_badge = ft.Container(
            bgcolor=DS.BG_ELEVATED,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=7, vertical=2),
            content=ft.Text(
                str(len(entries)),
                size=10,
                color=DS.TEXT_MUTED,
                weight=ft.FontWeight.W_600,
            ),
        )

        def handle_clear(e):
            state.transcript_history.clear()
            transcription_log.clear()
            _refresh_history()

        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=DS.SP_SM,
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.HISTORY_ROUNDED,
                            color=DS.TEXT_MUTED,
                            size=14,
                        ),
                        ft.Text(
                            "Recent Transcriptions",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=DS.TEXT_PRIMARY,
                        ),
                        count_badge,
                    ],
                ),
                ft.TextButton(
                    text="Clear",
                    on_click=handle_clear,
                    style=ft.ButtonStyle(
                        color=DS.TEXT_MUTED,
                        overlay_color=DS.BG_OVERLAY,
                    ),
                ),
            ],
        )

        if not entries:
            list_content = ft.Container(
                height=80,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.HISTORY_ROUNDED,
                            color=DS.TEXT_MUTED,
                            size=24,
                        ),
                        ft.Text(
                            "No transcriptions yet",
                            size=12,
                            color=DS.TEXT_MUTED,
                        ),
                    ],
                ),
            )
        else:
            def _make_copy_handler(entry_text: str):
                def _copy(e):
                    pyperclip.copy(entry_text)
                return _copy

            rows = [
                _transcription_entry(
                    text=e.get("text", ""),
                    timestamp=e.get("timestamp", ""),
                    duration=e.get("duration", ""),
                    index=i,
                    on_copy=_make_copy_handler(e.get("text", "")),
                )
                for i, e in enumerate(entries[:10])
            ]
            list_content = ft.ListView(
                controls=rows,
                spacing=0,
                height=220,
                padding=ft.padding.only(right=DS.SP_XS),
            )

        return ft.Container(
            bgcolor=DS.BG_SURFACE,
            border_radius=DS.RADIUS_LG,
            border=ft.border.all(1, DS.BORDER),
            padding=ft.padding.all(DS.SP_LG),
            content=ft.Column(
                spacing=DS.SP_SM,
                controls=[
                    header_row,
                    _divider(),
                    list_content,
                ],
            ),
        )

    def _refresh_history():
        """Swap history panel content and call page.update()."""
        if history_panel_ref.current:
            history_panel_ref.current.content = _build_history_panel(transcription_log)
            page.update()

    # ----------------------------------------------------------------
    # Settings panel — wired to real backend state
    # ----------------------------------------------------------------

    hotkey_ref = ft.Ref()
    model_ref  = ft.Ref()
    device_ref = ft.Ref()

    HOTKEY_OPTIONS_KEYS = ['right alt', 'scroll lock', 'pause', 'f13', 'f14', 'insert', 'right ctrl']
    hotkey_options = [(k, k.upper()) for k in HOTKEY_OPTIONS_KEYS]

    # Ollama models from live API
    ollama_models = get_ollama_models()
    if ollama_models:
        model_options = [(m, m) for m in ollama_models]
        state.selected_ollama_model = ollama_models[0]
    else:
        model_options = [("none", "No models found")]

    # Audio input devices from sounddevice
    try:
        all_devices = sd.query_devices()
        audio_input_devices = [
            (str(i), f"{d['name']} ({int(d['default_samplerate'])} Hz)")
            for i, d in enumerate(all_devices)
            if d['max_input_channels'] > 0
        ]
    except Exception as _dev_err:
        log.warning(f"Could not enumerate audio devices: {_dev_err}")
        audio_input_devices = [("default", "System Default")]

    def handle_hotkey_change(e):
        new_key = hotkey_ref.current.value if hotkey_ref.current else None
        if new_key:
            state.hotkey = new_key
            # Update footer chip label
            if footer_chip_ref.current:
                content = footer_chip_ref.current.content
                if content and hasattr(content, 'value'):
                    content.value = new_key.upper()
            page.update()
            log.info(f"Hotkey changed to: {new_key}")

    def handle_model_change(e):
        new_model = model_ref.current.value if model_ref.current else None
        if new_model and new_model != "none":
            state.selected_ollama_model = new_model
            log.info(f"AI model changed to: {new_model}")

    def handle_device_change(e):
        new_device_str = device_ref.current.value if device_ref.current else None
        if new_device_str and new_device_str != "default":
            try:
                idx = int(new_device_str)
                state.selected_device_index = idx
                devices = sd.query_devices()
                state.device_sample_rate = int(devices[idx]['default_samplerate'])
                log.info(f"Audio device changed to index {idx}, sample rate {state.device_sample_rate}")
            except (ValueError, IndexError) as ex:
                log.warning(f"Device change error: {ex}")

    # Find initial device index string for the dropdown value
    initial_device_value = None
    if state.selected_device_index is not None and audio_input_devices:
        initial_device_value = str(state.selected_device_index)
        # Verify this index is actually in the options list
        valid_keys = [k for k, _ in audio_input_devices]
        if initial_device_value not in valid_keys:
            initial_device_value = audio_input_devices[0][0] if audio_input_devices else None

    settings_panel = ft.Container(
        bgcolor=DS.BG_SURFACE,
        border_radius=DS.RADIUS_LG,
        border=ft.border.all(1, DS.BORDER),
        padding=ft.padding.all(DS.SP_LG),
        content=ft.Column(
            spacing=DS.SP_MD,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.TUNE_ROUNDED,
                            color=DS.TEXT_MUTED,
                            size=14,
                        ),
                        ft.Text(
                            "Settings",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=DS.TEXT_PRIMARY,
                        ),
                    ],
                    spacing=DS.SP_SM,
                ),
                _divider(),
                _styled_dropdown(
                    "Push-to-Talk Hotkey",
                    hotkey_options,
                    hotkey_ref,
                    on_change=handle_hotkey_change,
                    initial_value=state.hotkey,
                ),
                _styled_dropdown(
                    "AI Model",
                    model_options,
                    model_ref,
                    on_change=handle_model_change,
                    initial_value=model_options[0][0] if model_options else None,
                ),
                _styled_dropdown(
                    "Microphone",
                    audio_input_devices if audio_input_devices else [("default", "System Default")],
                    device_ref,
                    on_change=handle_device_change,
                    initial_value=initial_device_value,
                ),
            ],
        ),
    )

    # ----------------------------------------------------------------
    # Header — with working Pin button
    # ----------------------------------------------------------------

    def handle_pin_toggle(e):
        _pinned[0] = not _pinned[0]
        page.window.always_on_top = _pinned[0]
        # Update pin icon/color to reflect state
        if pin_icon_ref.current:
            pin_icon_ref.current.icon = (
                ft.Icons.PUSH_PIN_ROUNDED if _pinned[0] else ft.Icons.PUSH_PIN_OUTLINED
            )
            pin_icon_ref.current.color = DS.PRIMARY if _pinned[0] else DS.TEXT_MUTED
        if pin_text_ref.current:
            pin_text_ref.current.color = DS.PRIMARY if _pinned[0] else DS.TEXT_MUTED
        if pin_chip_ref.current:
            pin_chip_ref.current.bgcolor = (DS.BG_ELEVATED if not _pinned[0] else DS.PRIMARY_DIM)
        page.update()

    pin_chip = ft.Container(
        ref=pin_chip_ref,
        bgcolor=DS.BG_ELEVATED,
        border_radius=14,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border=ft.border.all(1, DS.BORDER_BRIGHT),
        tooltip="Toggle always-on-top",
        on_click=handle_pin_toggle,
        content=ft.Row(
            spacing=5,
            tight=True,
            controls=[
                ft.Icon(
                    ref=pin_icon_ref,
                    icon=ft.Icons.PUSH_PIN_OUTLINED,
                    color=DS.TEXT_MUTED,
                    size=12,
                ),
                ft.Text(
                    ref=pin_text_ref,
                    value="Pin",
                    size=11,
                    color=DS.TEXT_MUTED,
                ),
            ],
        ),
    )

    minimize_btn = _icon_button(
        ft.Icons.REMOVE_ROUNDED,
        "Minimize",
        on_click=lambda _: setattr(page.window, "minimized", True) or page.update(),
    )

    wordmark = ft.Row(
        spacing=DS.SP_SM,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=34, height=34,
                border_radius=10,
                bgcolor=DS.PRIMARY,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(
                    icon=ft.Icons.SPATIAL_AUDIO_ROUNDED,
                    color=ft.Colors.WHITE,
                    size=18,
                ),
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    color=DS.PRIMARY + "55",
                    offset=ft.Offset(0, 4),
                ),
            ),
            ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        "Whisper Walkie",
                        size=15,
                        weight=ft.FontWeight.W_700,
                        color=DS.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "v1.0",
                        size=10,
                        color=DS.TEXT_MUTED,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
            ),
        ],
    )

    header = ft.Container(
        bgcolor=DS.BG_SURFACE,
        border_radius=DS.RADIUS_LG,
        border=ft.border.all(1, DS.BORDER),
        padding=ft.padding.symmetric(horizontal=DS.SP_LG, vertical=DS.SP_MD),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                wordmark,
                ft.Row(
                    spacing=DS.SP_XS,
                    controls=[pin_chip, minimize_btn],
                ),
            ],
        ),
    )

    # ----------------------------------------------------------------
    # Footer
    # ----------------------------------------------------------------

    footer_chip = ft.Container(
        ref=footer_chip_ref,
        bgcolor=DS.BG_ELEVATED,
        border_radius=DS.RADIUS_SM,
        padding=ft.padding.symmetric(horizontal=DS.SP_SM, vertical=DS.SP_XS),
        border=ft.border.all(1, DS.BORDER_BRIGHT),
        content=ft.Text(
            state.hotkey.upper(),
            size=11,
            color=DS.TEXT_ACCENT,
            weight=ft.FontWeight.W_600,
            font_family="monospace",
        ),
    )

    footer = ft.Container(
        bgcolor=DS.BG_SURFACE,
        border_radius=DS.RADIUS_LG,
        border=ft.border.all(1, DS.BORDER),
        padding=ft.padding.symmetric(horizontal=DS.SP_LG, vertical=DS.SP_MD),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=DS.SP_SM,
            controls=[
                ft.Text("Hold", size=12, color=DS.TEXT_MUTED),
                footer_chip,
                ft.Text("anywhere to transcribe", size=12, color=DS.TEXT_MUTED),
            ],
        ),
    )

    # ----------------------------------------------------------------
    # Assemble the layout
    # ----------------------------------------------------------------

    status_panel   = status_card.build()
    history_panel  = ft.Container(
        ref=history_panel_ref,
        content=_build_history_panel(transcription_log),
    )

    body = ft.ListView(
        scroll_mode=ft.ScrollMode.ADAPTIVE,
        spacing=DS.SP_SM,
        padding=ft.padding.symmetric(horizontal=DS.SP_LG, vertical=DS.SP_MD),
        controls=[
            status_panel,
            history_panel,
            settings_panel,
        ],
        expand=True,
    )

    root = ft.Column(
        spacing=0,
        expand=True,
        controls=[
            ft.Container(
                content=header,
                padding=ft.padding.only(
                    left=DS.SP_LG,
                    right=DS.SP_LG,
                    top=DS.SP_LG,
                    bottom=0,
                ),
            ),
            ft.Container(content=body, expand=True),
            ft.Container(
                content=footer,
                padding=ft.padding.only(
                    left=DS.SP_LG,
                    right=DS.SP_LG,
                    top=0,
                    bottom=DS.SP_LG,
                ),
            ),
        ],
    )

    page.add(root)
    page.update()

    # ----------------------------------------------------------------
    # Wire up the gui_update_callback to drive the status card
    # ----------------------------------------------------------------

    def update_ui(ui_state: str, transcription_text: str = ""):
        """
        Called from background threads to update the UI.
        ui_state: "ready" | "recording" | "processing" | "result"
        """
        if ui_state == "result" and transcription_text:
            now = datetime.datetime.now()
            entry = {
                "text":      transcription_text,
                "timestamp": now.strftime("%-I:%M %p") if platform.system() != "Windows"
                             else now.strftime("%#I:%M %p"),
                "duration":  "",
            }
            transcription_log.insert(0, entry)
            if len(transcription_log) > 10:
                transcription_log.pop()

        # Transition status card (handles page.update() internally)
        status_card.transition(ui_state, transcription_text, page)

        # Refresh history panel when a result arrives or history is cleared
        if ui_state in ("result", "ready"):
            _refresh_history()

    state.gui_update_callback = update_ui

    # ----------------------------------------------------------------
    # Device Setup — auto-detect audio input
    # ----------------------------------------------------------------

    try:
        devices = sd.query_devices()
        input_device_found = False
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                if not input_device_found:
                    state.selected_device_index = i
                    state.device_sample_rate = int(d['default_samplerate'])
                    input_device_found = True

                # High priority devices
                if "Realtek" in d['name'] or "Astro" in d['name']:
                    state.selected_device_index = i
                    state.device_sample_rate = int(d['default_samplerate'])
                    break
    except Exception as e:
        log.warning(f"Device setup error: {e}")

    # ----------------------------------------------------------------
    # Background Listener Startup
    # ----------------------------------------------------------------

    def run_transcription():
        load_whisper()

        # Build the set of expected key names and scan codes for the hotkey
        _expected_names = backend.get_hotkey_names(state.hotkey)
        _expected_scans = backend.get_hotkey_scan_codes(state.hotkey)

        log.info(f"Hotkey config: names={_expected_names}, scans={_expected_scans}")

        _key_log_count = [0]

        def on_key_event(event_type, key_name, scan_code):
            """Normalized key event handler from platform backend."""
            # Log first 20 key events for debugging
            if _key_log_count[0] < 20:
                log.debug(f"KEY: name={key_name!r} scan={scan_code} type={event_type}")
                _key_log_count[0] += 1
                if _key_log_count[0] == 20:
                    log.debug("(throttling key logging after 20 events)")

            matched = key_name in _expected_names or scan_code in _expected_scans

            if matched:
                if event_type == 'down' and not state.is_recording:
                    log.info(f"HOTKEY DOWN: name={key_name!r} scan={scan_code}")
                    start_recording()
                elif event_type == 'up' and state.is_recording:
                    log.info(f"HOTKEY UP: name={key_name!r} scan={scan_code}")
                    stop_recording()

        try:
            state.key_handler = on_key_event
            state.hook_ref = backend.install_key_hook(on_key_event)
            log.info("Keyboard hook installed successfully")
        except Exception as e:
            print(f"Hotkey initialization error: {e}")
            state.status_text = "Hotkey Init Error"
            if state.gui_update_callback: state.gui_update_callback("ready")

        # Audio stream setup (unchanged)
        log.info(f"Audio device index: {state.selected_device_index}, sample rate: {state.device_sample_rate}")
        try:
            if state.selected_device_index is not None:
                stream = sd.InputStream(
                    device=state.selected_device_index,
                    samplerate=state.device_sample_rate,
                    channels=1,
                    callback=audio_callback,
                    dtype='float32'
                )
                with stream:
                    while True:
                        time.sleep(0.1)
        except Exception as e:
            print(f"Audio stream error: {e}")

    threading.Thread(target=run_transcription, daemon=True).start()


if __name__ == "__main__":
    ft.run(main_gui)
