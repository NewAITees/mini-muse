# 変更履歴 - 2025年10月3日

## 追加されたドキュメント

### 1. TensorRT SD3.5セットアップガイド（ローカル環境向け）
- **ファイル**: `doc/tensorrt_sd35_setup_guide.md`
- **内容**: Stable Diffusion 3.5のTensorRT実装における長文プロンプト対応（最大256トークン）のための環境構築ガイド（WSL2ローカル環境）

### 2. TensorRT SD3.5 Dockerセットアップガイド（推奨）
- **ファイル**: `doc/tensorrt_sd35_docker_setup.md`
- **内容**: Docker環境でのTensorRT SD3.5セットアップガイド
- **特徴**:
  - NVIDIA公式PyTorchコンテナベース
  - devcontainerとは独立した構成
  - 依存関係の問題を回避
  - 再現性の高い環境

## 追加されたDocker環境

### TensorRT専用Dockerコンテナ
- **Dockerfile**: `docker/tensorrt-sd35.Dockerfile`
- **ベースイメージ**: `nvcr.io/nvidia/pytorch:25.01-py3`
- **含まれる依存関係**:
  - TensorRT
  - CUDA 12.9
  - PyTorch 2.x
  - Diffusers
  - Transformers
  - すべてのTensorRT Diffusion依存関係

### Docker Compose設定
- **ファイル**: `docker/docker-compose.tensorrt.yml`
- **機能**:
  - GPU完全サポート（`--gpus all`）
  - HuggingFaceキャッシュの永続化
  - TensorRTエンジンの永続化
  - Stable Diffusionデータマウント（Windows Dドライブ対応）
  - 16GB共有メモリ設定

### コンテナ管理スクリプト
- **ファイル**: `scripts/run_tensorrt_demo.sh`
- **機能**:
  - Dockerイメージビルド
  - コンテナ起動/停止
  - デモ実行
  - エンジンビルド
  - GPU状態確認
  - クリーンアップ

## 使用方法

### Docker環境でのクイックスタート

```bash
# 1. Dockerイメージをビルド（初回のみ、15-20分）
./scripts/run_tensorrt_demo.sh build

# 2. コンテナを起動
./scripts/run_tensorrt_demo.sh start

# 3. TensorRTエンジンをビルド（初回のみ、20-30分）
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --build-enable-refit \
  --build-static-batch \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "test image"

# 4. 画像生成デモを実行
docker exec tensorrt-sd35 python demo_txt2img_sd35.py \
  --version 3.5-medium \
  --height 1024 \
  --width 1024 \
  --denoising-steps 30 \
  "A beautiful sunset over mountains, highly detailed, 8k"
```

### 既存のdevcontainerとの使い分け

- **devcontainer（.devcontainer/）**: mini-museアプリケーション開発用
- **TensorRT Docker**: 画像生成・推論専用

両者は独立して動作し、互いに干渉しません。

## 検証済み動作環境

### ハードウェア
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- System RAM: 32GB
- OS: WSL2 (Ubuntu 22.04)

### パフォーマンス実測値
- 画像生成速度: **16.1秒/画像** (1024x1024, 30ステップ)
- スループット: 0.062 画像/秒
- VRAM使用量: 約3.2GB
- Dockerイメージサイズ: 43.4GB
- エンジンファイルサイズ: 約10GB（3エンジン合計）

### コンポーネント別レイテンシ
| コンポーネント | レイテンシ |
|----------------|------------|
| CLIP-G         | 10.09 ms   |
| CLIP-L         | 4.46 ms    |
| T5エンコーダー | 27.18 ms   |
| MMDiT (30ステップ) | 17,040.91 ms |
| VAEデコーダー  | 75.63 ms   |

### 生成例
- 解像度: 1024x1024
- モデル: Stable Diffusion 3.5 Medium
- T5エンコーダー: 256トークン長文プロンプト対応
- 出力先: `/workspace/TensorRT/demo/Diffusion/output/`
- 生成画像サイズ: 約1.9MB/枚

#### ガイドの主要セクション

1. **概要とシステム要件**
   - GPU要件（RTX 4000シリーズ以降推奨）
   - VRAM要件（12GB～24GB）
   - ソフトウェア要件（WSL2、Python 3.11、CUDA 12.4以降）

2. **WSL2のGPU対応セットアップ**
   - WSL2とUbuntuのインストール確認
   - NVIDIA Driver確認
   - WSL内でのCUDA動作確認

3. **uvによる環境構築**
   - uvのインストール手順
   - プロジェクトディレクトリのセットアップ
   - 基本依存関係のインストール
   - PyTorch + CUDA動作確認テスト

4. **TensorRT環境のセットアップ**
   - TensorRTと関連ライブラリのインストール
   - TensorRTインストール確認テスト
   - Diffusers/Transformersのセットアップ

5. **HuggingFace認証のセットアップ**
   - トークンの取得方法
   - 認証設定手順
   - SD3.5モデルへのアクセス確認

6. **TensorRT公式リポジトリのセットアップ**
   - リポジトリのクローン手順
   - Demo依存関係のインストール
   - エンジンビルド準備完了確認

7. **全テストの一括実行**
   - 統合テストスクリプトの作成
   - 環境検証の自動化

8. **トラブルシューティング**
   - よくある問題と解決方法（6項目）
   - パフォーマンスチューニング
   - ベンチマークスクリプト

9. **次のステップ**
   - エンジンビルドの実行方法
   - カスタム実装の開始手順

#### 技術的特徴

- **プロンプト長**: 最大256トークン（デフォルト77トークンの3倍以上）
- **パフォーマンス**: BF16 PyTorchと比較して1.7倍～2.3倍高速
- **メモリ削減**: FP8量子化で40%のVRAM削減
- **実装難易度**: 中級（Python開発経験者向け）

#### 含まれるテストスクリプト

1. `test_01_pytorch_cuda.py` - PyTorch + CUDA動作確認
2. `test_02_tensorrt.py` - TensorRTインストール確認
3. `test_03_diffusers.py` - Diffusers/Transformers確認
4. `test_04_huggingface.py` - HuggingFace接続確認
5. `test_05_ready_to_build.py` - エンジンビルド準備完了確認
6. `run_all_tests.sh` - 統合テストスクリプト

## 参考リソース

- TensorRT公式リポジトリ: https://github.com/NVIDIA/TensorRT
- SD3.5モデル: https://huggingface.co/stabilityai/stable-diffusion-3.5-large
- TensorRT開発者ガイド: https://docs.nvidia.com/deeplearning/tensorrt/

## 備考

このガイドは、mini-museプロジェクトにおけるNVIDIA TensorRTとStable Diffusion 3.5の統合を支援するために作成されました。WSL2環境でのGPU対応、uvによるモダンなPython環境管理、および長文プロンプト対応の実装方法を包括的に解説しています。
