# Stable Diffusion 3.5 TensorRT + T5長文プロンプト対応：開発者向け実装ガイド

## 概要

本ガイドでは、NVIDIA TensorRTを使用したStable Diffusion 3.5の実装において、T5エンコーダーによる長文プロンプト対応（最大256トークン）を実現する手順を解説します。

**主な特徴**
- プロンプト長：最大256トークン（デフォルト77トークンの3倍以上）
- パフォーマンス：BF16 PyTorchと比較して1.7倍～2.3倍高速
- メモリ削減：FP8量子化で40%のVRAM削減
- 実装難易度：中級（Python開発経験者向け）

## システム要件

### 必須要件

**ハードウェア**
- GPU: NVIDIA RTX 4000シリーズ以降（Ada Lovelace）推奨
- VRAM: 最低12GB（FP8量子化時）、推奨18GB以上（BF16時）
- システムRAM: 32GB以上推奨

**ソフトウェア**
- OS: WSL2 (Ubuntu 22.04推奨)
- Python: 3.10～3.12
- CUDA: 12.4以降
- NVIDIA Driver: 535以降（Windows側）
- uv: 最新版

### 推奨構成

| GPU | VRAM | 推奨精度 | 期待速度 |
|-----|------|----------|----------|
| RTX 4090 | 24GB | BF16/FP8 | 最速 |
| RTX 4080 | 16GB | FP8 | 高速 |
| RTX 4070 Ti | 12GB | FP8 | 中速 |

## WSL2のGPU対応セットアップ

### Step 1: WSL2とUbuntuのインストール確認

```powershell
# PowerShellで実行（管理者権限）

# WSL2がインストールされているか確認
wsl --list --verbose

# Ubuntu 22.04がない場合はインストール
wsl --install -d Ubuntu-22.04

# WSLのバージョンを2に設定
wsl --set-version Ubuntu-22.04 2
wsl --set-default Ubuntu-22.04
```

### Step 2: NVIDIA Driver確認（Windows側）

```powershell
# PowerShellでドライバーバージョン確認
nvidia-smi

# 出力例：
# Driver Version: 535.xx以上であることを確認
```

**必要な場合**: https://www.nvidia.com/Download/index.aspx から最新のGame Ready Driverをダウンロード・インストール

### Step 3: WSL内でのCUDA動作確認

```bash
# WSL2のUbuntuターミナルで実行

# nvidia-smiがWSL内で動作するか確認
nvidia-smi

# 成功すれば以下のような出力が表示される：
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx       Driver Version: 535.xx       CUDA Version: 12.x    |
# +-----------------------------------------------------------------------------+
```

**トラブルシューティング**: nvidia-smiが動作しない場合

```bash
# WSLカーネルを最新に更新（PowerShellで実行）
wsl --update

# WSLを再起動
wsl --shutdown
# 再度WSLを起動
```

## uvのインストールと環境構築

### Step 4: uvのインストール

```bash
# WSL2のUbuntuターミナルで実行

# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# シェルを再起動してパスを通す
source $HOME/.cargo/env

# インストール確認
uv --version
```

### Step 5: プロジェクトディレクトリのセットアップ

```bash
# プロジェクトディレクトリを作成
mkdir -p ~/sd35-tensorrt
cd ~/sd35-tensorrt

# uvでPythonプロジェクトを初期化
uv init --python 3.11

# 仮想環境が自動作成されたことを確認
ls -la .venv
```

### Step 6: 基本依存関係のインストール

```bash
# pyproject.tomlを編集
cat > pyproject.toml << 'EOF'
[project]
name = "sd35-tensorrt"
version = "0.1.0"
description = "Stable Diffusion 3.5 with TensorRT and T5 encoder"
requires-python = ">=3.11"
dependencies = [
    "torch>=2.1.0",
    "torchvision>=0.16.0",
    "numpy>=1.24.0",
    "pillow>=10.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
index-url = "https://download.pytorch.org/whl/cu121"
EOF

# 依存関係をインストール
uv sync

# 仮想環境を有効化
source .venv/bin/activate
```

### Step 7: PyTorchとCUDAの動作確認テスト

