# TensorRT Stable Diffusion 3.5 Docker環境セットアップガイド

## 概要

本ガイドでは、mini-museプロジェクトにおいて、NVIDIA公式PyTorchコンテナをベースとしたTensorRT Stable Diffusion 3.5環境の構築手順を解説します。

**主な特徴**
- **Docker分離構成**: TensorRT環境を専用Dockerコンテナで実行
- **devcontainerとの併用**: 既存のdevcontainerとは独立した環境
- **NVIDIA公式ベース**: `nvcr.io/nvidia/pytorch:25.01-py3` を使用
- **依存関係の解決**: すべての依存関係がコンテナ内で完結

## 前提条件

### 必須環境

- **OS**: WSL2 (Ubuntu 22.04推奨)
- **GPU**: NVIDIA RTX 4000シリーズ以降
- **VRAM**: 最低12GB（FP8量子化時）、推奨18GB以上
- **Docker**: 20.10以降
- **Docker Compose**: v2.0以降
- **NVIDIA Container Toolkit**: インストール済み

### WSL2でのNVIDIA Container Toolkit確認

```bash
# NVIDIA Docker runtimeの動作確認
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

成功すれば、コンテナ内でGPU情報が表示されます。

## プロジェクト構成

```
mini-muse/
├── docker/
│   ├── tensorrt-sd35.Dockerfile      # TensorRT専用Dockerfile
│   └── docker-compose.tensorrt.yml   # Docker Compose設定
├── scripts/
│   └── run_tensorrt_demo.sh          # コンテナ管理スクリプト
├── TensorRT/                          # NVIDIA TensorRTリポジトリ
│   └── demo/Diffusion/                # デモスクリプト
└── .devcontainer/                     # 既存のdevcontainer（mini-muse用）
```

## セットアップ手順

### Step 1: HuggingFaceトークンの設定

```bash
# HuggingFaceトークンを環境変数に設定
export HF_TOKEN="your_huggingface_token_here"

# または ~/.cache/huggingface/token に保存
echo "your_huggingface_token_here" > ~/.cache/huggingface/token
```

**トークンの取得方法**:
1. https://huggingface.co/settings/tokens にアクセス
2. "New token" をクリック
3. Name: "tensorrt-sd35"
4. Type: "Read" を選択
5. トークンをコピー

### Step 2: Dockerイメージのビルド

```bash
# プロジェクトルートに移動
cd /home/perso/analysis/mini-muse

# イメージをビルド（初回は15-20分程度かかります）
./scripts/run_tensorrt_demo.sh build
```

ビルド内容：
- NVIDIA PyTorch 25.01コンテナをベースに構築
- TensorRT Diffusionの全依存関係をインストール
- HuggingFaceキャッシュディレクトリを設定

### Step 3: コンテナの起動

```bash
# コンテナを起動
./scripts/run_tensorrt_demo.sh start

# 起動確認
docker ps | grep tensorrt-sd35
```

### Step 4: GPU動作確認

```bash
# コンテナ内でGPU確認
./scripts/run_tensorrt_demo.sh gpu
```

**期待される出力**:
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 575.xx       Driver Version: 576.xx         CUDA Version: 12.9     |
+-----------------------------------------------------------------------------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA GeForce RTX 4090        On  |   00000000:01:00.0  On |                  Off |
+-----------------------------------------------------------------------------------------+
```

### Step 5: TensorRTエンジンのビルド

初回実行時は、TensorRTエンジンをビルドする必要があります（20-30分程度）。

```bash
# SD3.5 Medium用エンジンをビルド
./scripts/run_tensorrt_demo.sh build-engine 3.5-medium

# または SD3.5 Large用エンジンをビルド
./scripts/run_tensorrt_demo.sh build-engine 3.5-large
```

**エンジンビルドの進行状況**:
- モデルのダウンロード（初回のみ）
- ONNX形式への変換
- TensorRTエンジンの最適化
- エンジンファイルの保存

エンジンは以下に保存されます：
```
TensorRT/demo/Diffusion/engine/
```

### Step 6: デモの実行

