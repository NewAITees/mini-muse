# mini-muse プロジェクト環境情報

このドキュメントは、AI（Claude）が作業を進める際に参照する環境情報をまとめたものです。

**最終更新**: 2025-10-20

---

## プロジェクト概要

**名前**: mini-muse
**目的**: ComfyUIベースの画像生成システム
**主な機能**:
- プロンプト自動生成（テンプレートベース）
- ComfyUI APIを使用した画像生成
- バッチ処理（1枚～任意の枚数）
- 日付別フォルダへの自動整理＋CSVログ記録
- **NEW**: Ollama LMMを使用した画像→プロンプト生成

---

## ディレクトリ構造

```
/home/perso/analysis/mini-muse/
├── mini_muse/                    # メインパッケージ
│   ├── __pycache__/
│   ├── comfyui_client.py         # ComfyUI APIクライアント (19,344 bytes)
│   ├── prompt_generator.py       # プロンプト生成器 (17,829 bytes)
│   └── ollama_prompt.py          # Ollama画像分析モジュール (NEW - Step 2)
├── prompts/                      # プロンプトテンプレート（15ファイル）
│   ├── prompt_elements.json      # デフォルト（ミニチュア/ジオラマ）
│   ├── prompt_templates_抽象画_20250117.json
│   ├── prompt_templates_抽象画_enhanced_20250117.json
│   ├── prompt_templates_抽象画_final_20250117.json
│   ├── prompt_templates_抽象悪夢_20250122.json
│   ├── prompt_templates_Tシャツデザイン_20250127.json
│   └── その他のテンプレートファイル...
├── workflows/                    # ComfyUIワークフロー
│   └── sd3.5_large_turbo_upscale.json
├── tests/                        # テストスクリプト
│   ├── test_comfyui_client.py
│   ├── test_prompt_generator.py
│   ├── test_integration.py
│   ├── test_generate.py
│   ├── test_simple_generate.py
│   └── test_ollama_prompt.py     # Ollama画像分析テスト (NEW - Step 2)
├── config/
│   └── config.yaml               # プロジェクト設定ファイル
├── doc/
│   └── CHANGELOG_20251015163942.md
├── input/                        # 入力ファイル置き場
├── output/                       # 出力ファイル置き場
├── metadata/                     # メタデータ保存場所
├── processed/                    # 処理済みファイル
├── processing/                   # 処理中ファイル
├── failed/                       # 失敗ファイル
├── weights/                      # モデルウェイト
├── .venv/                        # 仮想環境
├── .cache/
├── .git/
├── generate_images.py            # バッチ画像生成メインスクリプト (11,168 bytes)
├── test_placeholder_resolution.py
├── sample.jpg
├── loadimage_min.json
├── README.md                     # プロジェクトREADME
├── pyproject.toml                # uv プロジェクト設定
├── uv.lock                       # uv 依存関係ロック
└── TensorRT/                     # シンボリックリンク？
```

---

## 既存の主要ファイル

### 1. mini_muse/comfyui_client.py

**目的**: ComfyUI APIクライアント
**主要クラス**: `ComfyUIClient`
**主要メソッド**:
- `__init__(server_address="127.0.0.1:8188")`
- `load_workflow(workflow_path: str) -> Dict`
- `queue_prompt(workflow: Dict) -> str`
- `wait_for_completion(prompt_id: str, timeout=300) -> Dict`
- `get_image(filename, subfolder, folder_type) -> bytes`
- `update_prompt(workflow, positive_prompt, negative_prompt, seed, steps, cfg, width, height) -> Dict`
- `generate_image(workflow, positive_prompt, ..., save_path) -> bytes`

**依存関係**:
- `requests`
- `websocket`
- `json`, `time`, `pathlib`, `random`

**重要な仕様**:
- デフォルトサーバーアドレス: `127.0.0.1:8188`
- ワークフロー形式: ComfyUI API形式のJSON
- ノードID: 固定（3: KSampler, 16: Positive Prompt, 53: LatentImage, 54: Negative Prompt）

---

### 2. mini_muse/prompt_generator.py