```bash
# テストスクリプトを作成
cat > test_01_pytorch_cuda.py << 'EOF'
"""
Test 1: PyTorchとCUDAの動作確認
"""
import torch
import sys

print("=" * 60)
print("Test 1: PyTorch + CUDA 動作確認")
print("=" * 60)

# PyTorchバージョン
print(f"\n✓ PyTorch version: {torch.__version__}")

# CUDA利用可能性
cuda_available = torch.cuda.is_available()
print(f"✓ CUDA available: {cuda_available}")

if not cuda_available:
    print("\n❌ ERROR: CUDAが利用できません")
    print("   WSL2のGPU設定を確認してください")
    sys.exit(1)

# CUDAバージョン
print(f"✓ CUDA version: {torch.version.cuda}")

# GPU情報
gpu_count = torch.cuda.device_count()
print(f"✓ GPU count: {gpu_count}")

for i in range(gpu_count):
    gpu_name = torch.cuda.get_device_name(i)
    gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
    print(f"  - GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")

# 簡単なテンソル演算
print("\n✓ テンソル演算テスト:")
x = torch.randn(1000, 1000, device='cuda')
y = torch.randn(1000, 1000, device='cuda')
z = torch.matmul(x, y)
print(f"  - Matrix multiplication: {z.shape}")
print(f"  - Result sample: {z[0, 0].item():.4f}")

print("\n" + "=" * 60)
print("✓ Test 1 PASSED: PyTorchとCUDAは正常に動作しています")
print("=" * 60)
EOF

# テスト実行
python test_01_pytorch_cuda.py
```

**期待される出力**:
```
============================================================
Test 1: PyTorch + CUDA 動作確認
============================================================

✓ PyTorch version: 2.x.x
✓ CUDA available: True
✓ CUDA version: 12.1
✓ GPU count: 1
  - GPU 0: NVIDIA GeForce RTX 4090 (24.0 GB)

✓ テンソル演算テスト:
  - Matrix multiplication: torch.Size([1000, 1000])
  - Result sample: -1.2345

============================================================
✓ Test 1 PASSED: PyTorchとCUDAは正常に動作しています
============================================================
```

## TensorRT環境のセットアップ

### Step 8: TensorRTと関連ライブラリのインストール

```bash
# TensorRTと依存関係を追加
uv add tensorrt-cu12 \
  diffusers \
  transformers \
  accelerate \
  safetensors \
  onnx \
  onnxruntime-gpu \
  polygraphy

# HuggingFace CLIもインストール
uv add huggingface-hub
```

### Step 9: TensorRTインストール確認テスト

```bash
# テストスクリプトを作成
cat > test_02_tensorrt.py << 'EOF'
"""
Test 2: TensorRTのインストール確認
"""
import sys

print("=" * 60)
print("Test 2: TensorRT インストール確認")
print("=" * 60)

# TensorRTのインポート
try:
    import tensorrt as trt
    print(f"\n✓ TensorRT version: {trt.__version__}")
except ImportError as e:
    print(f"\n❌ ERROR: TensorRTをインポートできません: {e}")
    sys.exit(1)

# TensorRTロガーの作成テスト
try:
    logger = trt.Logger(trt.Logger.WARNING)
    print(f"✓ TensorRT Logger created: {type(logger)}")
except Exception as e:
    print(f"❌ ERROR: TensorRT Logger作成エラー: {e}")
    sys.exit(1)

# TensorRTビルダーの作成テスト
try:
    builder = trt.Builder(logger)
    print(f"✓ TensorRT Builder created: {type(builder)}")
except Exception as e:
    print(f"❌ ERROR: TensorRT Builder作成エラー: {e}")
    sys.exit(1)

# ONNX関連のインポート
try:
    import onnx
    import onnxruntime
    print(f"\n✓ ONNX version: {onnx.__version__}")
    print(f"✓ ONNX Runtime version: {onnxruntime.__version__}")

    # ONNX RuntimeのGPUプロバイダー確認
    providers = onnxruntime.get_available_providers()
    print(f"✓ ONNX Runtime providers: {providers}")

    if 'CUDAExecutionProvider' not in providers:
        print("⚠ WARNING: CUDAExecutionProviderが利用できません")
    else:
        print("✓ CUDA Execution Provider available")

except ImportError as e:
    print(f"❌ ERROR: ONNX関連ライブラリのインポートエラー: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Test 2 PASSED: TensorRTは正常にインストールされています")
print("=" * 60)
EOF

# テスト実行
python test_02_tensorrt.py
```