エンジンビルド完了後、画像生成デモを実行できます。

```bash
# デフォルトプロンプトで実行
./scripts/run_tensorrt_demo.sh demo

# カスタムプロンプトで実行
./scripts/run_tensorrt_demo.sh demo "A beautiful landscape with mountains, sunset, highly detailed, 8k"

# SD3.5 Largeで実行（ステップ数50）
./scripts/run_tensorrt_demo.sh demo "A futuristic cityscape at night" 3.5-large 50
```

**デモパラメータ**:
- 引数1: プロンプト（デフォルト: "A beautiful sunset over mountains..."）
- 引数2: バージョン（3.5-medium または 3.5-large、デフォルト: 3.5-medium）
- 引数3: ステップ数（デフォルト: 30）

生成画像は以下に保存されます：
```
TensorRT/demo/Diffusion/output/
```

## コンテナ管理コマンド

### 基本操作

```bash
# コンテナを起動
./scripts/run_tensorrt_demo.sh start

# コンテナを停止
./scripts/run_tensorrt_demo.sh stop

# コンテナのシェルに入る
./scripts/run_tensorrt_demo.sh shell

# ログを表示
./scripts/run_tensorrt_demo.sh logs
```

### コンテナ内での手動実行

```bash
# コンテナに入る
./scripts/run_tensorrt_demo.sh shell

# コンテナ内で手動実行
cd /workspace/TensorRT/demo/Diffusion

python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --prompt "Your prompt here" \
  --denoising-steps 30 \
  --height 1024 \
  --width 1024 \
  --batch-size 1
```

### クリーンアップ

```bash
# エンジンと出力を削除
./scripts/run_tensorrt_demo.sh cleanup

# コンテナを完全に削除
docker-compose -f docker/docker-compose.tensorrt.yml down -v
```

## 詳細設定

### docker-compose.tensorrt.yml の主要設定

```yaml
services:
  tensorrt-sd35:
    # GPUアクセス
    runtime: nvidia

    # 環境変数
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - HF_TOKEN=${HF_TOKEN:-}
      - CUDA_MODULE_LOADING=LAZY

    # ボリュームマウント
    volumes:
      # プロジェクト全体
      - ..:/workspace

      # HuggingFaceキャッシュ（永続化）
      - ${HOME}/.cache/huggingface:/workspace/.cache/huggingface

      # Stable Diffusionデータ（Windowsマウント）
      - /mnt/d/python/stablediffusion:/workspace/stable_diffusion_data

      # TensorRTエンジン（永続化）
      - tensorrt-engines:/workspace/TensorRT/demo/Diffusion/engine

      # 出力（永続化）
      - tensorrt-outputs:/workspace/TensorRT/demo/Diffusion/output

    # 共有メモリ（大きなモデル用）
    shm_size: '16gb'
```

### 環境変数のカスタマイズ

`.env` ファイルをプロジェクトルートに作成：

```bash
# .env
HF_TOKEN=your_huggingface_token_here
CUDA_VISIBLE_DEVICES=0
```

### ストレージパスの変更

Windows Dドライブ以外を使用する場合、`docker-compose.tensorrt.yml` を編集：

```yaml
volumes:
  # カスタムパスに変更
  - /your/custom/path:/workspace/stable_diffusion_data
```

## 既存のdevcontainerとの使い分け

### devcontainer（mini-muse開発用）

- **用途**: mini-museアプリケーションの開発・テスト
- **起動方法**: VS Codeの"Reopen in Container"
- **特徴**:
  - Pythonコード編集とデバッグ
  - TUIアプリケーション開発
  - 軽量な依存関係

### TensorRT Docker（推論専用）

- **用途**: TensorRT SD3.5での画像生成
- **起動方法**: `./scripts/run_tensorrt_demo.sh start`
- **特徴**:
  - 重い依存関係が分離
  - NVIDIA最適化済み環境
  - 再現性の高い推論環境

### 併用パターン

1. **開発時**:
   ```bash
   # VS Codeでdevcontainerを開く
   code .
   # → devcontainer内でmini-museコードを編集
   ```

