import os
import re

# -------------------------- Constant Configuration (常量配置) --------------------------
# Blacklist of executable files that do not need to be monitored (无需监控的可执行文件黑名单)
# These are usually auxiliary processes (not the main game process) (这些通常是辅助进程，非游戏主进程)
EXE_BLACKLIST = {
    "unitycrashhandler.exe",
    "unitycrashhandler64.exe",
    "uninstall.exe",
    "crashreporter.exe"
}

# Regular expression to match game name in ACF files (匹配ACF文件中游戏名称的正则表达式)
ACF_NAME_RE = re.compile(r'"name"\s+"(.+)"')
# Regular expression to match game installation directory in ACF files (匹配ACF文件中游戏安装目录的正则表达式)
ACF_INSTALL_RE = re.compile(r'"installdir"\s+"(.+)"')


def parse_acf(path: str):
    """
    Parse Steam ACF manifest files to extract game name and installation directory
    (解析Steam ACF清单文件，提取游戏名称和安装目录)
    
    Args:
        path: Full path to the ACF file (ACF文件的完整路径)
    
    Returns:
        tuple[str | None, str | None]: (game_name, install_directory) (游戏名称，安装目录)
        Returns (None, None) if parsing fails (解析失败返回(None, None))
    """
    game_name = None
    install_dir = None

    # Read ACF file (ignore encoding errors to handle special characters)
    # 读取ACF文件（忽略编码错误，兼容特殊字符）
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Extract game name if not already found (若未提取到游戏名称，进行提取)
            if not game_name:
                name_match = ACF_NAME_RE.search(line)
                if name_match:
                    game_name = name_match.group(1)
            
            # Extract installation directory if not already found (若未提取到安装目录，进行提取)
            if not install_dir:
                install_match = ACF_INSTALL_RE.search(line)
                if install_match:
                    install_dir = install_match.group(1)

    return game_name, install_dir


def scan_steam_games(steam_path: str) -> dict:
    """
    Scan Steam installation directory to find all installed games and their executable files
    (扫描Steam安装目录，查找所有已安装游戏及其可执行文件)
    
    Returns:
        dict: A dictionary with executable file names as keys and game details as values
        (返回以可执行文件名作为键、游戏详情作为值的字典)
        Format (格式):
        {
            "eldenring.exe": {
                "name": "ELDEN RING",
                "appid": "1245620",
                "exe_path": "D:/Steam/steamapps/common/ELDEN RING/Game/eldenring.exe"
            }
        }
    """
    # Initialize game dictionary (初始化游戏字典)
    games = {}
    
    # Construct path to Steam apps directory (构建Steam应用目录路径)
    steamapps_dir = os.path.join(steam_path, "steamapps")
    
    # Return empty dict if steamapps directory does not exist (若steamapps目录不存在，返回空字典)
    if not os.path.isdir(steamapps_dir):
        return games

    # Traverse all files in steamapps directory (遍历steamapps目录下的所有文件)
    for file_name in os.listdir(steamapps_dir):
        # Filter valid ACF manifest files (筛选有效的ACF清单文件)
        if not file_name.startswith("appmanifest_") or not file_name.endswith(".acf"):
            continue

        # Extract Steam App ID from ACF file name (从ACF文件名中提取Steam应用ID)
        app_id = file_name.replace("appmanifest_", "").replace(".acf", "")
        
        # Parse ACF file to get game name and installation directory (解析ACF文件，获取游戏名称和安装目录)
        acf_file_path = os.path.join(steamapps_dir, file_name)
        game_name, install_dir = parse_acf(acf_file_path)
        
        # Skip if game name or installation directory is missing (若缺少游戏名称或安装目录，跳过当前文件)
        if not game_name or not install_dir:
            continue

        # Construct the root directory of the installed game (构建游戏安装的根目录)
        game_root_dir = os.path.join(steamapps_dir, "common", install_dir)
        
        # Skip if game root directory does not exist (若游戏根目录不存在，跳过当前游戏)
        if not os.path.isdir(game_root_dir):
            continue

        # Recursively traverse game directory to find executable files (递归遍历游戏目录，查找可执行文件)
        for root_dir, _, file_list in os.walk(game_root_dir):
            for file in file_list:
                # Filter files with .exe extension (筛选.exe后缀的文件)
                if not file.lower().endswith(".exe"):
                    continue
                
                # Skip executable files in blacklist (跳过黑名单中的可执行文件)
                if file.lower() in EXE_BLACKLIST:
                    continue

                # Add game information to the dictionary (将游戏信息添加到字典中)
                games[file.lower()] = {
                    "name": game_name,
                    "appid": app_id,
                    "exe_path": os.path.join(root_dir, file)
                }

    return games