## Diffusers/Transformersのセットアップ

### Step 10: Diffusers動作確認テスト

```bash
# テストスクリプトを作成
cat > test_03_diffusers.py << 'EOF'
"""
Test 3: Diffusers/Transformersのインストール確認
"""
import sys

print("=" * 60)
print("Test 3: Diffusers/Transformers 確認")
print("=" * 60)

# Diffusersのインポート
try:
    import diffusers
    print(f"\n✓ Diffusers version: {diffusers.__version__}")
except ImportError as e:
    print(f"\n❌ ERROR: Diffusersをインポートできません: {e}")
    sys.exit(1)

# Transformersのインポート
try:
    import transformers
    print(f"✓ Transformers version: {transformers.__version__}")
except ImportError as e:
    print(f"❌ ERROR: Transformersをインポートできません: {e}")
    sys.exit(1)

# 主要コンポーネントのインポートテスト
try:
    from diffusers import DiffusionPipeline
    from transformers import AutoTokenizer, T5EncoderModel
    print(f"\n✓ DiffusionPipeline imported")
    print(f"✓ T5EncoderModel imported")
except ImportError as e:
    print(f"❌ ERROR: 必要なコンポーネントのインポートエラー: {e}")
    sys.exit(1)

# T5トークナイザーの動作テスト
try:
    print("\n✓ T5トークナイザーテスト:")

    # 小さなT5モデルで動作確認
    # (SD3.5の実際のモデルはまだダウンロードしない)
    tokenizer = AutoTokenizer.from_pretrained("t5-small")

    test_prompt = "A beautiful landscape with mountains"
    tokens = tokenizer.encode(test_prompt)

    print(f"  - Test prompt: '{test_prompt}'")
    print(f"  - Token count: {len(tokens)}")
    print(f"  - Tokens: {tokens[:10]}...")  # 最初の10トークンのみ表示

except Exception as e:
    print(f"❌ ERROR: T5トークナイザーテストエラー: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Test 3 PASSED: Diffusers/Transformersは正常動作しています")
print("=" * 60)
EOF

# テスト実行
python test_03_diffusers.py
```

## HuggingFace認証のセットアップ

### Step 11: HuggingFaceトークンの設定

```bash
# HuggingFaceにログイン
huggingface-cli login

# プロンプトに従ってトークンを入力
# Token: hf_xxxxxxxxxxxxxxxxxxxxx
```

**トークンの取得方法**:
1. https://huggingface.co/settings/tokens にアクセス
2. "New token" をクリック
3. Name: "sd35-tensorrt"
4. Type: "Read" を選択
5. "Generate token" をクリック
6. トークンをコピー

### Step 12: HuggingFace接続テスト