2. **画像生成時**:
   ```bash
   # TensorRTコンテナで推論実行
   ./scripts/run_tensorrt_demo.sh demo "Your prompt"
   ```

3. **統合テスト時**:
   ```bash
   # mini-museからTensorRTコンテナを呼び出す
   # （将来的な実装予定）
   ```

## トラブルシューティング

### 1. Dockerビルドエラー

**症状**:
```
ERROR: failed to solve: failed to fetch...
```

**解決方法**:
```bash
# Dockerキャッシュをクリア
docker builder prune -a

# 再ビルド
./scripts/run_tensorrt_demo.sh build
```

### 2. GPU not found

**症状**:
```
RuntimeError: No CUDA devices found
```

**解決方法**:
```bash
# WSL2でNVIDIA Driverを確認
nvidia-smi

# NVIDIA Container Toolkitを再インストール
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3. HuggingFaceモデルダウンロードエラー

**症状**:
```
HTTPError: 401 Client Error: Unauthorized
```

**解決方法**:
```bash
# HF_TOKENを再設定
export HF_TOKEN="your_new_token"

# コンテナを再起動
./scripts/run_tensorrt_demo.sh stop
./scripts/run_tensorrt_demo.sh start
```

### 4. メモリ不足エラー

**症状**:
```
RuntimeError: CUDA out of memory
```

**解決方法**:

```bash
# エンジンをFP8量子化でリビルド
docker exec -it tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --prompt "test" \
  --build-only \
  --onnx-opset 18 \
  --fp8
```

または解像度を下げる：
```bash
./scripts/run_tensorrt_demo.sh demo "Your prompt" 3.5-medium 30 768 768
```

### 5. 共有メモリ不足

**症状**:
```
ERROR: /dev/shm is too small
```

**解決方法**:

`docker-compose.tensorrt.yml` を編集：
```yaml
shm_size: '32gb'  # 16gbから増やす
```

## パフォーマンス最適化

### エンジンビルドオプション

```bash
# 最速設定（FP8 + 静的バッチ）
docker exec -it tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --prompt "test" \
  --build-only \
  --build-static-batch \
  --build-enable-refit \
  --fp8 \
  --onnx-opset 18
```

### 推論速度の比較

| 設定 | VRAM使用量 | 生成速度（RTX 4090） |
|------|------------|---------------------|
| FP16 標準 | 18GB | 約3.0秒/画像 |
| FP8 量子化 | 12GB | 約1.3秒/画像 |
| BF16 PyTorch | 20GB | 約7.0秒/画像 |

## 次のステップ

### 1. mini-museプロジェクトとの統合

TensorRTコンテナをmini-museから呼び出す実装を検討：

```python
# mini_muse/services/tensorrt_client.py (将来的な実装)
class TensorRTClient:
    def generate_image(self, prompt: str) -> Path:
        # Dockerコンテナ内でTensorRT実行
        pass
```

### 2. カスタムモデルの追加

他のStable Diffusionモデルを追加：
- SD3.5 Turbo
- SDXL
- Flux

### 3. バッチ処理の実装

複数プロンプトの一括処理：
```bash
# バッチスクリプト例
cat prompts.txt | xargs -I {} ./scripts/run_tensorrt_demo.sh demo "{}"
```

## 参考リソース

- **NVIDIA TensorRT**: https://github.com/NVIDIA/TensorRT
- **SD3.5モデル**: https://huggingface.co/stabilityai/stable-diffusion-3.5-large
- **NVIDIA PyTorchコンテナ**: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch
- **Docker Compose**: https://docs.docker.com/compose/

## まとめ

本ガイドでは、mini-museプロジェクトにおけるTensorRT SD3.5のDocker環境構築手順を解説しました。

**重要なポイント**:
- TensorRT環境を専用Dockerコンテナで分離
- NVIDIA公式コンテナで依存関係の問題を回避
- 既存のdevcontainerとは独立した運用
- スクリプトによる簡単な管理

Docker環境を使用することで、依存関係の競合を避け、安定した推論環境を実現できます。
