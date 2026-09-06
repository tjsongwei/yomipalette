[English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

# YomiPalette

用喜欢的声音，把电子书变成有声书。

Android/iOS Flutter客户端作为独立项目保存在[`mobile/`](mobile/README.zh-CN.md)。由于客户端凭据安全和SDK可用性的差异，移动版支持的提供商范围有所不同。

一款将 TXT、EPUB 或 PDF 文件中的文本转换为 MP3 语音的桌面应用，支持 Windows 和 macOS。

## 主要功能

- 从 TXT / EPUB / PDF / MOBI / AZW / AZW3 文件中提取文本
- 按 EPUB 章节生成 MP3
- 按指定字符数生成 MP3
- 选择语言和音色
- 使用所选输出单元生成试听音频
- 调整语速、音量和音调
- 自动分割长文本
- 后台生成并支持取消
- 在日语、英语和简体中文之间切换界面

## 支持的语音提供商

| 提供商 | 认证信息 |
| --- | --- |
| Edge TTS | 无需认证 |
| Microsoft Azure Speech | API 密钥和区域 |
| Google Cloud Text-to-Speech | API 密钥或服务账号 JSON |
| OpenAI TTS | API 密钥 |

## 下载

请从[最新的 GitHub Release](https://github.com/tjsongwei/yomipalette/releases/latest)下载适合您操作系统的文件。

已发布的 v0.1.7 及更早版本仍使用旧名称 `TTS-Text-MP3` 的文件名和应用名称。下方的 `YomiPalette` 文件名适用于今后的版本。

### Windows

| 文件 | 用途 |
| --- | --- |
| `YomiPalette_Setup_<version>.exe` | 标准安装版，支持开始菜单快捷方式和卸载 |
| `YomiPalette_Windows_Portable_<version>.zip` | 免安装版；解压 ZIP 后运行 `YomiPalette.exe` |

建议使用 Setup 版。使用 Portable 版时，请先将整个 ZIP 解压到文件夹，再启动应用。

### macOS

请选择与 Mac 类型相匹配的 DMG 或 ZIP。

| 文件名包含 | 适用的 Mac |
| --- | --- |
| `arm64` | Apple Silicon Mac（M1、M2、M3、M4 或更高版本） |
| `x86_64` | Intel Mac |

- DMG：打开磁盘映像使用应用
- ZIP：解压后使用 `.app`

当前 macOS 版未经 Apple 代码签名或公证。如果首次启动时 macOS 显示警告，请在 Finder 中按住 Control 键点击应用，然后选择“打开”。

## 基本用法

1. 选择 TTS 提供商。
2. 如有需要，在“设置...”中输入认证信息。
3. 选择 TXT、EPUB 或 PDF 文件。
4. 设置输出文件夹、语言、音色、语速等选项。
5. 如有需要，使用“试听”。
6. 点击“开始生成 MP3”。

### MP3 分割方式

- “按章节”根据 EPUB 目录的顶层章节生成 MP3；章标题页与正文即使位于不同文件也会合并，子节归入父章节。桌面版与移动版使用相同规则。
- 前置内容以及可根据标题或 EPUB 信息识别的补注、版权页等会保留为独立选项。默认全部勾选，可取消不需要朗读的项目。无法明确识别的后续正文仍归入章节；部分目录链接失效不会影响其他有效章节。锚点缺失且该文件没有有效章节起点时，以文件开头作为分界；完全没有可用目录时，按内部文件保留正文。
- “按字符数”会合并 TXT、EPUB 或 PDF 正文，并分割为从 `Part 001` 开始的连续 MP3 文件。默认上限为 5000 个字符。
- 字符数以处理后的文本为准；空格和换行各计一个字符。优先在限制内最后一个句末或换行处分割。没有合适边界时，会在上限处分割。
- 所选分割方式和字符数会在下次启动时恢复。

“试听”会根据所选输出单元生成约 15 秒的样本。如果未选择任何单元，则使用第一个。实际时长会因语言、音色和语速而有所不同。

Edge TTS 无需认证信息即可使用。

### 界面语言

使用窗口顶部的“界面语言”可在日语、英语和简体中文之间切换。首次启动时，应用会使用操作系统语言；对于不支持的语言，会默认显示英语。您的选择会保存并在以后启动时恢复。

## 认证信息和配置

请在“设置...”中输入 Azure、Google 和 OpenAI 认证信息。这些信息以明文保存在以下位置：

- Windows：`%USERPROFILE%\.tts-text-mp3\config.json`
- macOS：`~/.tts-text-mp3/config.json`

请勿提交或共享 API 密钥、`config.json` 或 Google 服务账号 JSON 文件。发布包和 GitHub Release 中不包含认证信息。

## 从源代码运行

请使用 Python 3.10 或更高版本。

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## 在本地构建发布包

### Windows

需要 PowerShell、PyInstaller 和 Inno Setup 6。

```powershell
python -m pip install -r requirements.txt pyinstaller
.\scripts\build_windows.ps1 -Version "dev"
```

Setup 安装程序和 Portable ZIP 会生成在 `release/` 目录中。

### macOS

请在 macOS 上运行。

```bash
python -m pip install -r requirements.txt pyinstaller
bash scripts/build_macos.sh dev
```

当前 Mac 架构对应的 `.app` ZIP 和 DMG 会生成在 `release/` 目录中。

## 创建 GitHub Release

推送以 `v` 开头的标签后，GitHub Actions 会构建 Windows Setup、Windows Portable、macOS Apple Silicon 和 macOS Intel 版本，并将它们附加到 Release。

```bash
git tag v0.2.0
git push origin v0.2.0
```

工作流位于 `.github/workflows/release.yml`。它不保存提供商认证信息，并且仅使用标准 GitHub Actions `GITHUB_TOKEN` 和 `contents: write` 权限创建 Release。

## 当前限制

- macOS 版未签名且未公证。
- Windows 版未进行代码签名，因此 SmartScreen 可能显示警告。
- 提供商的费用、字符限制和地区限制均遵循各服务的条款。
- macOS 应用图标目前尚未设置。

## 许可证

本项目根据 [MIT License](LICENSE) 发布。

Copyright (c) 2026 YuluEthan

## 支持 YomiPalette 开发

如果 YomiPalette 对您有帮助，欢迎支持项目的持续开发。您的支持将用于功能改进、问题修复以及 Windows 和 Android 的兼容性测试。支持完全自愿，不影响您可以使用的应用功能。

- [通过 GitHub Sponsors 支持开发](https://github.com/sponsors/tjsongwei)
- [通过 Buy Me a Coffee 支持开发](https://buymeacoffee.com/tjsongweic)

## PDF导入

支持含文本的PDF。“按章节／页”按原始页序生成 `Page 001` 等单元；“按字符数”先合并所有提取的页面文本再分割。不根据PDF书签划分章节。无文本的页面（空白或纯图片）会被跳过，标题保留原始页码。

暂不支持OCR。无法读取纯图片或扫描PDF；混合文档只提取其中的文本页面。不支持需要输入密码的PDF。竖排、多栏、表格及特殊字体的阅读顺序或提取结果可能不准确。PDF文本在设备上提取；语音生成遵循所选TTS服务的通常行为。

## Kindle 导入（MOBI / AZW / AZW3）

支持 Kindle 的 MOBI、AZW 和 AZW3 文件。**AZW3 中嵌入 KF8（EPUB）**时，会按照与桌面 EPUB 相同的章节结构拆分。**较老的 MOBI / AZW** 格式没有可靠的目录信息，因此整个文件会作为单一章节读取（仍可通过“按字符数”拆分）。

无法读取受 DRM 保护的 Kindle 文件（如从 Kindle 商店购买的内容）。请使用已去除 DRM 的副本（例如通过 Calibre 等工具转换本人拥有的文件）。其他限制：不支持印刷版 Kindle（PDF 固定排版），音频、视频、固定版式与词典条目将被忽略。文本在设备上提取；语音生成遵循所选 TTS 服务的通常行为。