```bash
# テストスクリプトを作成
cat > test_04_huggingface.py << 'EOF'
"""
Test 4: HuggingFace接続確認
"""
import sys
import os

print("=" * 60)
print("Test 4: HuggingFace 接続確認")
print("=" * 60)

# HuggingFace Hubのインポート
try:
    from huggingface_hub import HfApi, login
    print(f"\n✓ HuggingFace Hub imported")
except ImportError as e:
    print(f"\n❌ ERROR: HuggingFace Hubをインポートできません: {e}")
    sys.exit(1)

# 認証確認
try:
    api = HfApi()
    whoami = api.whoami()
    print(f"✓ Logged in as: {whoami['name']}")
except Exception as e:
    print(f"❌ ERROR: HuggingFaceにログインできていません")
    print(f"   'huggingface-cli login' を実行してください")
    print(f"   Error: {e}")
    sys.exit(1)

# SD3.5モデルへのアクセス確認（メタデータのみ）
try:
    print(f"\n✓ SD3.5モデルアクセステスト:")

    model_id = "stabilityai/stable-diffusion-3.5-large"

    # モデル情報を取得（ダウンロードはしない）
    model_info = api.model_info(model_id)

    print(f"  - Model ID: {model_id}")
    print(f"  - Model author: {model_info.author}")
    print(f"  - Downloads: {model_info.downloads}")
    print(f"  - Model size: ~{len(model_info.siblings)} files")

    print(f"\n✓ モデルへのアクセス権限: OK")

except Exception as e:
    print(f"❌ ERROR: SD3.5モデルにアクセスできません")
    print(f"   以下を確認してください:")
    print(f"   1. https://huggingface.co/stabilityai/stable-diffusion-3.5-large")
    print(f"   2. ライセンスに同意しているか")
    print(f"   3. トークンに適切な権限があるか")
    print(f"   Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Test 4 PASSED: HuggingFaceへの接続は正常です")
print("=" * 60)
EOF

# テスト実行
python test_04_huggingface.py
```

## TensorRT公式リポジトリのセットアップ

### Step 13: TensorRTリポジトリのクローン

```bash
# ホームディレクトリに戻る
cd ~

# TensorRT公式リポジトリをクローン
git clone https://github.com/NVIDIA/TensorRT.git
cd TensorRT

# 最新の安定版ブランチをチェックアウト
git checkout release/10.8

# Diffusionデモディレクトリに移動
cd demo/Diffusion

# 現在のディレクトリを確認
pwd
# 出力例: /home/username/TensorRT/demo/Diffusion
```

### Step 14: TensorRT Demo依存関係のインストール

```bash
# Diffusionディレクトリで実行
cd ~/TensorRT/demo/Diffusion

# requirements.txtを確認
cat requirements.txt

# uvを使って依存関係をインストール
# (既存のプロジェクトに追加する形で)
cd ~/sd35-tensorrt

# TensorRT Diffusionの依存関係を追加
uv add colored polygraphy onnx-graphsurgeon

# TensorRT Diffusionディレクトリへのシンボリックリンクを作成
ln -s ~/TensorRT/demo/Diffusion ./tensorrt_diffusion

# 確認
ls -la tensorrt_diffusion
```

### Step 15: エンジンビルド準備完了テスト（最終確認）

