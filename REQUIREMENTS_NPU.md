# Intel NPU 搭載 PC 向け Python 版 DN_SuperBook_PDF_Converter 要件定義書

作成日: 2026-01-26  
対象リポジトリ: 本リポジトリ (DN_SuperBook_PDF_Converter_NPUver)  
元プロジェクト: https://github.com/dnobori/DN_SuperBook_PDF_Converter

## 1. 目的・背景
- 元の C# プロジェクト (DN_SuperBook_PDF_Converter) をフォークし、Intel 製 NPU 搭載 PC 上で動作する Python プロジェクトとして再構築する。
- スキャン書籍 PDF の高品質化 (鮮明化、傾き補正、余白調整、ページ番号整合、見開き/縦書き対応) と OCR/AI-OCR 出力の機能価値を維持する。
- NPU を活用した推論で GPU/CUDA 前提を減らし、Intel プラットフォーム上での運用性を高める。

## 2. スコープ
### 2.1. 対象範囲 (必須)
- Python 3.11 以上で動作する CLI ツールとして実装する。
- 主要処理フロー (PDF 解析 → 画像処理 → AI 鮮明化 → OCR → メタデータ再適用 → 出力) を Python で再構築する。
- Intel NPU を利用可能な推論バックエンドを採用し、NPU 未搭載環境では CPU へフォールバックする。
- 既存の出力形式 (PDF / HTML / Markdown / JSON) を維持する。

### 2.2. 対象範囲外 (除外)
- 既存の C# GUI/CLI 実装の継続保守。
- macOS / Linux 向けの GPU/NPU 最適化。
- 商用利用のライセンス調整や課金システムの実装。

## 3. ユーザー要件
- 書籍スキャン PDF を入力として、読みやすい PDF と OCR 出力を得たい。
- Intel 製 NPU 搭載 PC で GPU 不要、あるいは GPU がなくても高速に処理したい。
- OCR で日本語が高精度に認識され、検索可能 PDF とテキスト出力が得られる。
- 既存 CLI に近い操作感 (例: ConvertPdf コマンド相当) を維持したい。

## 4. 機能要件
### 4.1. 入出力
- 入力: 1 つ以上の PDF ファイル (ディレクトリ指定可、再帰検索対応)。
- 出力:
  - 高品質化 PDF (ページ番号整合、見開き/縦書きフラグ含む)
  - OCR 結果の検索可能 PDF
  - OCR 結果の HTML / Markdown / JSON

### 4.2. 画像処理
- ページの傾き補正、オフセット補正、余白統一トリミング。
- ページ番号検出と論理ページ番号の一致処理。
- 見開き用の左右判別と縦書き判定フラグの付与。

### 4.3. AI 鮮明化 (NPU 連携)
- Real-ESRGAN 相当の画像鮮明化を NPU 対応モデルで実行。
- 推論バックエンド:
  - Intel OpenVINO もしくは Intel NPU 対応の推論ランタイムを採用。
  - NPU 利用可否の自動判定。
  - NPU 不可時は CPU へフォールバック。

### 4.4. OCR
- 既存の高精細 OCR 相当の日本語対応を維持。
- OCR 結果を PDF へ再埋め込みし、既存メタデータを保持。
- OCR 出力の構造化 (見出し、段組み、表など) を可能な範囲で維持。

### 4.5. CLI/設定
- `convertpdf` 相当の CLI を提供 (引数で OCR や出力形式を指定)。
- 設定は CLI 引数と設定ファイル (YAML または JSON) を併用。
- 進捗表示とログ出力 (INFO/WARN/ERROR) を提供。

## 5. 非機能要件
### 5.1. 性能
- NPU 利用時、従来 GPU (CUDA) 依存に比べて実用的な速度を確保。
- CPU フォールバック時でもクラッシュせず完走する。

### 5.2. 互換性
- OS: Windows 11 x64 (Intel NPU 搭載 PC) を最優先。
- Python: 3.11 以上。
- 入力 PDF のページ数が多い場合でも安定動作する。

### 5.3. 安定性・保守性
- 1 冊 (数百ページ) の変換でもメモリリークや異常終了が起きない。
- 主要処理ステージごとにエラー復旧/リトライ方針を設ける。

### 5.4. セキュリティ
- 外部ツール呼び出しはパスを明示し、コマンドインジェクションを防止。
- OCR 出力やログに個人情報が含まれないよう配慮。

## 6. 想定技術スタック (案)
- 画像処理: Pillow, OpenCV
- AI 鮮明化: OpenVINO 対応の超解像モデル (Real-ESRGAN 相当)
- OCR: Tesseract + 日本語モデル、または OpenVINO 対応 OCR
- PDF 操作: PyPDF2 / pikepdf / pdfcpu 互換 API
- CLI: Typer または Click

## 7. 受け入れ条件
- Intel NPU 搭載 Windows 11 環境でサンプル PDF を変換できる。
- NPU が無効/未搭載でも CPU で処理が完走する。
- 出力 PDF がページ番号整合・見開き/縦書きフラグを保持する。
- OCR 出力が HTML / Markdown / JSON で得られる。

## 8. 移行・開発計画 (案)
1. 既存 C# 実装の処理フロー整理と Python 版設計。
2. PDF 分解・画像処理・メタデータ操作の Python 実装。
3. NPU 対応 AI 鮮明化モデルの検証と組み込み。
4. OCR と出力フォーマット生成。
5. CLI/設定/ログ実装。
6. 結合テストと性能検証。

