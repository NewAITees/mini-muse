#!/usr/bin/env python3
"""
動画生成パイプライン 統合テストスクリプト

このスクリプトは、以下の統合テストを行います：
1. Ollama LMMで画像から動画プロンプト生成
2. ComfyUIで画像→動画生成

使い方:
    uv run python test_video_generation.py

    または

    PYTHONPATH=/home/perso/analysis/mini-muse uv run python test_video_generation.py
"""

import sys
from pathlib import Path

# 環境変数設定（必要に応じて変更）
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llava:7b"
COMFY_HOST = "http://127.0.0.1:8000"

def main():
    print("=" * 70)
    print("動画生成パイプライン統合テスト")
    print("=" * 70)

    # モジュールインポート
    try:
        from mini_muse.ollama_video_prompt import analyze_image_with_ollama
        from mini_muse.comfy_video_generator import run_comfy_pipeline
        print("✓ モジュールのインポート成功")
    except ImportError as e:
        print(f"✗ モジュールのインポートエラー: {e}")
        print("\n実行方法:")
        print("  PYTHONPATH=/home/perso/analysis/mini-muse uv run python test_video_generation.py")
        return 1

    # ComfyUIサーバーの起動確認
    print("\n[事前確認] ComfyUIサーバーの接続確認...")
    try:
        import requests
        r = requests.get(f"{COMFY_HOST}/system_stats", timeout=5)
        if r.status_code == 200:
            print(f"✓ ComfyUIサーバー接続成功: {COMFY_HOST}")
        else:
            print(f"✗ ComfyUIサーバー接続エラー: status={r.status_code}")
            print("\n確認事項:")
            print("  - ComfyUIサーバーが起動しているか確認してください")
            return 1
    except Exception as e:
        print(f"✗ ComfyUIサーバーに接続できません: {e}")
        print(f"\n確認事項:")
        print(f"  - ComfyUIサーバーが起動しているか: {COMFY_HOST}")
        print(f"  - このテストはComfyUIサーバーが必要です")
        print(f"\n⚠️  ComfyUIが起動していないため、Step 1のみ実行します")
        comfy_available = False
    else:
        comfy_available = True

    # テスト用画像の確認
    test_image = Path("input/test_image.jpg")
    if not test_image.exists():
        print(f"✗ テスト用画像が見つかりません: {test_image}")
        print("\nテスト用画像を生成します...")
        from PIL import Image
        test_image.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (640, 640), (100, 150, 200))
        img.save(test_image, "JPEG", quality=90)
        print(f"✓ テスト用画像を生成しました: {test_image}")

    # ワークフローJSONの確認
    workflow_path = Path("workflows/wan22_i2v_workflow.json")
    if not workflow_path.exists():
        print(f"✗ ワークフローJSONが見つかりません: {workflow_path}")
        return 1
    print(f"✓ ワークフローJSON確認: {workflow_path}")

    # Step 1: Ollamaで画像からプロンプト生成
    print("\n[Step 1] 画像からプロンプト生成中...")
    try:
        prompt = analyze_image_with_ollama(
            test_image,
            model=OLLAMA_MODEL,
            host=OLLAMA_HOST,
            timeout=60
        )
        print(f"✓ プロンプト生成成功")
        print(f"  生成されたプロンプト: {prompt}")
    except Exception as e:
        print(f"✗ プロンプト生成エラー: {e}")
        print("\n確認事項:")
        print("  - Ollamaサーバーが起動しているか: ollama serve")
        print(f"  - モデルがインストールされているか: ollama pull {OLLAMA_MODEL}")
        return 1

    # Step 2: ComfyUIで動画生成
    if comfy_available:
        print("\n[Step 2] ComfyUIで動画生成中...")
        print("  ⚠️  この処理には数分かかる場合があります...")
        try:
            output_files = run_comfy_pipeline(
                image_path=test_image,
                prompt_text=prompt,
                workflow_path=workflow_path,
                host=COMFY_HOST,
                out_dir="output/test_pipeline",
                timeout_s=600
            )
            print(f"✓ 動画生成成功")
            print(f"  生成されたファイル:")
            for f in output_files:
                print(f"    - {f}")
        except Exception as e:
            print(f"✗ 動画生成エラー: {e}")
            print("\n確認事項:")
            print("  - ComfyUIサーバーが起動しているか")
            print("  - 必要なモデルがロードされているか")
            print("  - VRAMが十分か")
            return 1
    else:
        print("\n[Step 2] スキップ（ComfyUIサーバーが利用不可）")

    print("\n" + "=" * 70)
    if comfy_available:
        print("✓ 全てのテストが成功しました！")
    else:
        print("✓ Step 1（プロンプト生成）が成功しました！")
        print("⚠️  Step 2（動画生成）はスキップされました")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
