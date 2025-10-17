# mini_muse

ComfyUIベースの画像生成システム

## 概要

Mini-MuseはComfyUIを使用した画像生成プロジェクトです。テンプレートベースのプロンプト自動生成から画像生成、バッチ処理まで一貫して行うことができます。

## 主な機能

- **🎨 プロンプト自動生成**: 36カテゴリ、4種類のテンプレートから多様なプロンプトを生成
- **⚡ バッチ生成**: 1枚から100枚以上の連続画像生成に対応
- **🎯 ComfyUI連携**: ComfyUI API経由での画像生成
- **🔧 パラメータ制御**: ステップ数、CFG、解像度などを細かく制御
- **🖼️ 高解像度出力**: RealESRGAN x2アップスケーリング対応（2048x2048）

## プロジェクト構成

```
mini-muse/
├── mini_muse/
│   ├── comfyui_client.py      # ComfyUI APIクライアント
│   └── prompt_generator.py    # プロンプト生成器
├── prompts/
│   ├── prompt_elements.json   # デフォルトプロンプト要素（ミニチュア/ジオラマ）
│   ├── prompt_templates_抽象画_20250117.json      # 抽象画専用テンプレート
│   └── prompt_templates_抽象悪夢_20250122.json    # 抽象悪夢テンプレート
├── workflows/
│   └── sd3.5_large_turbo_upscale.json  # SD3.5 + RealESRGAN x2ワークフロー
├── tests/
│   ├── test_comfyui_client.py     # クライアントユニットテスト
│   ├── test_prompt_generator.py   # 生成器ユニットテスト
│   ├── test_integration.py        # 統合テスト
│   ├── test_generate.py           # 画像生成テスト（高レベル）
│   └── test_simple_generate.py    # 画像生成テスト（低レベル）
├── stablediffusion/
│   └── outputs/                   # 生成画像の出力先（日付別フォルダに自動整理）
│       └── YYYYMMDD/              # 日付フォルダ
│           ├── *.png              # 生成画像
│           └── generation_log_YYYYMMDD.csv  # 生成ログ（CSVファイル）
├── generate_images.py             # バッチ画像生成メインスクリプト
├── config/
│   └── config.yaml                # プロジェクト設定ファイル
├── doc/
│   └── CHANGELOG_*.md             # 変更履歴
├── pyproject.toml                 # uvプロジェクト設定ファイル
├── uv.lock                        # uv依存関係ロックファイル
└── README.md                      # このファイル
```

## インストール

### 必要な環境

- Python 3.9+
- **uv** (Pythonパッケージマネージャー - インストール済み)
- ComfyUI (インストール済み、実行中)
- Stable Diffusion 3.5 Large Turbo モデル
- RealESRGAN_x2plus モデル

### パッケージインストール

**重要**: このプロジェクトでは `uv` を使用します。すべてのPythonスクリプト実行時には `uv run` を使用してください。

```bash
# 依存関係のインストール（初回のみ）
uv sync

# または、個別にパッケージをインストール
uv pip install requests websocket-client
```

## 使い方

### 1. ComfyUIの起動

ComfyUIサーバーを起動してください（デフォルト: http://127.0.0.1:8000）

### 2. 画像生成

**⚠️ 重要**: すべてのPythonスクリプト実行時には必ず `uv run` を使用してください。

#### 基本的な使用方法（1枚生成）

```bash
uv run python generate_images.py
```

#### バッチ生成

```bash
# 10枚生成
uv run python generate_images.py --count 10

# 100枚生成
uv run python generate_images.py --count 100

# 500枚生成
uv run python generate_images.py --count 500
```

#### テンプレート指定

```bash
# abstract_artテンプレートで5枚生成
uv run python generate_images.py --template abstract_art --count 5

# 利用可能なテンプレート:
#   - abstract_art (抽象アート)
#   - detailed_diorama (詳細なジオラマ)
#   - imaginative_world (想像の世界)
#   - miniature_world (ミニチュア世界)
```

#### カスタムテンプレートファイルの使用

プロジェクトには複数のプロンプトテンプレートファイルがあります。`--template-file` オプションで指定できます。

```bash
# 利用可能なテンプレートファイルを確認
uv run python generate_images.py --list-templates

# 抽象画テンプレートを使用（新規作成されたテンプレート）
uv run python generate_images.py \
  --template-file "prompts/prompt_templates_抽象画_20250117.json" \
  --template "abstract_composition" \
  --count 10

# 抽象悪夢テンプレートを使用
uv run python generate_images.py \
  --template-file "prompts/prompt_templates_抽象悪夢_20250122.json" \
  --template "beksinski_nightmare" \
  --count 5

# 500枚の抽象画を一括生成
uv run python generate_images.py \
  --template-file "prompts/prompt_templates_抽象画_20250117.json" \
  --template "abstract_composition" \
  --count 500 \
  --steps 30 \
  --cfg 5.45
```