```bash
# 総合テストスクリプトを作成
cat > test_05_ready_to_build.py << 'EOF'
"""
Test 5: エンジンビルド準備完了確認
"""
import sys
import os
from pathlib import Path

print("=" * 60)
print("Test 5: エンジンビルド準備完了確認")
print("=" * 60)

# 必要なモジュールの確認
required_modules = [
    ('torch', 'PyTorch'),
    ('tensorrt', 'TensorRT'),
    ('diffusers', 'Diffusers'),
    ('transformers', 'Transformers'),
    ('onnx', 'ONNX'),
    ('onnxruntime', 'ONNX Runtime'),
]

print("\n✓ 必須モジュール確認:")
all_modules_ok = True

for module_name, display_name in required_modules:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"  ✓ {display_name:20s}: {version}")
    except ImportError:
        print(f"  ❌ {display_name:20s}: NOT FOUND")
        all_modules_ok = False

if not all_modules_ok:
    print("\n❌ ERROR: 必須モジュールが不足しています")
    sys.exit(1)

# CUDA確認
print("\n✓ CUDA環境確認:")
import torch

if not torch.cuda.is_available():
    print("  ❌ CUDAが利用できません")
    sys.exit(1)

print(f"  ✓ CUDA version: {torch.version.cuda}")
print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
print(f"  ✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# HuggingFace認証確認
print("\n✓ HuggingFace認証確認:")
try:
    from huggingface_hub import HfApi
    api = HfApi()
    whoami = api.whoami()
    print(f"  ✓ Logged in as: {whoami['name']}")
except Exception as e:
    print(f"  ❌ HuggingFaceにログインできていません")
    sys.exit(1)

# TensorRT Diffusionディレクトリ確認
print("\n✓ TensorRT Diffusionディレクトリ確認:")
tensorrt_diffusion_path = Path.home() / 'TensorRT' / 'demo' / 'Diffusion'

if not tensorrt_diffusion_path.exists():
    print(f"  ❌ TensorRT Diffusionディレクトリが見つかりません")
    print(f"     Expected: {tensorrt_diffusion_path}")
    sys.exit(1)

print(f"  ✓ Path: {tensorrt_diffusion_path}")

# 主要スクリプトの存在確認
demo_script = tensorrt_diffusion_path / 'demo_txt2img.py'
if not demo_script.exists():
    print(f"  ❌ demo_txt2img.py が見つかりません")
    sys.exit(1)

print(f"  ✓ demo_txt2img.py found")

# ディスク容量確認
print("\n✓ ディスク容量確認:")
import shutil
stat = shutil.disk_usage(Path.home())
free_gb = stat.free / 1024**3
print(f"  - Free space: {free_gb:.1f} GB")

if free_gb < 50:
    print(f"  ⚠ WARNING: 空き容量が50GB未満です")
    print(f"     モデルダウンロードとエンジンビルドには50GB以上推奨")
else:
    print(f"  ✓ Sufficient disk space")

# メモリ確認
print("\n✓ システムメモリ確認:")
import psutil
mem = psutil.virtual_memory()
total_gb = mem.total / 1024**3
available_gb = mem.available / 1024**3
print(f"  - Total RAM: {total_gb:.1f} GB")
print(f"  - Available RAM: {available_gb:.1f} GB")

if available_gb < 16:
    print(f"  ⚠ WARNING: 利用可能メモリが16GB未満です")
else:
    print(f"  ✓ Sufficient memory")

# 最終チェック
print("\n" + "=" * 60)
print("✓ Test 5 PASSED: エンジンビルドの準備が完了しました！")
print("=" * 60)
print("\n次のステップ:")
print("1. SD3.5モデルのエンジンをビルド:")
print("   cd ~/TensorRT/demo/Diffusion")
print("   python demo_txt2img.py --version xl-1.0 \\")
print("     --prompt 'A test image' --build-only")
print("\n2. カスタムスクリプトの開発:")
print("   cd ~/sd35-tensorrt")
print("   # 独自の実装を開始")
EOF

# psutilを追加インストール
uv add psutil

# テスト実行
python test_05_ready_to_build.py
```

## 全テストの一括実行

### Step 16: 統合テストスクリプトの作成

```bash
# すべてのテストを一括実行するスクリプト
cat > run_all_tests.sh << 'EOF'
#!/bin/bash

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SD3.5 TensorRT 環境テスト実行"
echo "=========================================="
echo ""

# 仮想環境の有効化
source .venv/bin/activate

# テスト配列
tests=(
    "test_01_pytorch_cuda.py"
    "test_02_tensorrt.py"
    "test_03_diffusers.py"
    "test_04_huggingface.py"
    "test_05_ready_to_build.py"
)

failed_tests=()

# 各テストを実行
for test in "${tests[@]}"; do
    echo ""
    echo -e "${YELLOW}Running: $test${NC}"
    echo ""

    if python "$test"; then
        echo -e "${GREEN}✓ $test PASSED${NC}"
    else
        echo -e "${RED}✗ $test FAILED${NC}"
        failed_tests+=("$test")
    fi

    echo ""
    echo "------------------------------------------"
done

# 結果サマリー
echo ""
echo "=========================================="
echo "テスト結果サマリー"
echo "=========================================="
echo "Total tests: ${#tests[@]}"
echo "Passed: $((${#tests[@]} - ${#failed_tests[@]}))"
echo "Failed: ${#failed_tests[@]}"

if [ ${#failed_tests[@]} -eq 0 ]; then
    echo -e "${GREEN}"
    echo "✓ すべてのテストがパスしました！"
    echo "エンジンビルドの準備が完了しています。"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "✗ 以下のテストが失敗しました:"
    for test in "${failed_tests[@]}"; do
        echo "  - $test"
    done
    echo -e "${NC}"
    exit 1
fi
EOF

# 実行権限を付与
chmod +x run_all_tests.sh

# 一括テスト実行
./run_all_tests.sh
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. WSL2でnvidia-smiが動作しない

**症状**
```bash
nvidia-smi
# command not found または No devices were found
```

**解決方法**

```bash
# PowerShellで実行（管理者権限）
wsl --update

