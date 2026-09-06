[English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

# YomiPalette

電子書籍を、好きな声で。

TXT・EPUB・PDFファイルを読み込み、文章をMP3音声へ変換するデスクトップアプリです。WindowsとmacOSに対応しています。

Android・iOS向けのモバイル版は、同一リポジトリ内の別プロジェクトとして[`mobile/README.ja.md`](mobile/README.ja.md)で開発しています。モバイル版では認証情報の安全性とSDKの違いにより、一部プロバイダの対応範囲が異なります。

## 主な機能

- TXT / EPUB / PDF / MOBI / AZW / AZW3からのテキスト抽出
- EPUBの章ごとのMP3出力
- 指定文字数ごとのMP3出力
- 言語・ボイスの選択
- 選択した出力単位を使った音声確認
- 読み上げ速度、音量、ピッチの調整
- 長文の自動分割
- バックグラウンド生成とキャンセル
- UIの日本語・英語・簡体中国語切り替え

## 対応プロバイダ

| プロバイダ | 認証情報 |
| --- | --- |
| Edge TTS | 不要 |
| Microsoft Azure Speech | APIキーとリージョンが必要 |
| Google Cloud Text-to-Speech | APIキーまたはサービスアカウントJSONが必要 |
| OpenAI TTS | APIキーが必要 |

## ダウンロード

[最新のGitHub Release](https://github.com/tjsongwei/yomipalette/releases/latest)から、お使いのOSに合ったファイルをダウンロードしてください。

v0.1.7までの公開済み配布物は、旧名称 `TTS-Text-MP3` のファイル名・アプリ名のままです。下記の `YomiPalette` のファイル名は今後のリリースから適用します。

### Windows

| ファイル | 用途 |
| --- | --- |
| `YomiPalette_Setup_<version>.exe` | 通常のインストール版。スタートメニューへの登録とアンインストールに対応 |
| `YomiPalette_Windows_Portable_<version>.zip` | インストール不要版。ZIPを展開して `YomiPalette.exe` を実行 |

通常はSetup版がおすすめです。Portable版を使う場合は、ZIP内から直接起動せず、最初に任意のフォルダへすべて展開してください。

### macOS

Macの種類に合ったDMGまたはZIPを選んでください。

| ファイル名に含まれる表記 | 対象Mac |
| --- | --- |
| `arm64` | Apple Silicon搭載Mac（M1、M2、M3、M4以降） |
| `x86_64` | Intel搭載Mac |

- DMG：開いてアプリを利用する配布形式
- ZIP：展開して `.app` を利用する形式

現在のmacOS版はAppleによるコード署名・公証を行っていません。初回起動時にmacOSの警告が表示された場合は、FinderでアプリをControlキーを押しながらクリックし、「開く」を選択してください。

## 基本的な使い方

1. 使用するTTSプロバイダを選択します。
2. 必要な場合は「設定...」から認証情報を入力します。
3. TXT・EPUB・PDFファイルを選択します。
4. 出力フォルダ、言語、ボイス、速度などを設定します。
5. 必要に応じて「音声確認」を実行します。
6. 「MP3生成 開始」を押します。

### MP3の分割方法

- 「章ごと」は、EPUBの目次の最上位の章ごとにMP3を生成します。章扉と本文が別ファイルでも結合し、下位の節は親の章に含めます。デスクトップ・モバイル共通の動作です。
- 前付けや、見出し・EPUB情報から判別できる補註・奥付などは別項目として残します。初期状態ではすべて選択されるため、不要な項目はチェックを外してください。判別できない続きの本文は章に含め、目次の一部に参照切れがあっても、有効な章構成は維持します。アンカーが見つからず、そのファイルに有効な章開始位置がない場合はファイル先頭で区切ります。有効な目次がない場合は内部ファイル単位で本文を保持します。
- 「文字数ごと」は、TXT・EPUB・PDFの本文全体を指定文字数以内に分割し、`Part 001`からの連番MP3を生成します。初期値は5000文字です。
- 文字数は読み込み後の本文で数え、空白と改行も1文字とします。指定文字数以内の最後の句点または改行を優先し、区切りがない長文は指定文字数で分割します。
- 選択した分割方法と文字数は、次回起動時に復元されます。

「音声確認」は、出力単位の一覧で選択中の部分から約15秒分のサンプルを生成します。何も選択していない場合は、最初の出力単位を使用します。実際の長さは言語、ボイス、読み上げ速度によって前後します。

Edge TTSは認証情報なしですぐに使用できます。

### 表示言語

画面上部の「表示言語」から日本語、English、簡体中文を切り替えられます。初回起動時はOSの言語を使用し、対応外の言語では英語を表示します。選択した言語は次回起動時にも復元されます。

## 認証情報と設定ファイル

Azure、Google、OpenAIの認証情報はGUIの「設定...」から入力します。設定は次の場所に平文で保存されます。

- Windows：`%USERPROFILE%\.tts-text-mp3\config.json`
- macOS：`~/.tts-text-mp3/config.json`

APIキー、`config.json`、GoogleのサービスアカウントJSONをGitへコミットしたり、他人と共有したりしないでください。これらの認証情報は配布ファイルやGitHub Releaseには含まれていません。

## ソースコードから実行する

Python 3.10以降を使用してください。

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

## 配布ファイルをローカルでビルドする

### Windows

PowerShell、PyInstaller、Inno Setup 6が必要です。

```powershell
python -m pip install -r requirements.txt pyinstaller
.\scripts\build_windows.ps1 -Version "dev"
```

`release/` にSetup.exeとPortable ZIPが作成されます。

### macOS

macOS上で実行してください。

```bash
python -m pip install -r requirements.txt pyinstaller
bash scripts/build_macos.sh dev
```

実行したMacのアーキテクチャ向けに、`.app`のZIPとDMGが `release/` に作成されます。

## GitHub Releaseを作成する

`v`で始まるタグをpushすると、GitHub ActionsがWindows Setup版、Windows Portable版、macOS Apple Silicon版、macOS Intel版をビルドしてReleaseへ添付します。

```bash
git tag v0.2.0
git push origin v0.2.0
```

ワークフローは `.github/workflows/release.yml` にあります。認証情報は登録せず、Release作成にはGitHub Actions標準の `GITHUB_TOKEN` と `contents: write` 権限だけを使用します。

## 現在の制限事項

- macOS版は未署名・未公証です。
- Windows版もコード署名していないため、環境によってはSmartScreenの警告が表示される場合があります。
- TTSプロバイダの利用料金、文字数制限、地域制限は各サービスの条件に従います。
- macOS版のアプリアイコンは現在未設定です。

## ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。

Copyright (c) 2026 YuluEthan

## YomiPaletteの開発を応援する

YomiPaletteが役に立ったら、開発の継続を応援していただけるとうれしいです。いただいた支援は、機能改善・不具合修正・Windows／Androidでの動作検証に役立てます。支援は任意で、支援の有無によって利用できる機能は変わりません。

- [GitHub Sponsorsで開発を応援する](https://github.com/sponsors/tjsongwei)
- [Buy Me a Coffeeで開発を応援する](https://buymeacoffee.com/tjsongweic)

## PDFの読み込み

テキスト入りPDFに対応しています。「章・ページごと」ではページ順に `Page 001` などの単位を作り、「文字数ごと」では抽出した全ページの本文を連結して分割します。PDFのしおりによる章分けは行いません。文字のないページ（空白・画像のみ）は省略し、タイトルには元のページ番号を残します。

OCRは未対応です。画像・スキャンのみのPDFからは読み込めず、画像ページとテキストページが混在する場合はテキスト部分だけが対象です。パスワード入力が必要なPDFには対応していません。縦書き・段組み・表・特殊なフォントは、読み順や抽出結果が崩れる場合があります。PDFの文字は端末内で抽出し、音声生成時は選択したTTSプロバイダの通常の動作に従います。

## Kindleの読み込み（MOBI / AZW / AZW3）

KindleのMOBI・AZW・AZW3ファイルに対応しています。**AZW3でKF8（EPUB）が埋め込まれている場合**は、デスクトップのEPUBと同じ章構造で分割します。**古いMOBI・AZW**は目次情報が安定して取り出せないため、ファイル全体=1チャプターとして読み込みます（その場合でも「文字数ごと」での分割は可能です）。

DRM付きKindleファイル（Kindleストアで購入したものなど）は読み込めません。DRMを解除したコピー（自分が所有するファイルをCalibreなどで変換したもの）を使用してください。その他の制限：印刷用Kindle（PDFレイアウト固定）は非対応、音声・動画・固定レイアウト・辞書エントリは無視されます。文字は端末内で抽出し、音声生成時は選択したTTSプロバイダの通常の動作に従います。
