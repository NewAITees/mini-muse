#!/usr/bin/env python3
"""
バッチ動画生成スクリプト

指定フォルダ内の画像を自動的に処理し、動画を生成します。

処理フロー:
1. video_input/ から画像を取得
2. Ollamaで各画像から動画プロンプト生成
3. ComfyUIで動画生成
4. 生成された動画を video_output/ にコピー
5. 処理済み画像を video_processed/ に移動

フォルダ構成:
    D:\python\stablediffusion\
    ├── video_input/          # 入力画像フォルダ
    ├── video_output/         # 動画出力フォルダ
    └── video_processed/      # 処理済み画像フォルダ

使い方:
    uv run python batch_video_generation.py

    または環境変数で設定変更:
    INPUT_DIR=/path/to/input OUTPUT_DIR=/path/to/output uv run python batch_video_generation.py
"""

import os
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# モジュールインポート
try:
    from mini_muse.ollama_video_prompt import analyze_image_with_ollama
    from mini_muse.comfy_video_generator import run_comfy_pipeline
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました: {e}")
    print("\n実行方法:")
    print("  PYTHONPATH=/home/perso/analysis/mini-muse uv run python batch_video_generation.py")
    sys.exit(1)

# 環境変数から設定を取得（デフォルト値あり）
BASE_DIR = Path(os.environ.get("BASE_DIR", "/mnt/d/python/stablediffusion"))
INPUT_DIR = Path(os.environ.get("INPUT_DIR", BASE_DIR / "video_input"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR / "video_output"))
PROCESSED_DIR = Path(os.environ.get("PROCESSED_DIR", BASE_DIR / "video_processed"))
WORKFLOW_PATH = Path(os.environ.get("WORKFLOW_PATH", "workflows/wan22_i2v_workflow.json"))

# Ollama/ComfyUI設定
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llava:7b")
COMFY_HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8000")
COMFY_TIMEOUT = int(os.environ.get("COMFY_TIMEOUT", "600"))

# サポートする画像拡張子
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def setup_directories() -> bool:
    """
    必要なディレクトリを作成します。

    Returns:
        bool: 成功した場合True
    """
    print("\n[ディレクトリ設定]")
    print(f"  ベースディレクトリ: {BASE_DIR}")
    print(f"  入力ディレクトリ: {INPUT_DIR}")
    print(f"  出力ディレクトリ: {OUTPUT_DIR}")
    print(f"  処理済みディレクトリ: {PROCESSED_DIR}")

    try:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        print("✓ ディレクトリ準備完了")
        return True
    except Exception as e:
        print(f"✗ ディレクトリ作成エラー: {e}")
        return False


def get_input_images() -> List[Path]:
    """
    入力ディレクトリから画像ファイルを取得します。

    Returns:
        List[Path]: 画像ファイルパスのリスト
    """
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(INPUT_DIR.glob(f"*{ext}"))
        images.extend(INPUT_DIR.glob(f"*{ext.upper()}"))

    # ソート（ファイル名順）
    images = sorted(images)
    return images


def copy_video_from_comfy_to_output(video_filename: str, dest_dir: Path) -> Path:
    """
    ComfyUIの出力ディレクトリから動画をコピーします。

    Args:
        video_filename: 動画ファイル名（例: "ComfyUI_00001_.mp4"）
        dest_dir: コピー先ディレクトリ

    Returns:
        Path: コピー先のファイルパス

    Note:
        ComfyUIの出力ディレクトリは D:\python\stablediffusion\output\comfy\video\ です
    """
    # ComfyUIの出力ディレクトリ（Windowsパス）
    comfy_output = Path("/mnt/d/python/stablediffusion/output/comfy/video")
    source_file = comfy_output / video_filename

    if not source_file.exists():
        raise FileNotFoundError(f"ComfyUI出力ファイルが見つかりません: {source_file}")

    # コピー先のファイルパス
    dest_file = dest_dir / video_filename
    shutil.copy2(source_file, dest_file)

    return dest_file


