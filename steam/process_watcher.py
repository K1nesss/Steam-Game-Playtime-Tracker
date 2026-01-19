import sys
import psutil
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from utils.utils import format_playtime

# ========= Path Handling (Configurable Externally) =========
# Do not hardcode BASE_DIR anymore, it is passed in during initialization
# (不再硬编码BASE_DIR，改为初始化时从外部传入)
DATA_FILE_NAME = "playtime.json"

class ProcessWatcher:
    """
    Steam Game Process Watcher
    - Responsibilities: Detect process startup/shutdown, count playtime, persist data to file
    - Non-responsibilities: UI, window management, visual display
    (Steam游戏进程监控器)
    - 负责：进程启动 / 关闭检测、时间统计、数据落盘
    - 不负责：UI、窗口、显示
    """

    def __init__(
        self,
        games: dict,
        base_dir: Path,  # New: Base directory passed in from external (新增：外部传入基准目录)
        log_fn: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the ProcessWatcher instance (初始化ProcessWatcher实例)
        
        Args:
            games: EXE mapping returned by scan_steam_games() (scan_steam_games() 返回的 exe 映射字典)
            base_dir: Project root directory (used to locate the data folder) (项目根目录，用于定位data文件夹)
            log_fn: Log callback function (e.g., MainWindow.append_log) (日志回调函数，例如 MainWindow.append_log)
        """
        self.games = games
        self.log_fn = log_fn
        self.running = {}  # Key: exe filename (lowercase), Value: process start timestamp (exe -> 启动时间戳)

        # Unified data file path: root_dir/data/playtime.json (统一数据文件路径：根目录/data/playtime.json)
        self.DATA_FILE = base_dir / "data" / DATA_FILE_NAME
        # Create parent directory if it does not exist (若父目录不存在则创建)
        self.DATA_FILE.parent.mkdir(exist_ok=True)
        # Create empty JSON file if data file does not exist (若数据文件不存在则创建空JSON文件)
        if not self.DATA_FILE.exists():
            self.DATA_FILE.write_text("{}", encoding="utf-8")

        self._log("ProcessWatcher initialized successfully")
        self._log(f"Number of monitored EXE files: {len(self.games)}")
        self._log(f"Data file path: {self.DATA_FILE}")  # New: Print path for debugging (新增：打印路径便于调试)

    # ---------------- Logging ----------------
    def _log(self, msg: str):
        """
        Log output (supports callback and console print as fallback)
        (日志输出（支持回调函数，终端打印作为兜底）)
        """
        # Print to console with timestamp (带时间戳打印到终端)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        # Call external log callback if available (若存在外部日志回调则调用)
        if self.log_fn:
            try:
                # Add try-except to avoid monitor crash caused by UI callback exceptions
                # (增加异常捕获，避免UI回调异常导致监控崩溃)
                self.log_fn(msg)
            except Exception as e:
                print(f"[Warning] Failed to execute log callback: {e}")

    # ---------------- Data IO ----------------
    def _load(self) -> dict:
        """
        Load data from JSON file (从JSON文件加载数据)
        Returns:
            dict: Loaded game playtime data (加载的游戏时长数据，加载失败返回空字典)
        """
        try:
            return json.loads(self.DATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            self._log(f"[Warning] Failed to load data, using empty dictionary: {str(e)}")
            return {}

    def _save(self, data: dict):
        """
        Save data to JSON file (将数据保存到JSON文件)
        Args:
            data: Game playtime data to be saved (待保存的游戏时长数据)
        """
        try:
            self.DATA_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            self._log(f"[Error] Failed to save data: {str(e)}")

    # ---------------- Core Process Detection ----------------
    def tick(self):
        """
        Detect process status once per call (每次调用检测一次进程状态)
        Recommendation: Call every 1~2 seconds (建议：1~2 秒调用一次)
        """
        now_running = set()

        # ---- Scan system processes (get full EXE path for more reliable matching) ----
        # (扫描系统进程（获取完整EXE路径，提高匹配可靠性）)
        for proc in psutil.process_iter(["pid", "name", "exe"]):  # Add exe and pid fields (增加exe和pid字段)
            try:
                proc_info = proc.info
                proc_exe = proc_info.get("exe")  # Full process EXE path (most reliable) (进程完整EXE路径，最可靠)
                proc_name = proc_info.get("name", "")

                # Skip processes without full EXE path (跳过无完整EXE路径的进程)
                if not proc_exe:
                    continue

                # Extract EXE filename (with extension) from full path and convert to lowercase for matching
                # (从完整路径中提取EXE文件名（带后缀），转小写用于匹配)
                exe_filename = Path(proc_exe).name.lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                # Improve exception handling, skip invalid processes (完善异常处理，跳过无效进程)
                continue
            except Exception as e:
                self._log(f"[Warning] Failed to traverse process: {str(e)}")
                continue

            # ---- Match Steam game EXE files ---- (匹配Steam游戏EXE)
            if exe_filename in self.games:
                now_running.add(exe_filename)

                # -------- New Process Startup Detection -------- (新启动进程检测)
                if exe_filename not in self.running:
                    self.running[exe_filename] = time.time()
                    game_name = self.games[exe_filename]["name"]
                    game_exe_path = self.games[exe_filename]["exe_path"]
                    self._log(
                        f"Detected process startup: {exe_filename} ({game_name})\n"
                        f"  - Process PID: {proc_info.get('pid', 'Unknown')}\n"
                        f"  - Game path: {game_exe_path}"
                    )

        # ---- Detect Process Shutdown ---- (检测进程关闭)
        for exe in list(self.running.keys()):
            if exe not in now_running:
                start_ts = self.running.pop(exe)
                duration = int(time.time() - start_ts)
                self._record(exe, start_ts, duration)

    # ---------------- Data Recording ----------------
    def _record(self, exe: str, start_ts: float, duration: int):
        """
        Record game playtime data to JSON file (将游戏时长数据记录到JSON文件)
        Args:
            exe: Lowercase EXE filename (小写的EXE文件名)
            start_ts: Process start timestamp (进程启动时间戳)
            duration: Process running duration (seconds) (进程运行时长，单位：秒)
        """
        game_name = self.games[exe]["name"]

        # Format timestamps to human-readable strings (将时间戳格式化为人类可读字符串)
        start_str = datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S")
        end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format playtime for display (格式化时长用于展示)
        duration_show = format_playtime(duration)

        self._log(
            f"Detected process shutdown: {exe} ({game_name}), this session: {duration_show}"
        )

        # Load existing data (加载已有数据)
        data = self._load()
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Initialize data structure if not exists (初始化数据结构，若不存在则创建)
        data.setdefault(current_date, {})
        game_data = data[current_date].setdefault(
            game_name,
            {
                "total": 0,
                "last_open": None,
                "last_close": None
            }
        )

        # Update game playtime data (更新游戏时长数据)
        game_data["total"] += duration
        game_data["last_open"] = start_str
        game_data["last_close"] = end_str

        # Save updated data to file (将更新后的数据保存到文件)
        self._save(data)