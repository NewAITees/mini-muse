#!/usr/bin/env python3
"""
ComfyUI APIを使用して実際に画像を生成するテストスクリプト
"""

from mini_muse.comfyui_client import ComfyUIClient
from mini_muse.prompt_generator import PromptGenerator
from datetime import datetime

def main():
    print("="*70)
    print("ComfyUI 画像生成テスト")
    print("="*70)

    # クライアント初期化（ポート8000に接続）
    print("\n[1] ComfyUIクライアントを初期化中...")
    client = ComfyUIClient("127.0.0.1:8000")

    # ワークフロー読み込み
    print("\n[2] ワークフローを読み込み中...")
    workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

    # プロンプト生成器を初期化
    print("\n[3] プロンプト生成器を初期化中...")
    prompt_gen = PromptGenerator()

    # ランダムなプロンプトを生成
    print("\n[4] プロンプトを生成中...")
    prompt = prompt_gen.generate_prompt("abstract_art")
    print(f"\n生成されたプロンプト:")
    print(f"{prompt[:200]}...")

    # 画像生成
    print("\n[5] 画像を生成中...")
    print("これには数十秒かかる場合があります...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"stablediffusion/outputs/test_{timestamp}.png"

    try:
        image_data = client.generate_image(
            workflow,
            positive_prompt=prompt,
            negative_prompt="blurry, low quality, distorted",
            seed=42,
            steps=30,
            cfg=5.45,
            width=1024,
            height=1024,
            save_path=output_path
        )

        print(f"\n{'='*70}")
        print("✓ 画像生成成功！")
        print(f"{'='*70}")
        print(f"保存先: {output_path}")
        print(f"画像サイズ: {len(image_data)} bytes")
        print(f"{'='*70}")

    except Exception as e:
        print(f"\n{'='*70}")
        print("✗ エラーが発生しました")
        print(f"{'='*70}")
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