#### パラメータカスタマイズ

```bash
# ステップ数とCFGを指定
uv run python generate_images.py --steps 40 --cfg 7.0 --count 3

# 解像度指定
uv run python generate_images.py --width 1024 --height 1024 --count 5

# シード固定で再現性確保
uv run python generate_images.py --seed 42 --count 1
```

#### 全パラメータ

```bash
uv run python generate_images.py \
  --count 10 \
  --template-file "prompts/prompt_templates_抽象画_20250117.json" \
  --template abstract_composition \
  --server 127.0.0.1:8000 \
  --workflow workflows/sd3.5_large_turbo_upscale.json \
  --steps 30 \
  --cfg 5.45 \
  --width 1024 \
  --height 1024 \
  --seed 42 \
  --output-dir stablediffusion/outputs \
  --negative-prompt "blurry, low quality, distorted"
```

### 3. ヘルプ表示

```bash
uv run python generate_images.py --help
```

## テスト

### ユニットテスト

```bash
# プロンプト生成器のテスト
uv run python3 tests/test_prompt_generator.py

# ComfyUIクライアントのテスト
uv run python3 tests/test_comfyui_client.py
```

### 統合テスト

```bash
# 統合テスト実行（実際に画像生成を行います）
uv run python3 tests/test_integration.py
```

## プロンプトテンプレートファイル

### 利用可能なテンプレートファイル

プロジェクトには複数のプロンプトテンプレートファイルが用意されています：

1. **prompt_templates_抽象画_20250117.json** - 抽象画専用テンプレート
   - 抽象芸術に特化した要素とテンプレート
   - カンディンスキー、モンドリアン、ロスコなど著名な抽象画家のスタイル
   - 15種類のテンプレート（abstract_composition, kandinsky_inspired, rothko_fields, など）
   - 悪夢的・ホラー要素を排除した純粋な抽象表現

2. **prompt_templates_抽象悪夢_20250122.json** - 抽象悪夢テンプレート
   - ベクシンスキー風の暗部表現と悪夢的要素
   - ボルタンスキー風のメモリアル要素
   - 両者を融合した独特の表現

3. **prompt_elements.json** - デフォルトテンプレート（従来のミニチュア/ジオラマ向け）

### テンプレートファイル一覧の確認

```bash
# 利用可能なテンプレートファイルを一覧表示
uv run python generate_images.py --list-templates
```

### 抽象画テンプレートの詳細

`prompts/prompt_templates_抽象画_20250117.json`には以下の要素カテゴリがあります：

- **abstract_elements**: 幾何学的図形、カラーフィールド、フラクタルなど
- **colors**: vibrant, muted, monochromatic, complementary など
- **techniques**: layering, dripping, digital manipulation など
- **art_movements**: suprematism, de stijl, bauhaus, abstract expressionism など
- **artistic_techniques**: kandinsky color theory, pollock drip technique など
- **philosophical_concepts**: spiritual in art, universal harmony, zen emptiness など
- **spatial_concepts**: infinite depth, floating space, spatial tension など
- **geometric_elements**: point line plane, grid structure, planar relationship など
- **brush_elements**: brush stroke, gestural energy, calligraphic mark など
- **musical_elements**: harmonic resonance, rhythmic pattern, melodic flow など

### 利用可能なテンプレート（抽象画）

- `abstract_composition` - 抽象的構成
- `kandinsky_inspired` - カンディンスキー風構成
- `mondrian_composition` - モンドリアン風構成
- `rothko_fields` - ロスコ風色面構成
- `pollock_action` - ポロック風アクションペインティング
- `fontana_spatial` - フォンタナ風空間概念
- `twombly_gestural` - トゥオンブリー風スクリブル
- `richter_abstract` - リヒター風抽象
- `lee_ufan` - 李禹煥風ミニマル
- `malevich_supreme` - マレーヴィチ風シュプレマティスム
- `klee_pedagogical` - クレー風教育的抽象
- `albers_interaction` - アルバース風色彩相互作用
- `color_field_exploration` - 色面探求
- `geometric_harmony` - 幾何学的調和
- `expressive_abstraction` - 表現的抽象