**目的**: テンプレートベースのプロンプト生成
**主要クラス**: `PromptGenerator`, `LegacyPromptGenerator`（非推奨）
**主要メソッド**:
- `__init__(elements_file: Optional[str] = None)`
- `generate_prompt(template_name: Optional[str] = None) -> str`
- `generate_multiple_prompts(template_name, count=5) -> List[str]`
- `get_available_templates() -> List[str]`
- `get_template_info(template_name: str) -> Optional[Dict]`
- `get_available_elements() -> List[str]`
- `get_element_values(element_name: str) -> Optional[List[str]]`

**関数**:
- `list_available_template_files() -> List[str]`

**依存関係**:
- `json`, `random`, `re`, `pathlib`

**重要な仕様**:
- デフォルトパス: `prompts/prompt_elements.json`
- ファイル名のみ指定時は `prompts/` フォルダから検索
- テンプレート内のプレースホルダー（`{element_name}`）をランダム置換
- 同一ベース名のプレースホルダーは重複を避ける（`{color_1}`, `{color_2}` など）

---

### 3. generate_images.py

**目的**: バッチ画像生成メインスクリプト
**主要機能**:
- コマンドライン引数のパース
- プロンプト生成 + ComfyUI画像生成のバッチ実行
- 日付別フォルダへの自動整理（`YYYYMMDD/`）
- CSVログ記録（`generation_log_YYYYMMDD.csv`）

**コマンドライン引数**:
- `--count`, `-c`: 生成枚数（デフォルト: 1）
- `--template-file`: テンプレートファイル名
- `--template`, `-t`: テンプレート名
- `--list-templates`: テンプレートファイル一覧表示
- `--server`: ComfyUIサーバーアドレス（デフォルト: `127.0.0.1:8000`）
- `--workflow`: ワークフローファイル（デフォルト: `workflows/sd3.5_large_turbo_upscale.json`）
- `--steps`, `--cfg`, `--width`, `--height`, `--seed`
- `--output-dir`: 出力先（デフォルト: `stablediffusion/outputs`）
- `--negative-prompt`

**出力形式**:
```
stablediffusion/outputs/
└── YYYYMMDD/
    ├── template_name_YYYYMMDD_HHMMSS_0001.png
    ├── template_name_YYYYMMDD_HHMMSS_0002.png
    └── generation_log_YYYYMMDD.csv
```

**CSVログフィールド**:
- filename, template, positive_prompt, negative_prompt, seed, steps, cfg, width, height
- image_size_bytes, generation_time_seconds, timestamp

---

### 4. tests/

既存のテストファイル:
- `test_comfyui_client.py` (11,695 bytes)
- `test_prompt_generator.py` (15,169 bytes)
- `test_integration.py` (9,452 bytes)
- `test_generate.py` (2,218 bytes)
- `test_simple_generate.py` (8,103 bytes)

**重要**: 既存のテストファイルに追加するのではなく、新規テストは新規ファイルとして作成する

---

## Python環境

**Pythonバージョン**: 3.13
**パッケージマネージャー**: `uv`
**仮想環境**: `.venv/`
**依存関係管理**: `pyproject.toml`, `uv.lock`

**既知の依存パッケージ**:
- `requests`
- `websocket-client`
- `Pillow` (推測)

**実行方法**:
```bash
uv run python script.py
```

---

## プロジェクト設定

**ComfyUIサーバー**:
- デフォルトアドレス: `127.0.0.1:8188` (クライアント側)
- 実際の起動ポート: `127.0.0.1:8000` (generate_images.py デフォルト)

**デフォルトパラメータ** (config.yaml):
```yaml
default_params:
  steps: 30
  cfg: 5.45
  width: 1024
  height: 1024
```

---

## Git情報

**現在のブランチ**: `main`
**最新のコミット**:
```
006edfe 抽象テンプレートの追加とプロンプト生成改善
9197137 Add prompt templates for abstract art generation with diverse elements and settings
e4b38dc Add support for multiple template files
937a914 Add date-based folder organization and CSV logging
170253c Add batch image generation and reorganize test files
```

**未追跡ファイル**:
- `loadimage_min.json`

---

## Step 2 実装完了（2025-10-20）

### 新規作成したファイル