# WSLを完全にシャットダウン
wsl --shutdown

# 再度WSLを起動して確認
wsl
nvidia-smi
```

それでも解決しない場合：
1. Windows側のNVIDIA Driverを最新版に更新
2. WSL2のカーネルを手動更新: https://aka.ms/wsl2kernel

#### 2. uvコマンドが見つからない

**症状**
```bash
uv: command not found
```

**解決方法**

```bash
# パスが通っていない場合
echo 'source $HOME/.cargo/env' >> ~/.bashrc
source ~/.bashrc

# または手動でパスを追加
export PATH="$HOME/.cargo/bin:$PATH"

# 確認
uv --version
```

#### 3. PyTorchがCUDAを認識しない

**症状**
```python
torch.cuda.is_available()  # False
```

**解決方法**

```bash
# CUDA対応版PyTorchを再インストール
uv remove torch torchvision
uv add torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 確認
python -c "import torch; print(torch.cuda.is_available())"
```

#### 4. TensorRTのインポートエラー

**症状**
```python
ImportError: libnvinfer.so.10: cannot open shared object file
```

**解決方法**

```bash
# TensorRTを再インストール
uv remove tensorrt tensorrt-cu12
uv add tensorrt-cu12 --index-url https://pypi.nvidia.com

# 環境変数を設定
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/.venv/lib/python3.11/site-packages/tensorrt_libs
```

#### 5. HuggingFaceログインエラー

**症状**
```
Invalid token
```

**解決方法**

```bash
# トークンを削除して再ログイン
rm ~/.cache/huggingface/token

# 再度ログイン
huggingface-cli login

# または環境変数で設定
export HF_TOKEN="your_token_here"
```

#### 6. メモリ不足エラー

**症状**
```
RuntimeError: CUDA out of memory
```

**解決方法**

```bash
# WSL2のメモリ制限を変更
# .wslconfig ファイルを作成/編集（Windowsホーム）
cat > /mnt/c/Users/YourUsername/.wslconfig << 'EOF'
[wsl2]
memory=32GB
swap=16GB
EOF

# WSLを再起動（PowerShellで実行）
wsl --shutdown
```

## 次のステップ

環境構築とテストが完了したら、実際のエンジンビルドと画像生成に進めます。

### エンジンビルドの実行

```bash
# TensorRT Diffusionディレクトリに移動
cd ~/TensorRT/demo/Diffusion

# SD3.5 Large用エンジンをビルド（初回は20分程度かかります）
python demo_txt2img.py \
  --version xl-1.0 \
  --hf-token $(cat ~/.cache/huggingface/token) \
  --build-enable-refit \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  --prompt "A beautiful sunset over mountains, highly detailed"

# エンジンは engine/ ディレクトリに保存されます
```

### カスタム実装の開始

```bash
# 自分のプロジェクトディレクトリに戻る
cd ~/sd35-tensorrt

# カスタムスクリプトを作成
# (前のセクションで提供したLongPromptSD35Generatorなどを実装)
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. VRAM不足エラー

**症状**
```
RuntimeError: CUDA out of memory
```

**解決方法**

```python
# FP8量子化を有効化
generator = LongPromptSD35Generator(use_fp8=True)

# または解像度を下げる
images = generator.generate(
    prompt=prompt,
    width=768,  # 1024から変更
    height=768,
    steps=25    # ステップ数も削減
)
```

#### 2. HuggingFaceモデルダウンロードエラー

**症状**
```
HTTPError: 401 Client Error: Unauthorized
```

**解決方法**

```bash
# トークンを再設定
export HF_TOKEN="your_new_token"

# またはログインし直す
huggingface-cli login

# モデルへのアクセス権限を確認
# https://huggingface.co/stabilityai/stable-diffusion-3.5-large
```

#### 3. TensorRTエンジンビルドエラー

