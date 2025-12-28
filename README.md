<h1 align="center">NetEase Music Converter (NCM Converter)</h1>

<p align="center">
    <strong>🎵 简单的网易云音乐 NCM 格式转换工具</strong>
    <br />
    将加密的 NCM 文件转换为 MP3/FLAC，保留元数据与封面。
    <br />
</p>


<!-- BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/GUI-PySide6-green.svg?style=flat-square&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-lightgrey.svg?style=flat-square" alt="Platform">
</p>

---

## 目录

- [功能特性](#功能特性)
- [系统要求与依赖](#系统要求与依赖)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
  - [图形界面 (GUI)](#图形界面-gui)
  - [命令行 (CLI)](#命令行-cli)
- [项目结构](#项目结构)
- [注意事项](#注意事项)
- [致谢](#致谢)
- [贡献](#贡献)

---

## 功能特性

| 功能 | 描述                                       |
| :--- |:-----------------------------------------|
| 🔓 **NCM 解密** | 快速解密网易云音乐加密的 `.ncm` 文件                   |
| 🔄 **格式转换** | 支持转换为 **MP3**、**FLAC** 等通用音频格式           |
| 🏷️ **元数据保留** | 完整保留歌曲标题、艺术家、专辑名称等元数据信息                  |
| 🖼️ **封面提取** | 自动提取并嵌入专辑封面图片                            |
| 🖥️ **双模式支持** | 提供现代化的 **图形界面 (GUI)** 和高效的 **命令行 (CLI)** |
| 👁️ **预览功能** | 转换前查看文件详情，内置简易播放器预览转换后的音频                |
| 🖱️ **拖拽支持** | 支持直接拖拽文件到界面进行处理                          |

---

## 系统要求与依赖

### 环境要求
*   **Python**: 3.14 
*   **操作系统**:
    *   Windows 7+ （支持 Qt6/PySide6）

### 核心依赖库
该项目依赖以下库：
*   [`mutagen`](https://github.com/quodlibet/mutagen) - 音频数据处理
*   [`pillow`](https://python-pillow.org/) - 图像处理
*   [`pycryptodome`](https://www.pycryptodome.org/) - 核心解密算法
*   [`pyside6`](https://doc.qt.io/qtforpython/) - 现代化 GUI 界面
*   [`pyinstaller`](https://pyinstaller.org/) - 可执行文件打包

---

## 快速开始

### 方法一：Git 克隆与安装

```bash
# 克隆仓库
git clone https://github.com/your-username/NetEaseMusicConverter.git
cd NetEaseMusicConverter

# 安装依赖 (使用 uv 或 pip)
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

如果您希望生成无需 Python 环境即可运行的可执行文件：

```bash
# 使用配置文件 (推荐，包含完整资源配置，打包 GUI 版本)
pyinstaller NCM_Converter.spec

# 打包 GUI 版本
pyinstaller --onefile --windowed --icon=resources/NCMCicon.ico gui.py

# 打包 CLI 版本
pyinstaller --onefile cli.py
```

打包完成后的文件将位于 `dist/` 目录下。

### 方法二：从 release 下载并安装预打包版本（目前仅限 GUI）

下载 `exe` 文件后双击运行。

---

## 使用指南

### 图形界面 (GUI)

适合大多数用户，操作直观便捷。

```bash
python gui.py
```

功能亮点：

*   📂 **文件导入**：点击按钮选择或直接拖拽 NCM 文件进入窗口。
*   🎵 **预览播放**：内置播放器可在导出后试听。
*   📊 **状态监控**：实时进度条显示转换状态。

### 命令行 (CLI)

适合开发者或需要批处理脚本的用户。

```bash
# 基础转换 (默认输出到同目录)
python cli.py input.ncm

# 指定输出路径
python cli.py input.ncm -o /path/to/music/output.mp3

# 仅预览信息 (不进行解密)
python cli.py input.ncm -p
```

参数说明：

*   `input.ncm`: 输入文件路径
*   `-o, --output`: (可选) 输出文件路径
*   `-p, --preview`: (可选) 预览模式，仅读取元数据

---

## 项目结构

```
NetEaseMusicConverter/
├── codec/                  # 核心解码逻辑
│   └── ncm_codec.py        # NCM 解密算法实现
├── controller/             # 控制器
│   ├── cli_controller.py
│   └── gui_controller.py
├── domain/                 # 模型与异常定义
│   ├── exceptions.py
│   └── models.py
├── gui/                    # UI 界面层
│   ├── main_window.py      # 主窗口实现
│   └── widgets.py          # 自定义 UI 组件
├── session/                # 解密会话管理
│   └── decryption_session.py
├── resources/              # 静态资源
├── cli.py                  # CLI 程序入口
├── gui.py                  # GUI 程序入口
├── NCM_Converter.spec      # PyInstaller 打包配置
├── version_info.txt        # PyInstaller 文件版本信息
└── pyproject.toml          # 依赖列表
```

---

## 注意事项

[!IMPORTANT]
请务必阅读以下内容：

*   本项目仅供 **个人学习研究** 使用。
*   请严格遵守相关版权法律法规。
*   转换后的音频文件 **仅限个人使用与备份**，严禁用于任何商业用途。
*   使用本工具产生的任何法律后果由使用者自行承担。

---

## 致谢

ncm 文件解密算法参考自 anonymous5l 及 taurusxin/ncmdump 项目。

---

## 贡献

欢迎您的贡献！如果您发现 Bug 或有新功能建议，请提交 Issue 或 Pull Request。
