from __future__ import annotations
import calendar
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QDate, QTime, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame, QMenu,
    QDialog, QDialogButtonBox, QLineEdit, QTextEdit, QDateEdit, QTimeEdit,
    QCheckBox, QFormLayout, QFileDialog, QMessageBox, QSlider, QColorDialog,
    QComboBox, QSpinBox, QSystemTrayIcon
)

from config import load_config, save_config, APP_DIR
from google_calendar import GoogleCalendarService

APP_NAME = "Gcalcal"


def resource_path(relative_path: str) -> Path:
    """Resolve bundled assets in both normal Python and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path

STYLE = r"""
* { font-family: 'Yu Gothic UI', 'Meiryo UI', sans-serif; }
QMainWindow { background: transparent; color: #F3F6FA; }
QDialog { background: #161B24; color: #F3F6FA; }
QDialog QLabel { color: #F3F6FA; }
QDialog QLabel#muted { color: #9BA8B8; }
QDialog QCheckBox { color: #F3F6FA; spacing: 8px; }
QDialog QGroupBox { color: #F3F6FA; }
QDialogButtonBox QPushButton { min-width: 76px; min-height: 30px; font-weight: 600; }
QWidget#root { background: rgba(22, 27, 36, 238); color: #F3F6FA; border-radius: 18px; }
QFrame#panel { background: rgba(34, 41, 53, 225); border: 1px solid rgba(255,255,255,22); border-radius: 15px; }
QLabel#monthTitle { font-size: 25px; font-weight: 700; color: #F7FAFC; }
QLabel#yearTitle { color: #9BA8B8; font-size: 13px; }
QLabel#muted { color: #9BA8B8; }
QPushButton, QDialogButtonBox QPushButton {
    background: #303A49;
    border: 1px solid #526174;
    border-radius: 7px;
    padding: 7px 12px;
    color: #F3F6FA;
}
QPushButton:hover, QDialogButtonBox QPushButton:hover {
    background: #3B665E;
    border-color: #72D6B4;
    color: #FFFFFF;
}
QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
    background: #28564D;
    border-color: #72D6B4;
    color: #FFFFFF;
}
QPushButton:disabled, QDialogButtonBox QPushButton:disabled {
    background: #252D39;
    border-color: #394555;
    color: #9BA8B8;
}
QPushButton#nav { font-size: 18px; font-weight: 600; min-width: 30px; padding: 4px; }
QPushButton#day { min-height: 39px; border: none; background: transparent; padding: 2px; }
QPushButton#day:hover { background: rgba(255,255,255,20); }
QPushButton#day[otherMonth="true"] { color: #667181; }
QPushButton#day[sunday="true"] { color: #FF8D98; }
QPushButton#day[saturday="true"] { color: #83B8FF; }
QPushButton#day[holiday="true"] { color: #FF8D98; }
QPushButton#day[today="true"] { background: #72D6B4; color: #15221F; border-radius: 10px; font-weight: 800; }
QPushButton#day[selected="true"] { border: 2px solid #72D6B4; border-radius: 10px; }
QPushButton#day[hasEvents="true"] { font-weight: 800; }
QListWidget { background: transparent; border: none; outline: none; font-size: 12px; }
QListWidget::item { min-height: 18px; padding: 3px 7px; border-bottom: 1px solid rgba(255,255,255,13); }
QListWidget::item:selected { background: rgba(114,214,180,35); border-radius: 7px; }
QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox, QSpinBox { background: #252D39; border: 1px solid #465365; border-radius: 7px; padding: 7px; color: #F3F6FA; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 5px; background: #465365; border-radius: 2px; }
QSlider::handle:horizontal { background: #72D6B4; width: 14px; margin: -5px 0; border-radius: 7px; }
QToolTip { background: #202936; color: white; border: 1px solid #596779; padding: 5px; }
"""


class EventDialog(QDialog):
    def __init__(self, selected: date, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#F3F6FA"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#F3F6FA"))
        self.setPalette(palette)
        self.setWindowTitle("予定を追加")
        self.setMinimumWidth(370)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit()
        self.title.setPlaceholderText("予定のタイトル")
        self.day = QDateEdit(QDate(selected.year, selected.month, selected.day))
        self.day.setCalendarPopup(True)
        self.all_day = QCheckBox("終日")
        self.start = QTimeEdit(); self.start.setTime(QTime(9, 0))
        self.end = QTimeEdit(); self.end.setTime(QTime(10, 0))
        self.description = QTextEdit(); self.description.setMaximumHeight(90)
        form.addRow("タイトル", self.title)
        form.addRow("日付", self.day)
        form.addRow("開始", self.start)
        form.addRow("終了", self.end)
        form.addRow("", self.all_day)
        form.addRow("説明", self.description)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.all_day.toggled.connect(lambda checked: (self.start.setDisabled(checked), self.end.setDisabled(checked)))

    def values(self):
        d = self.day.date().toPython()
        start = datetime.combine(d, self.start.time().toPython())
        end = datetime.combine(d, self.end.time().toPython())
        if end <= start and not self.all_day.isChecked():
            end += timedelta(days=1)
        return self.title.text().strip(), start, end, self.description.toPlainText(), self.all_day.isChecked()


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#F3F6FA"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#F3F6FA"))
        self.setPalette(palette)
        self.setWindowTitle("Gcalcal 設定")
        self.setMinimumWidth(470)
        self.config = config.copy()
        root = QVBoxLayout(self); form = QFormLayout()
        self.credentials = QLineEdit(config.get("credentials_file", ""))
        browse = QPushButton("参照…")
        browse.clicked.connect(self.choose_credentials)
        credrow = QHBoxLayout(); credrow.addWidget(self.credentials); credrow.addWidget(browse)
        credwrap = QWidget(); credwrap.setLayout(credrow)
        self.calendar_id = QLineEdit(config.get("calendar_id", "primary"))
        self.all_calendars = QCheckBox("登録されているすべてのカレンダーの予定を表示")
        self.all_calendars.setChecked(config.get("all_calendars", True))
        self.holiday_id = QLineEdit(config.get("holiday_calendar_id", ""))
        self.opacity = QSlider(Qt.Horizontal); self.opacity.setRange(30, 100); self.opacity.setValue(int(float(config.get("opacity", .94))*100))
        self.opacity_label = QLabel(f"{self.opacity.value()}%")
        self.opacity.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        op_row = QHBoxLayout(); op_row.addWidget(self.opacity, 1); op_row.addWidget(self.opacity_label)
        op_wrap = QWidget(); op_wrap.setLayout(op_row)
        self.top = QCheckBox("常に最前面に表示"); self.top.setChecked(config.get("always_on_top", True))
        self.frameless = QCheckBox("タイトルバーを隠す（ドラッグで移動）"); self.frameless.setChecked(config.get("frameless", True))
        self.agenda = QCheckBox("予定一覧を表示"); self.agenda.setChecked(config.get("show_agenda", True))
        self.refresh = QSpinBox(); self.refresh.setRange(1, 180); self.refresh.setValue(int(config.get("refresh_minutes", 15))); self.refresh.setSuffix(" 分")
        self.accent = QLineEdit(config.get("accent_color", "#72D6B4"))
        color_btn = QPushButton("色を選択")
        color_btn.clicked.connect(self.choose_color)
        colorrow = QHBoxLayout(); colorrow.addWidget(self.accent); colorrow.addWidget(color_btn)
        colorwrap = QWidget(); colorwrap.setLayout(colorrow)
        form.addRow("OAuthクライアントJSON", credwrap)
        form.addRow("予定カレンダーID（個別指定時）", self.calendar_id)
        root.addWidget(self.all_calendars)
        form.addRow("祝日カレンダーID（任意）", self.holiday_id)
        form.addRow("ウィンドウ透過率", op_wrap)
        form.addRow("アクセントカラー", colorwrap)
        form.addRow("自動更新", self.refresh)
        root.addLayout(form)
        root.addWidget(self.top); root.addWidget(self.frameless); root.addWidget(self.agenda)
        hint = QLabel("※ Google Cloud ConsoleでCalendar APIを有効化し、デスクトップアプリ用OAuthクライアントを作成してください。")
        hint.setWordWrap(True); hint.setObjectName("muted"); root.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def choose_credentials(self):
        path, _ = QFileDialog.getOpenFileName(self, "OAuthクライアントJSONを選択", "", "JSON (*.json)")
        if path: self.credentials.setText(path)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.accent.text()), self)
        if color.isValid(): self.accent.setText(color.name())

    def values(self):
        return {
            "credentials_file": self.credentials.text().strip(),
            "calendar_id": self.calendar_id.text().strip() or "primary",
            "all_calendars": self.all_calendars.isChecked(),
            "holiday_calendar_id": self.holiday_id.text().strip(),
            "opacity": self.opacity.value()/100,
            "always_on_top": self.top.isChecked(),
            "frameless": self.frameless.isChecked(),
            "show_agenda": self.agenda.isChecked(),
            "refresh_minutes": self.refresh.value(),
            "accent_color": self.accent.text().strip() or "#72D6B4",
        }


class GcalcalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.service = GoogleCalendarService(self.config.get("credentials_file", ""))
        self.current = date.today().replace(day=1)
        self.selected = date.today()
        self.events: list[dict] = []
        self.holidays: dict[date, str] = {}
        self._drag_pos = None
        self._build_ui()
        # _apply_window_settings() calls show(), which immediately triggers showEvent().
        # Therefore this guard MUST exist before _apply_window_settings().
        self._startup_refresh_scheduled = False
        self._apply_window_settings()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(int(self.config.get("refresh_minutes", 15))*60*1000)
        self.render_calendar()

    def showEvent(self, event):
        super().showEvent(event)
        # Start the first calendar fetch only after the native window is visible.
        # Some Windows/Qt combinations can lose the first QListWidget paint if
        # data is populated while the top-level window is still being created.
        if not self._startup_refresh_scheduled:
            self._startup_refresh_scheduled = True
            self.agenda_list.clear()
            loading_item = QListWidgetItem("Googleカレンダーの予定を読み込み中…")
            loading_item.setForeground(QColor("#9BA8B8"))
            self.agenda_list.addItem(loading_item)
            QTimer.singleShot(300, self._startup_refresh)

    def _startup_refresh(self):
        self.refresh_data(show_errors=False)
        self.render_agenda()
        self.agenda_list.setVisible(bool(self.config.get("show_agenda", True)))
        self.agenda_list.doItemsLayout()
        self.agenda_list.viewport().update()
        self.agenda_list.repaint()

    def _build_ui(self):
        self.setWindowTitle("Gcalcal")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(380, 480)
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(15, 13, 15, 13); outer.setSpacing(10)
        top = QHBoxLayout()
        titlebox = QVBoxLayout(); titlebox.setSpacing(0)
        self.month_label = QLabel(); self.month_label.setObjectName("monthTitle")
        self.year_label = QLabel(); self.year_label.setObjectName("yearTitle")
        titlebox.addWidget(self.month_label); titlebox.addWidget(self.year_label)
        top.addLayout(titlebox); top.addStretch()
        self.prev_btn = QPushButton("‹"); self.prev_btn.setObjectName("nav"); self.prev_btn.clicked.connect(lambda: self.shift_month(-1))
        self.next_btn = QPushButton("›"); self.next_btn.setObjectName("nav"); self.next_btn.clicked.connect(lambda: self.shift_month(1))
        self.today_btn = QPushButton("今日"); self.today_btn.clicked.connect(self.go_today)
        self.refresh_btn = QPushButton("⟳"); self.refresh_btn.setToolTip("Googleカレンダーを更新"); self.refresh_btn.clicked.connect(self.refresh_data)
        self.menu_btn = QPushButton("⋯"); self.menu_btn.setToolTip("設定・操作")
        menu = QMenu(self)
        settings_action = menu.addAction("設定…"); settings_action.triggered.connect(self.open_settings)
        add_action = menu.addAction("予定を追加…"); add_action.triggered.connect(self.add_event)
        delete_action = menu.addAction("選択日の予定を削除…"); delete_action.triggered.connect(self.delete_event)
        menu.addSeparator(); auth_action = menu.addAction("Googleアカウントに接続"); auth_action.triggered.connect(self.connect_google)
        menu.addSeparator(); quit_action = menu.addAction("終了"); quit_action.triggered.connect(self.close)
        self.menu_btn.setMenu(menu)
        top.addWidget(self.prev_btn); top.addWidget(self.next_btn); top.addWidget(self.today_btn); top.addWidget(self.refresh_btn); top.addWidget(self.menu_btn)
        outer.addLayout(top)
        panel = QFrame(); panel.setObjectName("panel"); p_layout = QVBoxLayout(panel); p_layout.setContentsMargins(10, 12, 10, 10); p_layout.setSpacing(8)
        weekdays = QGridLayout(); weekdays.setSpacing(3)
        for col, name in enumerate(["日", "月", "火", "水", "木", "金", "土"]):
            lbl = QLabel(name); lbl.setAlignment(Qt.AlignCenter); lbl.setObjectName("muted")
            if col == 0: lbl.setStyleSheet("color:#FF8D98;font-weight:700")
            if col == 6: lbl.setStyleSheet("color:#83B8FF;font-weight:700")
            weekdays.addWidget(lbl, 0, col)
        p_layout.addLayout(weekdays)
        self.day_grid = QGridLayout(); self.day_grid.setSpacing(3)
        self.day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = QPushButton(); btn.setObjectName("day"); btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked=False, r=row, c=col: self.select_cell(r, c))
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda pos, b=btn: self.day_context(b, pos))
                self.day_grid.addWidget(btn, row, col); self.day_buttons.append(btn)
        p_layout.addLayout(self.day_grid)
        outer.addWidget(panel)
        self.agenda_title = QLabel("予定 · 選択日から14日間")
        self.agenda_title.setStyleSheet("font-weight:700;font-size:14px;color:#F3F6FA;")
        outer.addWidget(self.agenda_title)
        self.agenda_list = QListWidget()
        self.agenda_list.setObjectName("agendaList")
        self.agenda_list.setMinimumHeight(110)
        self.agenda_list.setSpacing(1)
        self.agenda_list.setStyleSheet(
            "QListWidget { color: #F3F6FA; background: transparent; border: none; font-size: 12px; }"
            "QListWidget::item { color: #F3F6FA; min-height: 18px; padding: 3px 7px; "
            "border-bottom: 1px solid rgba(255,255,255,13); }"
            "QListWidget::item:selected { color: #F3F6FA; "
            "background: rgba(114,214,180,35); border-radius: 7px; }"
        )
        self.agenda_list.setVisible(bool(self.config.get("show_agenda", True)))
        outer.addWidget(self.agenda_list, 1)
        footer = QHBoxLayout()
        self.status = QLabel("Googleカレンダー未接続"); self.status.setObjectName("muted")
        self.add_btn = QPushButton("＋ 予定を追加"); self.add_btn.clicked.connect(self.add_event)
        footer.addWidget(self.status, 1); footer.addWidget(self.add_btn); outer.addLayout(footer)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(QIcon(str(resource_path("assets/gcalcal.png"))))

    def _apply_window_settings(self):
        flags = Qt.Window
        if self.config.get("always_on_top", True): flags |= Qt.WindowStaysOnTopHint
        if self.config.get("frameless", True): flags |= Qt.FramelessWindowHint
        self.setWindowFlags(flags)
        self.setWindowOpacity(float(self.config.get("opacity", .94)))
        self.resize(int(self.config.get("window_width", 440)), int(self.config.get("window_height", 600)))
        self.move(int(self.config.get("window_x", 80)), int(self.config.get("window_y", 80)))
        self.show()

    def shift_month(self, amount):
        idx = self.current.year*12 + self.current.month - 1 + amount
        self.current = date(idx//12, idx%12+1, 1)
        self.selected = self.current
        self.render_calendar(); self.refresh_data(show_errors=False)

    def go_today(self):
        self.current = date.today().replace(day=1); self.selected = date.today()
        self.render_calendar(); self.refresh_data(show_errors=False)

    def select_cell(self, row, col):
        btn = self.day_buttons[row*7+col]
        d = btn.property("date")
        if not d: return
        self.selected = d
        if d.month != self.current.month:
            self.current = d.replace(day=1)
            self.refresh_data(show_errors=False)
        self.render_calendar(); self.render_agenda()

    def day_context(self, btn, pos):
        d = btn.property("date")
        if d:
            self.selected = d
            self.render_calendar(); self.render_agenda()
            menu = QMenu(self)
            menu.addAction("この日に予定を追加", self.add_event)
            menu.addAction("この日の予定を削除", self.delete_event)
            menu.exec(btn.mapToGlobal(pos))

    def render_calendar(self):
        self.month_label.setText(f"{self.current.month}月")
        self.year_label.setText(f"{self.current.year}年")
        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdatescalendar(self.current.year, self.current.month)
        while len(weeks) < 6:
            last = weeks[-1][-1]
            weeks.append([last + timedelta(days=i) for i in range(1, 8)])
        event_days = set()
        for event in self.events:
            day = event["_start"].date()
            last_day = (event["_end"] - timedelta(microseconds=1)).date()
            while day <= last_day:
                event_days.add(day)
                day += timedelta(days=1)
        for i, btn in enumerate(self.day_buttons):
            r, c = divmod(i, 7); d = weeks[r][c]
            holiday = self.holidays.get(d, "")
            btn.setText(str(d.day) + ("  •" if d in event_days else ""))
            btn.setProperty("date", d)
            btn.setProperty("otherMonth", d.month != self.current.month)
            btn.setProperty("sunday", c == 0)
            btn.setProperty("saturday", c == 6)
            btn.setProperty("holiday", bool(holiday))
            btn.setProperty("today", d == date.today())
            btn.setProperty("selected", d == self.selected)
            btn.setProperty("hasEvents", d in event_days)
            tips = [e.get("summary", "(タイトルなし)") for e in self.events if e["_start"].date() <= d <= (e["_end"] - timedelta(seconds=1)).date()]
            if holiday: tips.insert(0, holiday)
            btn.setToolTip("\n".join(tips))
            btn.style().unpolish(btn); btn.style().polish(btn)
        self.render_agenda()

    def render_agenda(self):
        self.agenda_list.clear()
        range_start = datetime.combine(self.selected, time.min)
        range_end = datetime.combine(self.selected + timedelta(days=14), time.min)
        events = [e for e in self.events if e["_start"] < range_end and e["_end"] > range_start]
        events.sort(key=lambda e: (e["_start"], e.get("summary", "").casefold()))
        for e in events:
            st = e["_start"]
            when = st.strftime("%m/%d  終日" if e.get("start", {}).get("date") else "%m/%d  %H:%M")
            calendar_name = e.get("_calendar_name", "")
            calendar_prefix = f"[{calendar_name}] " if calendar_name else ""
            item = QListWidgetItem(f"{when}   {calendar_prefix}{e.get('summary', '(タイトルなし)')}")
            item.setForeground(QColor("#F3F6FA"))
            item.setData(Qt.UserRole, e)
            if e.get("description"): item.setToolTip(e["description"])
            self.agenda_list.addItem(item)
        if not events:
            empty_item = QListWidgetItem("この期間に予定はありません")
            empty_item.setForeground(QColor("#9BA8B8"))
            self.agenda_list.addItem(empty_item)
        self.agenda_title.setText(f"予定 · {self.selected:%m/%d}から14日間")

    def refresh_data(self, show_errors=True):
        try:
            self.service.credentials_file = self.config.get("credentials_file", "")
            start = self.current - timedelta(days=7)
            end = (self.current.replace(day=calendar.monthrange(self.current.year, self.current.month)[1]) + timedelta(days=21))

            if self.config.get("all_calendars", True):
                self.events, calendars, calendar_errors = self.service.list_all_calendar_events(start, end)
                self.status.setText(f"同期済み · {len(calendars)}カレンダー · {len(self.events)}件 · {datetime.now():%H:%M}")
                if calendar_errors and show_errors:
                    details = "\\n".join(calendar_errors[:8])
                    QMessageBox.warning(self, "一部のカレンダーを取得できません", details)
            else:
                calendar_id = self.config.get("calendar_id", "primary") or "primary"
                self.events = self.service.list_events(calendar_id, start, end)
                self.status.setText(f"同期済み · {len(self.events)}件 · {datetime.now():%H:%M}")
                for event in self.events:
                    event["_calendar_name"] = calendar_id

            self.holidays = {}
            holiday_id = self.config.get("holiday_calendar_id", "").strip()
            if holiday_id:
                for e in self.service.list_events(holiday_id, start, end):
                    day = e["_start"].date()
                    last_day = (e["_end"] - timedelta(microseconds=1)).date()
                    while day <= last_day:
                        self.holidays[day] = e.get("summary", "祝日")
                        day += timedelta(days=1)
            self.render_calendar()
            self.render_agenda()
            self.agenda_list.viewport().update()
            self.agenda_list.updateGeometry()
        except Exception as exc:
            self.status.setText("Googleカレンダー未接続")
            if show_errors:
                QMessageBox.warning(self, "Googleカレンダー", str(exc))

    def connect_google(self):
        try:
            self.service.credentials_file = self.config.get("credentials_file", "")
            self.service.connect(force_login=True)
            self.refresh_data()
        except Exception as exc:
            QMessageBox.critical(self, "Google認証", str(exc))

    def add_event(self):
        dlg = EventDialog(self.selected, self)
        if dlg.exec() != QDialog.Accepted: return
        title, start, end, description, all_day = dlg.values()
        if not title:
            QMessageBox.information(self, "予定を追加", "タイトルを入力してください。"); return
        try:
            self.service.credentials_file = self.config.get("credentials_file", "")
            self.service.create_event(self.config.get("calendar_id", "primary"), title, start, end, description, all_day)
            self.refresh_data()
        except Exception as exc:
            QMessageBox.critical(self, "予定を追加", str(exc))

    def delete_event(self):
        day_events = [e for e in self.events if e["_start"].date() <= self.selected <= (e["_end"] - timedelta(seconds=1)).date()]
        if not day_events:
            QMessageBox.information(self, "予定を削除", "選択日に予定はありません。"); return
        menu = QMenu(self)
        actions = {menu.addAction(e.get("summary", "(タイトルなし)")): e for e in day_events}
        chosen = menu.exec(self.mapToGlobal(self.rect().center()))
        if not chosen: return
        event = actions[chosen]
        answer = QMessageBox.question(self, "予定を削除", f"「{event.get('summary', '(タイトルなし)')}」を削除しますか？")
        if answer != QMessageBox.Yes: return
        try:
            self.service.delete_event(event.get("_calendar_id", self.config.get("calendar_id", "primary")), event["id"])
            self.refresh_data()
        except Exception as exc:
            QMessageBox.critical(self, "予定を削除", str(exc))

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec() != QDialog.Accepted: return
        self.config.update(dlg.values())
        self.agenda_list.setVisible(bool(self.config.get("show_agenda", True)))
        save_config(self.config)
        self.service.credentials_file = self.config.get("credentials_file", "")
        self.refresh_timer.setInterval(int(self.config.get("refresh_minutes", 15))*60*1000)
        old_pos = self.pos()
        self._apply_window_settings(); self.move(old_pos)
        self.refresh_data(show_errors=False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.config.get("frameless", True):
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos); event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self.config["window_x"] = self.x(); self.config["window_y"] = self.y()
        self.config["window_width"] = self.width(); self.config["window_height"] = self.height()
        save_config(self.config); event.accept()


def main():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(resource_path("assets/gcalcal.png"))))
    app.setFont(QFont("Yu Gothic UI", 9))
    window = GcalcalWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
