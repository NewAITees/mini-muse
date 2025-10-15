# TensorRT Stable Diffusion 3.5 クイックスタートガイド

## 概要

本ガイドは、mini-museプロジェクトでTensorRT Stable Diffusion 3.5環境を構築し、初回の画像生成を実行するまでの実際の手順をまとめたものです。

**検証済み環境**
- OS: WSL2 (Ubuntu 22.04)
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- System RAM: 32GB
- Docker: 最新版
- CUDA: 12.9

**達成内容**
- TensorRT Stable Diffusion 3.5 Medium環境の構築
- T5エンコーダー（256トークン長文プロンプト対応）
- 画像生成速度: 約16秒/画像 (1024x1024, 30ステップ)

## 前提条件

### 必須環境

1. **WSL2 + GPU対応**
   ```bash
   # WSL2でnvidia-smiが動作すること
   nvidia-smi
   ```

2. **Docker + NVIDIA Container Toolkit**
   ```bash
   # NVIDIA Docker runtimeが動作すること
   docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
   ```

3. **HuggingFaceトークン**
   - https://huggingface.co/settings/tokens でトークンを作成
   - SD3.5モデルへのアクセス権限を取得

## セットアップ手順

### Step 1: HuggingFaceトークンの設定

```bash
# トークンをキャッシュに保存
echo "your_huggingface_token_here" > ~/.cache/huggingface/token

# または環境変数で設定
export HF_TOKEN="your_huggingface_token_here"
```

### Step 2: プロジェクトの確認

```bash
cd /home/perso/analysis/mini-muse

# 必要なファイルが存在することを確認
ls docker/tensorrt-sd35.Dockerfile
ls docker/docker-compose.tensorrt.yml
ls scripts/run_tensorrt_demo.sh
```

### Step 3: Dockerイメージのビルド

```bash
# イメージをビルド（初回は15-20分程度）
./scripts/run_tensorrt_demo.sh build
```

**ビルド結果**:
- イメージ名: `mini-muse/tensorrt-sd35:latest`
- サイズ: 約43.4GB
- ベースイメージ: `nvcr.io/nvidia/pytorch:25.01-py3`

### Step 4: コンテナの起動

```bash
# コンテナを起動
./scripts/run_tensorrt_demo.sh start
```

**確認**:
```bash
# コンテナが起動していることを確認
docker ps | grep tensorrt-sd35
```

### Step 5: GPU動作確認

```bash
# コンテナ内でGPU確認
docker exec tensorrt-sd35 nvidia-smi
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

### Step 6: TensorRTエンジンのビルド

エンジンのビルドは**初回のみ**必要です（20-30分程度）。

```bash
# SD3.5 Medium用エンジンをビルド
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --build-enable-refit \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  --batch-size 1 \
  "test image"
```

**ビルド内容**:
1. ONNXモデルの最適化
2. T5エンコーダーエンジン（256トークン対応）
3. Transformerエンジン（SD3.5メインモデル）
4. VAEデコーダーエンジン

**ビルド成功の確認**:
```bash
# エンジンファイルが作成されたことを確認
docker exec tensorrt-sd35 ls -lh engine/StableDiffusion35Pipeline_3.5-medium/
```

### Step 7: 画像生成デモの実行

エンジンビルド完了後、画像生成が可能になります。

```bash
# シンプルなプロンプトで生成
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "A beautiful sunset over mountains, highly detailed, 8k"
```

**生成画像の確認**:
```bash
# 出力ディレクトリを確認
docker exec tensorrt-sd35 ls -lh /workspace/TensorRT/demo/Diffusion/output/
```

## パフォーマンス計測結果

### 検証環境
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- モデル: Stable Diffusion 3.5 Medium
- 解像度: 1024x1024
- ステップ数: 30
- 精度: FP16

### 生成速度

| コンポーネント | レイテンシ |
|----------------|------------|
| CLIP-G         | 10.09 ms   |
| CLIP-L         | 4.46 ms    |
| T5エンコーダー | 27.18 ms   |
| MMDiT (30ステップ) | 17,040.91 ms |
| VAEデコーダー  | 75.63 ms   |
| **パイプライン全体** | **16,110 ms (約16秒)** |

**スループット**: 0.062 画像/秒

### メモリ使用量

- VRAM使用量: 約3.2GB (アイドル時を含む)
- システムRAM: コンテナで最大24GB（共有メモリ）
- エンジンファイルサイズ: 約10GB（3つのエンジン合計）

## トラブルシューティング

### 1. エンジンビルドがSIGKILL (9)で失敗

**症状**:
```
subprocess.CalledProcessError: Command '...' died with <Signals.SIGKILL: 9>
```

**原因**: メモリ不足（主に共有メモリ）

**解決方法**:
```bash
# docker-compose.tensorrt.yml を編集
shm_size: '24gb'  # 16gbから増やす

# コンテナを再起動
./scripts/run_tensorrt_demo.sh stop
./scripts/run_tensorrt_demo.sh start
```

### 2. GPU not found

**症状**:
```
RuntimeError: No CUDA devices found
```

**解決方法**:
```bash
# WSL2でnvidia-smiが動作するか確認
nvidia-smi