**症状**
```
[TensorRT] ERROR: ... Invalid dimensions
```

**解決方法**

```bash
# 既存のエンジンキャッシュを削除
rm -rf engine/

# 静的バッチサイズでリビルド
python demo_txt2img_sd35.py \
  --version xl-1.0 \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --prompt "rebuild test"
```

#### 4. プロンプトが切り捨てられる

**症状**
```
Warning: Prompt exceeds maximum token length
```

**解決方法**

```python
# トークン数を確認
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "stabilityai/stable-diffusion-3.5-large",
    subfolder="tokenizer"
)

tokens = tokenizer.encode(your_prompt)
print(f"トークン数: {len(tokens)}")

# 256トークンを超える場合は圧縮
if len(tokens) > 256:
    from prompt_optimizer import PromptOptimizer
    optimizer = PromptOptimizer()
    compressed = optimizer.compress_prompt(your_prompt)
```

#### 5. CUDA/cuDNNバージョン不一致

**症状**
```
ImportError: libnvinfer.so.10: cannot open shared object file
```

**解決方法**

```bash
# Dockerコンテナ使用（推奨）
# すべての依存関係が含まれている
docker run --gpus all -it --rm \
  nvcr.io/nvidia/pytorch:25.01-py3

# またはCUDA/cuDNNを再インストール
pip uninstall tensorrt tensorrt-cu12
pip install tensorrt-cu12 --extra-index-url https://pypi.nvidia.com
```

### パフォーマンスチューニング

#### メモリ使用量の最適化

```python
# 設定の優先順位（低VRAM環境）
config = {
    "use_fp8": True,              # 最優先: 40%メモリ削減
    "height": 768,                # 解像度を下げる
    "width": 768,
    "batch_size": 1,              # バッチサイズは1
    "enable_cuda_graph": False,   # CUDA Graphは無効
}

# 設定の優先順位（高速化重視）
config = {
    "use_fp8": True,              # FP8でも高速
    "height": 1024,
    "width": 1024,
    "batch_size": 1,              # 静的バッチ
    "enable_cuda_graph": True,    # CUDA Graph有効
    "use_static_batch": True,     # 静的バッチエンジン
}
```

#### ベンチマークスクリプト

```python
# benchmark.py
import time
import torch
from custom_sd35_generator import LongPromptSD35Generator

def benchmark(generator, prompt, iterations=10):
    """
    生成速度をベンチマーク
    """
    torch.cuda.synchronize()

    # ウォームアップ
    _ = generator.generate(prompt, steps=10)

    # 計測開始
    torch.cuda.synchronize()
    start_time = time.time()

    for i in range(iterations):
        _ = generator.generate(prompt, steps=30)

    torch.cuda.synchronize()
    elapsed = time.time() - start_time

    avg_time = elapsed / iterations
    print(f"平均生成時間: {avg_time:.2f}秒")
    print(f"画像/秒: {1/avg_time:.2f}")

# 実行
generator = LongPromptSD35Generator(use_fp8=True)
test_prompt = "A test image for benchmarking"
benchmark(generator, test_prompt)
```

## まとめ

本ガイドでは、TensorRTを使用したStable Diffusion 3.5の実装において、T5エンコーダーによる長文プロンプト対応を実現する方法を解説しました。

**重要なポイント**
- SD3.5はT5-XXLエンコーダーにより最大256トークンまで対応
- FP8量子化により40%のメモリ削減と2.3倍の高速化を実現
- Docker環境での構築が最も確実で再現性が高い
- カスタムPythonクラスで柔軟な統合が可能
- プロンプト最適化により効果的な生成が可能

**次のステップ**
1. 本ガイドの手順に従って環境を構築
2. サンプルコードで動作確認
3. 自分のプロジェクトに統合
4. パフォーマンスチューニングで最適化

**参考リソース**
- TensorRT公式リポジトリ: https://github.com/NVIDIA/TensorRT
- SD3.5モデル: https://huggingface.co/stabilityai/stable-diffusion-3.5-large
- TensorRT開発者ガイド: https://docs.nvidia.com/deeplearning/tensorrt/
