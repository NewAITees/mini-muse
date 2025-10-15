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
│   └── prompt_elements.json   # プロンプト要素データ（36カテゴリ）
├── workflows/
│   └── sd3.5_large_turbo_upscale.json  # SD3.5 + RealESRGAN x2ワークフロー
├── tests/
│   ├── test_comfyui_client.py     # クライアントユニットテスト
│   ├── test_prompt_generator.py   # 生成器ユニットテスト
│   ├── test_integration.py        # 統合テスト
│   ├── test_generate.py           # 画像生成テスト（高レベル）
│   └── test_simple_generate.py    # 画像生成テスト（低レベル）
├── stablediffusion/
│   └── outputs/                   # 生成画像の出力先
├── generate_images.py             # バッチ画像生成メインスクリプト
├── config/
│   └── config.yaml                # プロジェクト設定ファイル
└── README.md                      # このファイル
```

## インストール

### 必要な環境

- Python 3.9+
- ComfyUI (インストール済み、実行中)
- Stable Diffusion 3.5 Large Turbo モデル
- RealESRGAN_x2plus モデル

### パッケージインストール

```bash
# uvを使用（推奨）
uv pip install requests websocket-client

# または通常のpip
pip install requests websocket-client
```

## 使い方

### 1. ComfyUIの起動

ComfyUIサーバーを起動してください（デフォルト: http://127.0.0.1:8000）

### 2. 画像生成

#### 基本的な使用方法（1枚生成）

```bash
python generate_images.py
```

#### バッチ生成

```bash
# 10枚生成
python generate_images.py --count 10

# 100枚生成
python generate_images.py --count 100
```

#### テンプレート指定

```bash
# abstract_artテンプレートで5枚生成
python generate_images.py --template abstract_art --count 5

# 利用可能なテンプレート:
#   - abstract_art (抽象アート)
#   - detailed_diorama (詳細なジオラマ)
#   - imaginative_world (想像の世界)
#   - miniature_world (ミニチュア世界)
```

#### パラメータカスタマイズ

```bash
# ステップ数とCFGを指定
python generate_images.py --steps 40 --cfg 7.0 --count 3

# 解像度指定
python generate_images.py --width 1024 --height 1024 --count 5

# シード固定で再現性確保
python generate_images.py --seed 42 --count 1
```

#### 全パラメータ

```bash
python generate_images.py \
  --count 10 \
  --template abstract_art \
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
python generate_images.py --help
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

## プロンプト生成

### テンプレート構造

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

# プロンプト生成器初期化
prompt_gen = PromptGenerator()

# 単一プロンプト生成
prompt = prompt_gen.generate_prompt("abstract_art")
print(prompt)

# 複数プロンプト生成
prompts = prompt_gen.generate_multiple_prompts("detailed_diorama", count=5)
for prompt in prompts:
    print(prompt)

# 利用可能なテンプレート確認
templates = prompt_gen.get_available_templates()
print(templates)
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