def process_single_image(
    image_path: Path,
    index: int,
    total: int
) -> Dict[str, Any]:
    """
    単一画像を処理して動画を生成します。

    Args:
        image_path: 入力画像パス
        index: 現在の処理番号（1始まり）
        total: 総処理数

    Returns:
        Dict[str, Any]: 処理結果
            - success: bool - 成功したかどうか
            - image_path: Path - 入力画像パス
            - prompt: str - 生成されたプロンプト
            - video_path: Path - 出力動画パス（成功時）
            - error: str - エラーメッセージ（失敗時）
            - duration: float - 処理時間（秒）
    """
    result = {
        "success": False,
        "image_path": image_path,
        "prompt": None,
        "video_path": None,
        "error": None,
        "duration": 0.0
    }

    start_time = time.time()

    print(f"\n{'='*70}")
    print(f"[{index}/{total}] 処理中: {image_path.name}")
    print(f"{'='*70}")

    try:
        # Step 1: プロンプト生成
        print("\n[Step 1] Ollamaでプロンプト生成中...")
        prompt = analyze_image_with_ollama(
            image_path,
            model=OLLAMA_MODEL,
            host=OLLAMA_HOST,
            timeout=60
        )
        result["prompt"] = prompt
        print(f"✓ プロンプト生成成功")
        print(f"  プロンプト: {prompt}")

        # Step 2: 動画生成
        print("\n[Step 2] ComfyUIで動画生成中...")
        print("  ⚠️  この処理には数分かかる場合があります...")

        # 一時的な出力ディレクトリ
        temp_output = Path("output/batch_temp")

        output_files = run_comfy_pipeline(
            image_path=image_path,
            prompt_text=prompt,
            workflow_path=WORKFLOW_PATH,
            host=COMFY_HOST,
            out_dir=temp_output,
            timeout_s=COMFY_TIMEOUT
        )

        # 動画ファイルをComfyUIの出力ディレクトリからコピー
        # （run_comfy_pipelineは空のリストを返すことがあるため、履歴から取得）
        print("\n[Step 3] 動画ファイルをコピー中...")

        # 最新の動画ファイル名を取得（通常は ComfyUI_XXXXX_.mp4）
        comfy_output = Path("/mnt/d/python/stablediffusion/output/comfy/video")
        video_files = sorted(comfy_output.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

        if video_files:
            latest_video = video_files[0]

            # 出力ファイル名を生成（元の画像名ベース）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{image_path.stem}_{timestamp}.mp4"
            output_path = OUTPUT_DIR / output_filename

            # コピー
            shutil.copy2(latest_video, output_path)
            result["video_path"] = output_path
            print(f"✓ 動画保存成功: {output_path}")
        else:
            raise FileNotFoundError("ComfyUI出力ディレクトリに動画ファイルが見つかりません")

        # Step 3: 画像を処理済みフォルダに移動
        print("\n[Step 4] 画像を処理済みフォルダに移動中...")
        processed_path = PROCESSED_DIR / image_path.name
        shutil.move(str(image_path), str(processed_path))
        print(f"✓ 画像移動成功: {processed_path}")

        result["success"] = True
        result["duration"] = time.time() - start_time

        print(f"\n✓ 処理完了（所要時間: {result['duration']:.1f}秒）")

    except Exception as e:
        result["error"] = str(e)
        result["duration"] = time.time() - start_time
        print(f"\n✗ 処理エラー: {e}")
        print(f"  所要時間: {result['duration']:.1f}秒")

    return result


def main():
    """メイン処理"""
    print("="*70)
    print("バッチ動画生成スクリプト")
    print("="*70)

    # ディレクトリ設定
    if not setup_directories():
        return 1

    # ワークフローの確認
    if not WORKFLOW_PATH.exists():
        print(f"\n✗ ワークフローファイルが見つかりません: {WORKFLOW_PATH}")
        return 1
    print(f"✓ ワークフロー確認: {WORKFLOW_PATH}")

    # 入力画像の取得
    print("\n[入力画像の確認]")
    images = get_input_images()

    if not images:
        print(f"✗ 入力画像が見つかりません: {INPUT_DIR}")
        print(f"  対応形式: {', '.join(IMAGE_EXTENSIONS)}")
        return 1

    print(f"✓ {len(images)}枚の画像を検出")
    for img in images:
        print(f"  - {img.name}")

    # 処理開始確認（環境変数で自動実行可能）
    auto_run = os.environ.get("AUTO_RUN", "").lower() in ("1", "true", "yes")
    if not auto_run:
        print(f"\n{len(images)}枚の画像を処理します。よろしいですか？")
        print("  続行するには Enter キーを押してください...")
        print("  中止するには Ctrl+C を押してください...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n\n処理を中止しました。")
            return 0
    else:
        print(f"\n{len(images)}枚の画像を自動処理します...")

    # バッチ処理
    results = []
    success_count = 0
    failed_count = 0
    total_start_time = time.time()

    for i, image_path in enumerate(images, 1):
        result = process_single_image(image_path, i, len(images))
        results.append(result)

        if result["success"]:
            success_count += 1
        else:
            failed_count += 1

    # 結果サマリー
    total_duration = time.time() - total_start_time

    print("\n" + "="*70)
    print("処理完了")
    print("="*70)
    print(f"総処理時間: {total_duration:.1f}秒 ({total_duration/60:.1f}分)")
    print(f"成功: {success_count}枚")
    print(f"失敗: {failed_count}枚")

    if success_count > 0:
        avg_time = sum(r["duration"] for r in results if r["success"]) / success_count
        print(f"平均処理時間: {avg_time:.1f}秒/枚")

    # 成功した処理の詳細
    if success_count > 0:
        print(f"\n[成功した処理]")
        for r in results:
            if r["success"]:
                print(f"  ✓ {r['image_path'].name} → {r['video_path'].name}")

    # 失敗した処理の詳細
    if failed_count > 0:
        print(f"\n[失敗した処理]")
        for r in results:
            if not r["success"]:
                print(f"  ✗ {r['image_path'].name}: {r['error']}")

    print("\n出力ディレクトリ:")
    print(f"  動画: {OUTPUT_DIR}")
    print(f"  処理済み画像: {PROCESSED_DIR}")
    print("="*70)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
