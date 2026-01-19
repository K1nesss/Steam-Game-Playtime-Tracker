import sys
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QToolTip,
    QTextEdit, QSizePolicy
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QCursor, QIcon
from utils.utils import format_playtime

# ========= Path Handling (Unified to Project Root Directory) =========
def get_base_dir():
    """Get the project root directory (compatible with source code / packaged execution)"""
    if getattr(sys, "frozen", False):
        # If running as packaged EXE (如果以打包后的EXE运行)
        return Path(sys.executable).parent
    else:
        # If running as source code (main_window.py is in ui/ directory, go up one level to root)
        # 若以源码运行（main_window.py在ui/目录下，向上退一级到项目根目录）
        return Path(__file__).parent.parent.absolute()

# Global directory configuration (全局目录配置)
BASE_DIR = get_base_dir()
DATA_FILE = BASE_DIR / "data" / "playtime.json"

# ========= Main Window =========
class MainWindow(QWidget):
    # Signal for thread-safe log updating (用于线程安全更新日志的信号)
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        # 【Critical】The following 3 lines must be executed in order (缺一不可)
        # Set window title (设置窗口标题)
        self.setWindowTitle("Steam Game Playtime Tracker")
        # Set window default size (设置窗口默认大小)
        self.resize(900, 480)
        
        # Core modification: Set window title bar icon (核心修改：设置窗口标题栏图标)
        window_icon_path = BASE_DIR / "assets" / "tray.ico"  # Reuse tray icon, or replace with window.ico
        if window_icon_path.exists():
            self.setWindowIcon(QIcon(str(window_icon_path)))
        
        # Must call this method to create UI widgets (including log_view)
        # 必须调用该方法创建UI控件（包含log_view日志窗口）
        self._init_ui()
        
        # Apply UI theme (choose one theme below) (应用UI主题，下方选择其中一个即可)
        # self._apply_dark_theme()
        # self._apply_light_theme()
        self._apply_morandi_pink_theme()
        
        # Game data cache (游戏数据缓存)
        self.cache = {}
        
        # Connect log signal to thread-safe log method (将日志信号连接到线程安全的日志方法)
        self.log_signal.connect(self._append_log_safe)
        
        # Set up auto-refresh timer (设置自动刷新定时器)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)  # Refresh every 5 seconds (每5秒刷新一次)

        # Initial data refresh (初始数据刷新)
        self.refresh()

    # ---------------- UI Initialization ----------------
    def _init_ui(self):
        """Initialize the user interface layout and widgets (初始化用户界面布局和控件)"""
        # Main horizontal layout (主水平布局)
        main_layout = QHBoxLayout(self)

        # ===== Left Panel (1/4 of window width) =====
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        # --- Upper Part: Statistics Information (Centered) ---
        stat_layout = QVBoxLayout()
        stat_layout.addStretch()

        # Create statistics labels (创建统计标签)
        self.today_label = QLabel("Today's Playtime: 0")
        self.week_label = QLabel("This Week's Playtime: 0")

        # Set text alignment to center (设置文本居中对齐)
        self.today_label.setAlignment(Qt.AlignCenter)
        self.week_label.setAlignment(Qt.AlignCenter)

        # Set label styles (设置标签样式)
        self.today_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.week_label.setStyleSheet("font-size: 14px;")

        # Add labels to statistics layout (将标签添加到统计布局)
        stat_layout.addWidget(self.today_label)
        stat_layout.addWidget(self.week_label)
        stat_layout.addStretch()

        # --- Lower Part: Runtime Log ---
        # 【Critical】Create log_view here, ensure _init_ui() is executed first
        # 【关键】在此创建log_view，确保_init_ui()被优先执行
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)  # Set log window to read-only (设置日志窗口为只读)
        self.log_view.setPlaceholderText("Runtime Logs...")  # Placeholder text (占位文本)
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add statistics and log to left layout (将统计区域和日志区域添加到左侧布局)
        left_layout.addLayout(stat_layout, 1)
        left_layout.addWidget(self.log_view, 1)

        # ===== Right Panel (3/4 of window width) =====
        right_layout = QVBoxLayout()

        # Create game data table (创建游戏数据表格)
        self.table = QTableWidget(0, 4)
        # Set table header labels (设置表格表头标签)
        self.table.setHorizontalHeaderLabels(["Game", "Today", "This Week", "Total"])
        # Stretch last column to fill available space (最后一列自动拉伸填充剩余空间)
        self.table.horizontalHeader().setStretchLastSection(True)
        # Enable mouse tracking for tooltip display (启用鼠标跟踪，用于显示提示框)
        self.table.setMouseTracking(True)
        # Disable cell editing (禁用单元格编辑)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # Connect item hover event to tooltip method (将单元格悬浮事件连接到提示框方法)
        self.table.itemEntered.connect(self._show_tooltip)

        # Add table to right layout (将表格添加到右侧布局)
        right_layout.addWidget(self.table)

        # Add left and right panels to main layout (将左右面板添加到主布局)
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

    # ---------------- UI Themes ----------------
    def _apply_morandi_pink_theme(self):
        """Morandi Pink-Gray Theme (Soft & Elegant Style) (莫兰迪灰粉主题：温柔高级风)"""
        self.setStyleSheet("""
        QWidget {
            background-color: #faf9f8;
            color: #594f4f;
            font-size: 13px;
            font-family: "Microsoft YaHei", sans-serif;
        }

        QLabel {
            color: #594f4f;
        }

        QTableWidget {
            background-color: #ffffff;
            gridline-color: #eae6e5;
            selection-background-color: #e8dfe9;
            selection-color: #7d6e83;
            border: none;
            border-radius: 6px;
        }

        QHeaderView::section {
            background-color: #f3edf7;
            border: none;
            border-right: 1px solid #eae6e5;
            border-bottom: 2px solid #bba6c7;
            padding: 6px;
            color: #7d6e83;
            font-weight: bold;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }

        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #eae6e5;
            border-radius: 6px;
            color: #594f4f;
            padding: 8px;
        }

        QToolTip {
            background-color: #f3edf7;
            color: #7d6e83;
            border: 1px solid #e8dfe9;
            border-radius: 6px;
            padding: 6px;
        }
        """)

    def _apply_light_theme(self):
        """Light Theme (Bright & Clear Style) (浅色主题：明亮清晰风)"""
        self.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #212121;
            font-size: 13px;
        }

        QLabel {
            color: #212121;
        }

        QTableWidget {
            background-color: #fafafa;
            gridline-color: #e0e0e0;
            selection-background-color: #bbdefb;
            color: #212121;
        }

        QHeaderView::section {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            padding: 4px;
            color: #212121;
        }

        QTextEdit {
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            color: #212121;
        }

        QToolTip {
            background-color: #f9f9f9;
            color: #212121;
            border: 1px solid #e0e0e0;
        }
        """)

    def _apply_dark_theme(self):
        """Dark Theme (Dark & Eye-Friendly Style) (深色主题：暗黑护眼风)"""
        self.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #dcdcdc;
            font-size: 13px;
        }

        QLabel {
            color: #dcdcdc;
        }

        QTableWidget {
            background-color: #252526;
            gridline-color: #3c3c3c;
            selection-background-color: #094771;
        }

        QHeaderView::section {
            background-color: #2d2d2d;
            border: 1px solid #3c3c3c;
            padding: 4px;
        }

        QTextEdit {
            background-color: #252526;
            border: 1px solid #3c3c3c;
        }

        QToolTip {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3c3c3c;
        }
        """)

    # ---------------- Window Events ----------------
    def closeEvent(self, event):
        """Override close event to hide window instead of closing it (重写关闭事件，隐藏窗口而非退出)"""
        event.ignore()  # Ignore the default close event (忽略默认关闭事件)
        self.hide()     # Hide the window to tray (将窗口隐藏到托盘)

    # ---------------- Data Refresh ----------------
    def refresh(self):
        """Refresh game playtime data and update UI (刷新游戏游玩时长数据并更新UI)"""
        # Check if data file exists (检查数据文件是否存在)
        if not DATA_FILE.exists():
            if hasattr(self, "log_view"):  # Fault tolerance: prevent log_view not initialized (容错：防止log_view未初始化)
                self.append_log(f"[Info] Data file not found: {DATA_FILE}")
            return

        try:
            # Read and load JSON data from file (读取并加载文件中的JSON数据)
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            if hasattr(self, "log_view"):
                self.append_log(f"[Error] Failed to read data file: {e}")
            return

        # Get current date and week (获取当前日期和周数)
        today = datetime.now().strftime("%Y-%m-%d")
        current_week = datetime.now().isocalendar().week

        # Initialize statistics variables (初始化统计变量)
        today_total = 0
        week_total = 0
        games = {}

        # Traverse date data (with multi-layer fault tolerance) (遍历日期数据，增加多层容错)
        for date, daily in data.items():
            # Fault tolerance 1: daily must be a dictionary (容错1：daily必须是字典类型)
            if not isinstance(daily, dict):
                self.append_log(f"[Warning] Invalid daily data format (not a dictionary), skipping date: {date}")
                continue
            
            # Convert date string to datetime object (将日期字符串转换为datetime对象)
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            
            # Traverse game data for the current date (遍历当前日期的游戏数据)
            for name, info in daily.items():
                # Fault tolerance 2: info must be a dictionary (core fix: avoid int type error)
                # 容错2：info必须是字典类型（核心修复：避免int类型报错）
                if not isinstance(info, dict):
                    self.append_log(f"[Warning] Invalid game data format (not a dictionary), skipping game: {name}")
                    continue
                
                # Fault tolerance 3: info must contain "total" field, skip otherwise
                # 容错3：info必须包含"total"字段，否则跳过
                if "total" not in info:
                    self.append_log(f"[Warning] Game data missing 'total' field, skipping game: {name}")
                    continue

                # Initialize game data in cache (if not exists) (初始化缓存中的游戏数据，若不存在则创建)
                games.setdefault(name, {
                    "today": 0,
                    "week": 0,
                    "total": 0,
                    "last_open": info.get("last_open"),  # Safely get last open time (安全获取最近打开时间)
                    "last_close": info.get("last_close") # Safely get last close time (安全获取最近关闭时间)
                })

                # Accumulate total playtime (累加总游玩时长)
                games[name]["total"] += info["total"]

                # Accumulate today's playtime (累加今日游玩时长)
                if date == today:
                    games[name]["today"] += info["total"]
                    today_total += info["total"]

                # Accumulate this week's playtime (累加本周游玩时长)
                if date_obj.isocalendar().week == current_week:
                    games[name]["week"] += info["total"]
                    week_total += info["total"]

        # Update cache and statistics labels (更新缓存和统计标签)
        self.cache = games
        self.today_label.setText(f"Today's Playtime: {format_playtime(today_total)}")
        self.week_label.setText(f"This Week's Playtime: {format_playtime(week_total)}")

        # Update game data table (更新游戏数据表格)
        self.table.setRowCount(0)  # Clear existing rows (清空现有行)
        # Sort games by today's playtime (descending order) (按今日游玩时长降序排序)
        for name, g in sorted(games.items(), key=lambda x: x[1]["today"], reverse=True):
            row = self.table.rowCount()
            self.table.insertRow(row)  # Insert new row (插入新行)
            # Set table cell data (设置表格单元格数据)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(format_playtime(g["today"])))
            self.table.setItem(row, 2, QTableWidgetItem(format_playtime(g["week"])))
            self.table.setItem(row, 3, QTableWidgetItem(format_playtime(g["total"])))

    # ---------------- Tooltip Display ----------------
    def _show_tooltip(self, item):
        """Show tooltip with game's last open/close time when hovering over table cell (悬浮表格单元格时显示游戏最近启停时间)"""
        # Get game name from first column of the current row (获取当前行第一列的游戏名称)
        game = self.table.item(item.row(), 0).text()
        # Get game info from cache (从缓存中获取游戏信息)
        info = self.cache.get(game)
        if not info:
            return

        # Show tooltip at cursor position (在鼠标光标位置显示提示框)
        QToolTip.showText(
            QCursor.pos(),
            f"Last Opened: {info.get('last_open')}\nLast Closed: {info.get('last_close')}"
        )

    # ---------------- Thread-Safe Logging ----------------
    def _append_log_safe(self, text: str):
        """Thread-safe method to append log to UI (线程安全的UI日志追加方法)"""
        if not hasattr(self, "log_view"):
            print(f"[Warning] log_view not initialized, cannot output UI log: {text}")
            return
        # Add timestamp to log (为日志添加时间戳)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{timestamp}] {text}")

    def append_log(self, text: str):
        """Interface for ProcessWatcher to call (thread-safe) (供ProcessWatcher调用的日志接口，线程安全)"""
        try:
            # Emit signal to let main thread handle UI update (发送信号，由主线程处理UI更新)
            self.log_signal.emit(text)
        except Exception as e:
            print(f"[Warning] Failed to emit log signal: {e}")