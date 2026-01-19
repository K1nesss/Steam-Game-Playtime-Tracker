import sys
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QColor, QAction
from PySide6.QtCore import QCoreApplication

# Import custom UI and utility modules
from ui.main_window import MainWindow, get_base_dir
from utils.utils import format_playtime

# -------------------------- Global Configuration (全局配置) --------------------------
# Get the project root directory (获取项目根目录)
BASE_DIR = get_base_dir()
# Path to the playtime data storage file (游玩时长数据存储文件路径)
DATA_FILE = BASE_DIR / "data" / "playtime.json"
# Path to the system tray icon file (系统托盘图标文件路径)
ICON_PATH = BASE_DIR / "assets" / "tray.ico"

def get_today_ranking():
    """
    Get today's game playtime ranking (获取今日游戏游玩时长排行榜)
    Returns:
        list[tuple[str, str]]: Sorted list of (game_name, formatted_playtime) (排序后的游戏名称和格式化时长列表)
    """
    # Return empty list if data file does not exist (如果数据文件不存在，返回空列表)
    if not DATA_FILE.exists():
        return []
    
    try:
        # Read and load JSON data from the file (读取并加载文件中的JSON数据)
        text = DATA_FILE.read_text(encoding="utf-8").strip()
        if not text:  # Return empty list if file is blank (如果文件为空，返回空列表)
            return []
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[Warning] Failed to read today's ranking: {e}")
        return []

    # Get current date in "YYYY-MM-DD" format (获取当前日期，格式为"年-月-日")
    today = datetime.now().strftime("%Y-%m-%d")
    # Get today's game data (default to empty dict if not exists) (获取今日游戏数据，不存在则返回空字典)
    games = data.get(today, {})
    
    # Format playtime and build ranking list (格式化游玩时长并构建排行榜列表)
    ranking_list = []
    # Sort games by total playtime in descending order (按总游玩时长降序排序)
    for name, info in sorted(games.items(), key=lambda x: x[1]["total"], reverse=True):
        # Validate data format before processing (处理前验证数据格式)
        if isinstance(info, dict) and "total" in info:
            formatted_time = format_playtime(info["total"])
            ranking_list.append((name, formatted_time))
    
    return ranking_list

class TrayIcon(QSystemTrayIcon):
    """
    System Tray Icon Class (系统托盘图标类)
    Manages tray icon display, right-click menu, and window interaction (管理托盘图标显示、右键菜单和窗口交互)
    """
    def __init__(self, watcher=None, parent=None):
        """
        Initialize the system tray icon (初始化系统托盘图标)
        Args:
            watcher: Process watcher instance (for log association) (进程监控器实例，用于日志关联)
            parent: Parent Qt widget (父Qt控件)
        """
        super().__init__(parent)
        self.watcher = watcher  # Save watcher instance for log synchronization (保存监控器实例用于日志同步)
        
        # 1. Create a single global instance of the main window (创建全局唯一的主窗口实例)
        self.window = MainWindow()

        # 2. Create and set tray icon (创建并设置托盘图标)
        # Create a fallback pixmap (blue square) in case icon file is missing (创建备用像素图（蓝色方块），防止图标文件缺失)
        fallback_pixmap = QPixmap(64, 64)
        fallback_pixmap.fill(QColor(50, 150, 250))
        
        # Print icon path and existence for debugging (打印图标路径和存在性，用于调试)
        print(f"Tray icon path: {ICON_PATH}, Exists: {ICON_PATH.exists()}")
        
        # Set icon (use custom icon if exists, otherwise use fallback) (设置图标：存在自定义图标则使用，否则使用备用图标)
        if ICON_PATH.exists():
            self.setIcon(QIcon(str(ICON_PATH)))
        else:
            self.setIcon(QIcon(fallback_pixmap))
        
        # Set tray icon tooltip (设置托盘图标提示文本)
        self.setToolTip("GameTimeTracker")

        # 3. Configure right-click context menu (配置右键上下文菜单)
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        
        # Update menu content before each display (to show dynamic ranking) (每次显示菜单前更新内容，用于展示动态排行榜)
        self.menu.aboutToShow.connect(self.update_menu)

        # 4. Handle tray icon click events (e.g., left-click to show window) (处理托盘图标点击事件，例如左键点击显示窗口)
        self.activated.connect(self.on_activated)

        # Log startup information (记录启动信息)
        self.log("Tray application started successfully")
        # Show the tray icon (显示托盘图标)
        self.show()

    def log(self, text: str):
        """
        Log system information (记录系统信息)
        Args:
            text: Log content (日志内容)
        """
        # Format current time (格式化当前时间)
        current_time = datetime.now().strftime("%H:%M:%S")
        # Print to console (打印到控制台)
        print(f"[{current_time}] {text}")
        # Append to UI log window (追加到UI日志窗口)
        self.window.append_log(text)
        # Synchronize to watcher log if available (如果监控器存在，同步到监控器日志)
        if self.watcher:
            self.watcher._log(f"[Tray] {text}")

    def on_activated(self, reason):
        """
        Handle tray icon activation events (处理托盘图标激活事件)
        Args:
            reason: Activation reason (QSystemTrayIcon.ActivationReason) (激活原因)
        """
        # Triggered by left-click (左键点击触发)
        if reason == QSystemTrayIcon.Trigger:
            self.log("Left-click on tray icon, opening statistics panel")
            self.show_window()

    def show_window(self):
        """
        Show and refresh the main statistics window (显示并刷新主统计窗口)
        """
        self.log("Showing statistics window")
        self.window.refresh()  # Refresh latest game data (刷新最新游戏数据)
        self.window.show()     # Show the window (显示窗口)
        self.window.raise_()   # Bring the window to the front (将窗口提到最前)
        self.window.activateWindow()  # Activate the window (激活窗口，获得焦点)

    def update_menu(self):
        """
        Dynamically build the right-click context menu (动态构建右键上下文菜单)
        """
        self.log("Expanding tray right-click menu")
        # Clear existing menu items (清空现有菜单项)
        self.menu.clear()

        # --- Menu Item: Open Statistics Panel (菜单项：打开统计面板) ---
        action_open = self.menu.addAction("Open Statistics Panel")
        action_open.triggered.connect(self.show_window)

        # Add menu separator (添加菜单分隔线)
        self.menu.addSeparator()

        # --- Menu Section: Today's Ranking (菜单部分：今日排行榜) ---
        today_ranking = get_today_ranking()
        if today_ranking:
            # Add non-clickable ranking header (添加不可点击的排行榜标题)
            ranking_header = self.menu.addAction("🎮 Today's Ranking")
            ranking_header.setEnabled(False)
            
            # Add each game to the menu (将每个游戏添加到菜单中)
            for game_name, formatted_time in today_ranking:
                menu_item = self.menu.addAction(f"{game_name}  {formatted_time}")
                menu_item.setEnabled(False)
        else:
            # Show prompt if no games played today (如果今日未玩游戏，显示提示信息)
            self.menu.addAction("No games played today").setEnabled(False)

        # Add another menu separator (添加另一个菜单分隔线)
        self.menu.addSeparator()

        # --- Menu Item: Exit Application (菜单项：退出应用程序) ---
        action_quit = self.menu.addAction("Exit")
        action_quit.triggered.connect(self.quit_app)

    def quit_app(self):
        """
        Quit the application completely (彻底退出应用程序)
        """
        self.log("User initiated application exit")
        # Terminate the Qt application event loop (终止Qt应用程序事件循环)
        QCoreApplication.quit()