# 動作しない場合、WSLを更新
wsl --update
wsl --shutdown
# WSLを再起動
```

### 3. HuggingFaceモデルダウンロードエラー

**症状**:
```
HTTPError: 401 Client Error: Unauthorized
```

**解決方法**:
```bash
# トークンを再設定
export HF_TOKEN="your_new_token"

# またはキャッシュを更新
echo "your_new_token" > ~/.cache/huggingface/token

# コンテナを再起動
./scripts/run_tensorrt_demo.sh stop
./scripts/run_tensorrt_demo.sh start
```

### 4. コンテナ起動エラー

**症状**:
```
Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

**解決方法**:
```bash
# NVIDIA Container Toolkitをインストール
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## 便利なコマンド

### コンテナ管理

```bash
# コンテナを起動
./scripts/run_tensorrt_demo.sh start

# コンテナを停止
./scripts/run_tensorrt_demo.sh stop

# コンテナのシェルに入る
docker exec -it tensorrt-sd35 /bin/bash

# ログを表示
docker logs -f tensorrt-sd35
```

### エンジン管理

```bash
# エンジンファイルを確認
docker exec tensorrt-sd35 ls -lh engine/StableDiffusion35Pipeline_3.5-medium/

# エンジンを削除（再ビルド時）
docker exec tensorrt-sd35 rm -rf engine/StableDiffusion35Pipeline_3.5-medium/
```

### 生成画像の取得

```bash
# ホストにコピー
docker cp tensorrt-sd35:/workspace/TensorRT/demo/Diffusion/output/. ./output/

# または直接確認
docker exec tensorrt-sd35 ls -lh /workspace/TensorRT/demo/Diffusion/output/
```

## 応用例

### 1. 長文プロンプトでの生成

T5エンコーダーは最大256トークンに対応しています。

```bash
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "A breathtaking landscape featuring towering snow-capped mountains under a vibrant sunset sky, with golden rays piercing through dramatic clouds, reflecting on a serene crystal-clear lake surrounded by lush pine forests, highly detailed, 8k resolution, photorealistic, professional photography"
```

### 2. 高品質生成（ステップ数を増やす）

```bash
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 1024 \
  --width 1024 \
  --denoising-steps 50 \
  "A masterpiece of digital art"
```

### 3. ネガティブプロンプトの使用

```bash
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  --negative-prompt "blurry, low quality, distorted, ugly" \
  "A beautiful portrait"
```

### 4. 異なる解像度での生成

```bash
# 横長画像（16:9）
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 768 \
  --width 1360 \
  --denoising-steps 30 \
  "A cinematic landscape"
```

**注意**: 解像度を変更する場合、エンジンを再ビルドする必要があります。

## 次のステップ

### 1. SD3.5 Largeモデルの使用

より高品質な生成には、Largeモデルを使用できます（要24GB VRAM）。

```bash
# Largeモデル用エンジンをビルド
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-large \
  --build-enable-refit \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "test image"
```

### 2. FP8量子化による高速化

メモリを削減し、さらに高速化するにはFP8量子化を使用できます。

```bash
# FP8エンジンをビルド
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --fp8 \
  --build-enable-refit \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "test image"
```

### 3. mini-museプロジェクトとの統合

TensorRTコンテナをmini-museアプリケーションから呼び出す実装（将来的な拡張）。

```python
# mini_muse/services/tensorrt_client.py (将来的な実装例)
class TensorRTClient:
    def __init__(self):
        self.container_name = "tensorrt-sd35"

    def generate_image(self, prompt: str, **kwargs) -> Path:
        """TensorRTコンテナで画像を生成"""
        # Docker exec経由でTensorRT実行
        pass
```

## まとめ

本ガイドでは、以下を達成しました：

1. ✅ **Docker環境の構築**
   - NVIDIA公式PyTorchコンテナベース
   - 全依存関係を含む43.4GBのイメージ

2. ✅ **TensorRTエンジンのビルド**
   - T5エンコーダー（256トークン長文プロンプト対応）
   - Transformerエンジン（SD3.5 Medium）
   - VAEデコーダーエンジン

3. ✅ **画像生成の実行**
   - 1024x1024解像度
   - 約16秒/画像のパフォーマンス
   - RTX 4090で検証済み

4. ✅ **devcontainerとの分離**
   - mini-muse開発環境とは独立
   - 依存関係の競合なし

**重要なポイント**:
- エンジンビルドは初回のみ（20-30分）
- ビルド後は高速な画像生成が可能
- 共有メモリ（shm_size）は24GB推奨
- T5エンコーダーで長文プロンプト対応

**参考ドキュメント**:
- 詳細なセットアップ: `doc/tensorrt_sd35_docker_setup.md`
- ローカル環境向け: `doc/tensorrt_sd35_setup_guide.md`
- 変更履歴: `doc/CHANGELOG_20251003.md`
