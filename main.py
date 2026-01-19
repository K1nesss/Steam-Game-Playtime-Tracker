import sys
import threading
import time
from pathlib import Path
import json
from PySide6.QtWidgets import QApplication
from steam.game_scanner import scan_steam_games
from steam.process_watcher import ProcessWatcher
import tray
from ui.main_window import get_base_dir

# -------------------------- Global Configuration & Variables (全局配置和变量) --------------------------
# Get the root directory of the project (获取项目根目录)
BASE_DIR = get_base_dir()

# Global process watcher instance (全局进程监控器实例)
global_watcher = None

def start_monitor(log_fn=None):
    """
    Start the background game process monitoring thread (启动后台游戏进程监控线程)
    Args:
        log_fn: UI log callback function (MainWindow.append_log) (UI日志回调函数，对应MainWindow.append_log方法)
    """
    global global_watcher  # Declare to use the global watcher variable (声明使用全局监控器变量)
    
    # Path to the configuration file (project root / config.json) (配置文件路径：项目根目录/config.json)
    config_path = BASE_DIR / "config.json"
    
    try:
        # Read and load the configuration file (读取并加载配置文件)
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            steam_path = config["steam_path"]
        
        # Log Steam path reading success (记录Steam路径读取成功信息)
        steam_path_msg = f"Successfully read Steam path: {steam_path}"
        print(steam_path_msg)
        if log_fn:
            log_fn(steam_path_msg)
    
    except FileNotFoundError:
        # Handle configuration file not found error (处理配置文件未找到错误)
        err_msg = f"Configuration file not found: {config_path}. Please check if the file exists."
        print(err_msg)
        if log_fn:
            log_fn(err_msg)
        return
    
    except KeyError:
        # Handle missing "steam_path" field in configuration (处理配置文件缺少"steam_path"字段错误)
        err_msg = f"Configuration file missing 'steam_path' field: {config_path}"
        print(err_msg)
        if log_fn:
            log_fn(err_msg)
        return

    # Scan Steam games from the specified Steam path (从指定Steam路径扫描Steam游戏)
    games = scan_steam_games(steam_path)
    scan_msg = f"Number of Steam games scanned: {len(games)}"
    print(scan_msg)
    if log_fn:
        log_fn(scan_msg)

    try:
        # Initialize the ProcessWatcher instance (初始化进程监控器实例)
        global_watcher = ProcessWatcher(
            games=games,
            base_dir=BASE_DIR,  # Pass the project root directory (传递项目根目录)
            log_fn=log_fn       # Pass the UI log callback function (传递UI日志回调函数)
        )
    except Exception as e:
        # Handle ProcessWatcher initialization failure (处理进程监控器初始化失败错误)
        err_msg = f"Failed to initialize ProcessWatcher: {e}"
        print(err_msg)
        if log_fn:
            log_fn(err_msg)
        return
    
    # Continuous monitoring loop (持续监控循环)
    while True:
        try:
            # Execute a single monitoring tick (执行单次监控检查)
            global_watcher.tick()
            # Sleep for 1 second to reduce CPU usage (休眠1秒，降低CPU占用)
            time.sleep(1)
        except Exception as e:
            # Handle exceptions during monitoring (处理监控过程中的异常)
            err_msg = f"Monitor thread exception occurred: {e}"
            print(err_msg)
            if log_fn:
                log_fn(err_msg)
            # Delay 1 second after exception to avoid infinite loop crashes (异常后休眠1秒，避免卡死循环)
            time.sleep(1)

if __name__ == "__main__":
    # 1. Create Qt Application instance (创建Qt应用程序实例)
    app = QApplication(sys.argv)
    # Do not quit the app when the last window is closed (关闭最后一个窗口时不退出应用程序，保持托盘驻留)
    app.setQuitOnLastWindowClosed(False)

    # 2. Create system tray first (to get the initialized MainWindow instance) (先创建系统托盘，获取已初始化的MainWindow实例)
    system_tray = tray.TrayIcon(watcher=global_watcher)
    # Get the initialized MainWindow instance from the tray (从托盘中获取已初始化的MainWindow实例)
    main_window = system_tray.window

    # 3. Start the background monitor thread (daemon thread) (启动后台监控线程，设置为守护线程)
    monitor_thread = threading.Thread(
        target=start_monitor,
        args=(main_window.append_log,),  # Pass the UI log callback function (传入UI日志回调函数)
        daemon=True
    )
    monitor_thread.start()

    # 4. Enter the Qt event loop (进入Qt事件循环)
    sys.exit(app.exec())