1. ✅ **mini_muse/ollama_prompt.py** - Ollama画像分析モジュール
2. ✅ **tests/test_ollama_prompt.py** - Ollama画像分析テスト

### 実装内容

#### mini_muse/ollama_prompt.py

**目的**: Ollama LMMを使用した画像→プロンプト生成
**主要関数**:
- `_load_and_resize_to_base64(image_path, short_side=768) -> str`
  - 画像を読み込み、リサイズ、base64エンコード
  - 短辺を768pxに縮小（メモリ節約）
  - RGB変換、JPEG品質90%

- `analyze_image_with_ollama(image_path, *, model="llava", host="http://localhost:11434", prompt=None, timeout=120) -> str`
  - 画像をOllama LMMで分析
  - 1行の動画化プロンプトを生成
  - フォーマット: "[subject], [motion], [camera movement], [atmosphere]"

**依存関係**:
- `requests`
- `Pillow` (PIL)
- `base64`, `io`, `json`, `pathlib`

**例外**:
- `FileNotFoundError`: 画像ファイルが見つからない
- `requests.HTTPError`: Ollama APIエラー
- `requests.Timeout`: タイムアウト
- `KeyError`: レスポンス形式が不正
- `ValueError`: 空のレスポンス

**デフォルトプロンプト**:
```
Analyze this image and output a single concise prompt for a 5-second video animation.
Format strictly: "[subject], [motion], [camera movement], [atmosphere]".
No extra words.
```

#### tests/test_ollama_prompt.py

**テスト内容**:
1. `test_analyze_returns_nonempty()` - 正常系テスト
   - テスト用画像（256x256）を生成
   - analyze_image_with_ollama を呼び出し
   - 文字列が返ることを確認
   - カンマ区切りのフォーマットを確認

2. `test_error_when_missing_file()` - 異常系テスト
   - 存在しないファイルを指定
   - FileNotFoundError が発生することを確認

**環境変数**:
- `OLLAMA_HOST`: OllamaサーバーURL（デフォルト: http://localhost:11434）
- `OLLAMA_MODEL`: 使用モデル（デフォルト: llava）

### 使用方法

```python
from mini_muse.ollama_prompt import analyze_image_with_ollama

# 基本的な使用
prompt = analyze_image_with_ollama("input/sample.jpg")
print(prompt)

# カスタム設定
prompt = analyze_image_with_ollama(
    "input/sample.jpg",
    model="bakllava",
    host="http://localhost:11434",
    timeout=300
)
```

### テスト実行

```bash
# pytest を使用
uv run pytest tests/test_ollama_prompt.py -v

# または直接実行
uv run python -m pytest tests/test_ollama_prompt.py
```

### 前提条件

1. **Ollamaサーバーの起動**
   ```bash
   ollama serve
   ```

2. **モデルのインストール**
   ```bash
   ollama pull llava
   ```

3. **依存パッケージ**
   - `requests`
   - `Pillow`
   - `pytest` (テスト実行時)

---

## 禁止事項（CLAUDE.md より）

1. ❌ ファイル生成・更新前にユーザー確認なしで実行しない
2. ❌ 計画変更時に再確認なしで別アプローチを行わない
3. ❌ ユーザーの指示を最適化せず、指示通りに実行する
4. ❌ 既存ファイルの内容を削らない
5. ❌ 勝手な解釈をしない

---

## 実行コマンド例

### プロンプト生成テスト
```bash
uv run python tests/test_prompt_generator.py
```

### 画像生成（1枚）
```bash
uv run python generate_images.py
```

### 画像生成（バッチ）
```bash
uv run python generate_images.py --count 10 --template abstract_art
```

### テンプレートファイル一覧
```bash
uv run python generate_images.py --list-templates
```

---

## メモ

- 現在のディレクトリ: `/home/perso/analysis/mini-muse`
- プラットフォーム: Linux (WSL2)
- プロジェクトは `git` で管理されている
- `uv` を使用したPython環境管理
- ComfyUI は別プロセスで起動している前提
- 画像生成は平均20-30秒/枚
- RealESRGAN x2 アップスケーリングあり（1024x1024 → 2048x2048）
