
# Steam 游戏时间统计工具 / Steam Game Playtime Tracker
> 一款轻量化 Steam 游戏运行时间监控工具（A lightweight tool for monitoring Steam game playtime）

---

## 目录
1. [中文版（Chinese Version）](#中文版-chinese-version)
2. [英文版（English Version）](#英文版-english-version)

---

## 中文版（Chinese Version）
# Steam 游戏时间统计工具
一款轻量化的 Steam 游戏运行时间监控工具，基于 Python + PySide6 开发，支持托盘驻留、自动扫描游戏、进程监控、时长统计和美观的图形界面展示，无需复杂配置，打包后可直接运行。

## 功能特点
1.  **自动扫描 Steam 游戏**：读取 Steam 安装目录下的游戏清单，自动收集游戏可执行文件、名称等信息，无需手动添加。
2.  **实时进程监控**：后台静默监控游戏进程启停，精准记录每款游戏的游玩时长，避免同名进程误判。
3.  **多维度时长统计**：支持按「今日/本周/总计」统计游玩时长，格式自适应（10s、2m2s、1h2m2s）。
4.  **系统托盘驻留**：轻量化运行，不占用桌面空间，左键点击打开统计面板，右键菜单查看今日排行榜。
5.  **美观的图形界面**：支持多款高颜值主题切换（深色/浅色/清新蓝白/莫兰迪灰粉/科技感银灰），数据表格清晰直观。
6.  **数据持久化存储**：游玩数据自动保存到 `data/playtime.json`，程序重启后不丢失。
7.  **支持打包为 EXE**：可打包为独立可执行文件，无需依赖 Python 环境，直接在 Windows 系统运行。

## 项目结构
```
Tracker/  # 项目根目录
├── main.py  # 程序入口文件
├── tray.py  # 系统托盘功能模块
├── config.json  # Steam 路径配置文件
├── README.md  # 英文版说明文档
├── README_CN.md  # 中文版说明文档
├── assets/  # 资源文件夹（存放图标）
│   └── tray.ico  # 图标
├── ui/  # 图形界面模块目录
│   └── main_window.py  # 主统计窗口实现
├── steam/  # 核心功能模块目录
│   ├── game_scanner.py  # Steam 游戏扫描工具
│   └── process_watcher.py  # 游戏进程监控与时长统计
├── utils/  # 工具目录
│   └── utils.py  # 工具
└── data/  # 数据存储目录（自动生成游玩数据）
    └── playtime.json  # 游玩时长持久化文件（程序运行后自动生成）
```

## 快速开始
### 1. 环境准备（源码运行）
- 支持 Python 3.8 及以上版本
- 安装依赖库：
  ```bash
  pip install requirements.txt
  ```

### 2. 配置 Steam 路径
1.  打开项目根目录下的 `config.json` 文件；
2.  修改 `steam_path` 为你的 Steam 安装目录（示例如下）：
  ```json
  {
      "steam_path": "D:/Steam"
  }
  ```
  > 注意：路径使用 `/` 或 `\\` 作为分隔符，避免使用单个 `\`。

### 3. 运行程序（两种方式）
#### 方式一：源码运行
在项目根目录打开命令行，执行以下命令：
```bash
python main.py
```

#### 方式二：EXE 运行（推荐）
1.  下载打包好的 EXE 压缩包，解压到任意目录；
2.  确保解压后目录包含 `assets/`、`ui/`、`steam/` 和 `config.json`；
3.  双击 `Steam游戏时间统计.exe` 运行；
4.  运行后托盘区会出现图标，左键点击打开统计面板，右键点击查看菜单。

## 界面操作说明
1.  **统计面板**：左侧显示今日/本周游玩时长和实时运行日志，右侧显示所有游戏的时长统计表格；
2.  **表格交互**：鼠标悬浮在游戏名称上，可查看该游戏最近一次的打开/关闭时间；
3.  **主题切换**：修改 `ui/main_window.py` 中的主题调用方法，可切换不同界面风格；
4.  **退出程序**：右键点击托盘图标，选择「退出」，即可正常终止程序（直接关闭统计面板仅隐藏窗口，程序仍在后台运行）。

## 打包为 EXE（自定义打包）
若需自行打包为 EXE 文件，步骤如下：
1.  安装打包工具：
  ```bash
  pip install pyinstaller
  ```
2.  在项目根目录执行打包命令：
  ```bash
  pyinstaller -w -F -i assets/tray.ico --add-data "assets;assets" --add-data "ui;ui" --add-data "steam;steam" --add-data "config.json;." --add-data "utils;utils" --name "Steam Game PlayTime Tracker" main.py
  ```
3.  打包完成后，在 `dist/` 目录下找到生成的 EXE 文件，将 `config.json` 复制到同目录即可运行。

## 常见问题
### Q1：运行后无托盘图标，或提示「未找到 Steam 配置」？
A1：检查 `config.json` 文件是否存在，且 `steam_path` 配置正确，确保 Steam 安装目录下存在 `steamapps` 文件夹。

### Q2：统计面板无数据，日志也无输出？
A2：
1.  确保以**管理员身份**运行程序；
2.  检查 `data/` 目录是否有读写权限，是否生成了 `playtime.json`；
3.  确认 Steam 游戏已被正确扫描，终端是否输出「扫描到 Steam 游戏数量」。

### Q3：打包后的 EXE 无法运行，提示模块缺失？
A3：打包命令中补充 `--hidden-import` 参数，指定缺失的模块，例如：
```bash
pyinstaller -w -F -i assets/tray.ico --hidden-import steam --hidden-import ui --hidden-import utils --hidden-import PySide6 --add-data "assets;assets" main.py
```

### Q4：游玩时长统计不准确？
A4：程序基于游戏进程启停统计，若游戏进程名称与 Steam 清单不一致，可能导致统计偏差，可检查 `steam/game_scanner.py` 中的 `EXE_BLACKLIST` 排除无关进程。

## 许可证
本项目为开源学习项目，仅供个人非商业使用，禁止用于商业盈利目的。

---

## 英文版（English Version）
# Steam Game Playtime Tracker
A lightweight tool for monitoring and statistics of Steam game playtime, developed based on Python + PySide6. It supports system tray residency, automatic game scanning, process monitoring, playtime statistics, and beautiful graphical interface display. No complex configuration is required, and it can be run directly after packaging.

## Features
1.  **Automatic Steam Game Scanning**: Reads the game manifest under the Steam installation directory, automatically collects game executable files, names and other information without manual addition.
2.  **Real-time Process Monitoring**: Silently monitors game process startup and shutdown in the background, accurately records the playtime of each game, and avoids misjudgment of processes with the same name.
3.  **Multi-dimensional Playtime Statistics**: Supports playtime statistics by "Today/This Week/Total", with adaptive format (10s, 2m2s, 1h2m2s).
4.  **System Tray Residency**: Runs lightweight without occupying desktop space. Left-click to open the statistics panel, and right-click the menu to view the today's ranking.
5.  **Beautiful Graphical Interface**: Supports switching between multiple high-value themes (Dark/Light/Fresh Blue-White/Morandi Pink-Gray/Tech Silver-Gray), with clear and intuitive data tables.
6.  **Persistent Data Storage**: Playtime data is automatically saved to `data/playtime.json` and will not be lost after the program restarts.
7.  **Support for Packaging as EXE**: Can be packaged into an independent executable file, which can run directly on the Windows system without relying on the Python environment.

## Project Structure
```
Tracker/  # Project root directory
├── main.py  # Program entry file
├── tray.py  # System tray function module
├── config.json  # Steam path configuration file
├── README.md  # English documentation
├── README_CN.md  # Chinese documentation
├── assets/  # Resource folder (stores icons)
│   ├── tray.ico  # Tray icon
│   └── open_panel.ico  # Open statistics panel menu icon
├── ui/  # Graphical interface module directory
│   └── main_window.py  # Main statistics window implementation
├── steam/  # Core function module directory
│   ├── game_scanner.py  # Steam game scanning tool
│   └── process_watcher.py  # Game process monitoring and playtime statistics
├── utils/  # tool directory
│   └── utils.py  # tool
└── data/  # Data storage directory (automatically generates playtime data)
    └── playtime.json  # Playtime persistence file (automatically generated after program runs)
```

## Quick Start
### 1. Environment Preparation (Run from Source Code)
- Supports Python 3.8 and above
- Install dependent libraries:
  ```bash
  pip install requirements.txt
  ```

### 2. Configure Steam Path
1.  Open the `config.json` file in the project root directory;
2.  Modify `steam_path` to your Steam installation directory (example as follows):
  ```json
  {
      "steam_path": "D:/Steam"
  }
  ```
  > Note: Use `/` or `\\` as the path separator, avoid using a single `\`.

### 3. Run the Program (Two Ways)
#### Way 1: Run from Source Code
Open the command line in the project root directory and execute the following command:
```bash
python main.py
```

#### Way 2: Run as EXE (Recommended)
1.  Download the packaged EXE compressed package and extract it to any directory;
2.  Ensure that the extracted directory contains `assets/`, `ui/`, `steam/` and `config.json`;
3.  Double-click `Steam Game Playtime Tracker.exe` to run it as **Administrator** (administrator privileges are required to read processes and write data);
4.  After running, an icon will appear in the tray area. Left-click to open the statistics panel, and right-click to view the menu.

## Interface Operation Instructions
1.  **Statistics Panel**: The left side displays today's/this week's playtime and real-time running logs, and the right side displays the playtime statistics table of all games;
2.  **Table Interaction**: Hover the mouse over the game name to view the last open/close time of the game;
3.  **Theme Switching**: Modify the theme calling method in `ui/main_window.py` to switch different interface styles;
4.  **Exit the Program**: Right-click the tray icon and select "Exit" to terminate the program normally (directly closing the statistics panel only hides the window, and the program still runs in the background).

## Package as EXE (Custom Packaging)
If you need to package it into an EXE file by yourself, the steps are as follows:
1.  Install the packaging tool:
  ```bash
  pip install pyinstaller
  ```
2.  Execute the packaging command in the project root directory:
  ```bash
  pyinstaller -w -F -i assets/tray.ico --add-data "assets;assets" --add-data "ui;ui" --add-data "steam;steam" --add-data "config.json;." --add-data "utils;utils" --name "Steam Game Playtime Tracker" main.py
  ```
3.  After packaging is completed, find the generated EXE file in the `dist/` directory, and copy `config.json` to the same directory to run.

## Frequently Asked Questions
### Q1: No tray icon after running, or prompt "Steam configuration not found"?
A1: Check if the `config.json` file exists and the `steam_path` is configured correctly, and ensure that the `steamapps` folder exists under the Steam installation directory.

### Q2: No data in the statistics panel and no output in the log?
A2:
1.  Ensure that the program is run as **Administrator**;
2.  Check if the `data/` directory has read and write permissions and whether `playtime.json` is generated;
3.  Confirm that the Steam games have been scanned correctly, and whether the terminal outputs "Number of scanned Steam games".

### Q3: The packaged EXE cannot run and prompts that the module is missing?
A3: Add the `--hidden-import` parameter to the packaging command to specify the missing modules, for example:
```bash
pyinstaller -w -F -i assets/tray.ico --hidden-import steam --hidden-import ui --hidden-import utils --hidden-import PySide6 --add-data "assets;assets" main.py
```

### Q4: Inaccurate playtime statistics?
A4: The program counts based on game process startup and shutdown. If the game process name is inconsistent with the Steam manifest, it may lead to statistical deviations. You can check the `EXE_BLACKLIST` in `steam/game_scanner.py` to exclude irrelevant processes.

## License
This project is an open-source learning project, for personal non-commercial use only, and prohibited for commercial profit purposes.