## プロンプト生成

### テンプレート構造（デフォルト）

`prompts/prompt_elements.json`には36のカテゴリがあります：

- **フレーム設定**: Victorian specimen jar, cosmic portal gateway, など
- **カメラフォーカス**: tilt-shift, macro lens, split focus, など
- **ミニチュアシーン**: pocket universe library, quantum physics lab, など
- **カメラアングル**: bird's eye view, worm's eye view, など
- **ユニークオブジェクト**: mechanical kraken, floating angelic beings, など
- その他31カテゴリ...

### プロンプト生成例

```python
from mini_muse.prompt_generator import PromptGenerator

# デフォルトテンプレートファイルでプロンプト生成器初期化
prompt_gen = PromptGenerator()

# カスタムテンプレートファイルで初期化
prompt_gen_abstract = PromptGenerator(
    elements_file="prompts/prompt_templates_抽象画_20250117.json"
)

# 単一プロンプト生成
prompt = prompt_gen_abstract.generate_prompt("abstract_composition")
print(prompt)

# 複数プロンプト生成
prompts = prompt_gen_abstract.generate_multiple_prompts("kandinsky_inspired", count=5)
for prompt in prompts:
    print(prompt)

# 利用可能なテンプレート確認
templates = prompt_gen_abstract.get_available_templates()
print(templates)
```

**実行時は必ず `uv run` を使用してください：**

```bash
uv run python your_script.py
```

## ComfyUIクライアント

### 基本的な使用方法

```python
from mini_muse.comfyui_client import ComfyUIClient

# クライアント初期化
client = ComfyUIClient("127.0.0.1:8000")

# ワークフロー読み込み
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

# 画像生成
image_data = client.generate_image(
    workflow,
    positive_prompt="a beautiful landscape with mountains and rivers",
    negative_prompt="blurry, low quality",
    seed=42,
    steps=30,
    cfg=5.45,
    width=1024,
    height=1024,
    save_path="output.png"
)
```

## 設定ファイル

`config/config.yaml` で以下の設定を管理します：

```yaml
paths:
  prompts: ./prompts
  outputs: ./stablediffusion/outputs

comfyui:
  base_url: http://127.0.0.1:8188

default_params:
  steps: 30
  cfg: 5.45
  width: 1024
  height: 1024
```

## ワークフロー

### 現在のワークフロー構成

`workflows/sd3.5_large_turbo_upscale.json`:

1. **CheckpointLoader**: SD3.5 Large Turbo モデル読み込み
2. **CLIPLoader**: テキストエンコーダー読み込み
3. **KSampler**: 画像生成（30ステップ、CFG 5.45）
4. **VAEDecode**: 潜在空間からピクセル空間への変換
5. **UpscaleModelLoader**: RealESRGAN x2plus 読み込み
6. **ImageUpscaleWithModel**: 2048x2048にアップスケール
7. **SaveImage**: 画像保存

### 処理時間

- **通常**: 20-30秒/枚
- **アップスケーリング込み**: 1024x1024 → 2048x2048
- **バッチ処理**: 平均22秒/枚

## トラブルシューティング

### ComfyUIに接続できない

```bash
# ComfyUIのポートを確認
# デフォルトは8188ですが、8000で動作している場合もあります
python generate_images.py --server 127.0.0.1:8000
```

### タイムアウトエラー

一部の画像生成で300秒（5分）を超える場合があります。これは以下の原因が考えられます：

- RealESRGANアップスケーリングの処理時間
- VRAMの断片化
- 複雑なプロンプトの処理負荷

### メモリ不足

大量のバッチ生成を行う場合、定期的にComfyUIを再起動することを推奨します。

## 出力例

生成された画像は以下の形式で保存されます：

```
stablediffusion/outputs/
├── abstract_art_20251015_225552_0001.png
├── abstract_art_20251015_225623_0002.png
├── abstract_art_20251015_225649_0003.png
...
└── test_integration/
    ├── test_single_20251015_222219.png
    └── test_batch_20251015_222331_01.png
```

## ライセンス

MIT License

## 更新履歴

変更履歴は `doc/CHANGELOG_*.md` を参照してください。

## 開発者向け

### テストの追加

新しいテストを追加する場合は `tests/` ディレクトリに配置してください。

### ワークフローのカスタマイズ

ComfyUI UIでワークフローをカスタマイズし、API形式でエクスポートして `workflows/` に配置してください。

### プロンプト要素の追加

`prompts/prompt_elements.json` を編集して、新しいカテゴリや要素を追加できます。
