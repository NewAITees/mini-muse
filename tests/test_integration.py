#!/usr/bin/env python3
"""
統合テスト: プロンプト生成 → ComfyUI画像生成

このテストスクリプトは、PromptGeneratorとComfyUIClientを統合して、
実際の画像生成フローが正しく動作することを確認します。
"""

import unittest
import sys
import os
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mini_muse.comfyui_client import ComfyUIClient
from mini_muse.prompt_generator import PromptGenerator


class TestIntegration(unittest.TestCase):
    """統合テストクラス"""

    @classmethod
    def setUpClass(cls):
        """テストクラスのセットアップ"""
        print("\n" + "="*70)
        print("統合テスト開始")
        print("="*70)

        # ComfyUIクライアント初期化
        cls.client = ComfyUIClient("127.0.0.1:8000")

        # プロンプト生成器初期化
        cls.prompt_gen = PromptGenerator()

        # ワークフロー読み込み
        cls.workflow = cls.client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

        # テスト出力ディレクトリ
        cls.test_output_dir = Path("stablediffusion/outputs/test_integration")
        cls.test_output_dir.mkdir(parents=True, exist_ok=True)

    def test_01_prompt_generation(self):
        """テスト1: プロンプト生成が正常に動作すること"""
        print("\n[テスト1] プロンプト生成テスト")

        templates = self.prompt_gen.get_available_templates()
        self.assertGreater(len(templates), 0, "テンプレートが1つ以上存在すること")

        for template in templates:
            prompt = self.prompt_gen.generate_prompt(template)
            self.assertIsInstance(prompt, str, "プロンプトは文字列であること")
            self.assertGreater(len(prompt), 0, "プロンプトは空でないこと")
            print(f"  ✓ テンプレート '{template}': {len(prompt)}文字")

    def test_02_workflow_loading(self):
        """テスト2: ワークフローが正常に読み込めること"""
        print("\n[テスト2] ワークフロー読み込みテスト")

        self.assertIsInstance(self.workflow, dict, "ワークフローは辞書型であること")
        self.assertIn("3", self.workflow, "KSamplerノードが存在すること")
        self.assertIn("16", self.workflow, "ポジティブプロンプトノードが存在すること")
        self.assertIn("54", self.workflow, "ネガティブプロンプトノードが存在すること")
        print("  ✓ ワークフローは正しい構造を持っている")

    def test_03_single_image_generation(self):
        """テスト3: 1枚の画像生成が正常に完了すること"""
        print("\n[テスト3] 単一画像生成テスト")

        # プロンプト生成
        prompt = self.prompt_gen.generate_prompt("abstract_art")
        print(f"  生成プロンプト: {prompt[:80]}...")

        # 画像生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.test_output_dir / f"test_single_{timestamp}.png"

        try:
            image_data = self.client.generate_image(
                self.workflow,
                positive_prompt=prompt,
                negative_prompt="blurry, low quality",
                seed=42,
                steps=30,
                cfg=5.45,
                width=1024,
                height=1024,
                save_path=str(output_path)
            )

            self.assertIsInstance(image_data, bytes, "画像データはbytes型であること")
            self.assertGreater(len(image_data), 0, "画像データは空でないこと")
            self.assertTrue(output_path.exists(), "画像ファイルが保存されていること")
            print(f"  ✓ 画像生成成功: {output_path.name}")
            print(f"  画像サイズ: {len(image_data):,} bytes")

        except Exception as e:
            self.fail(f"画像生成に失敗しました: {e}")

    def test_04_multiple_templates(self):
        """テスト4: 複数のテンプレートで画像生成が成功すること"""
        print("\n[テスト4] 複数テンプレート画像生成テスト")

        templates = ["abstract_art", "detailed_diorama"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, template in enumerate(templates):
            print(f"  [{i+1}/{len(templates)}] テンプレート: {template}")

            # プロンプト生成
            prompt = self.prompt_gen.generate_prompt(template)

            # 画像生成
            output_path = self.test_output_dir / f"test_multi_{template}_{timestamp}.png"

            try:
                image_data = self.client.generate_image(
                    self.workflow,
                    positive_prompt=prompt,
                    negative_prompt="blurry, low quality",
                    seed=100 + i,
                    steps=30,
                    cfg=5.45,
                    width=1024,
                    height=1024,
                    save_path=str(output_path)
                )

                self.assertGreater(len(image_data), 0, "画像データは空でないこと")
                self.assertTrue(output_path.exists(), "画像ファイルが保存されていること")
                print(f"    ✓ 成功: {output_path.name}")

            except Exception as e:
                self.fail(f"テンプレート '{template}' の画像生成に失敗: {e}")

    def test_05_batch_generation_small(self):
        """テスト5: 少量バッチ生成（3枚）が正常に完了すること"""
        print("\n[テスト5] 少量バッチ生成テスト（3枚）")

        batch_size = 3
        template = "abstract_art"
        success_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i in range(batch_size):
            print(f"  [{i+1}/{batch_size}] 生成中...")

            # プロンプト生成
            prompt = self.prompt_gen.generate_prompt(template)

            # 画像生成
            output_path = self.test_output_dir / f"test_batch_{timestamp}_{i+1:02d}.png"

            try:
                image_data = self.client.generate_image(
                    self.workflow,
                    positive_prompt=prompt,
                    negative_prompt="blurry, low quality",
                    seed=200 + i,
                    steps=30,
                    cfg=5.45,
                    width=1024,
                    height=1024,
                    save_path=str(output_path)
                )

                self.assertGreater(len(image_data), 0, "画像データは空でないこと")
                success_count += 1
                print(f"    ✓ 成功")

            except Exception as e:
                print(f"    ✗ 失敗: {e}")

        self.assertEqual(success_count, batch_size, f"{batch_size}枚すべての生成が成功すること")
        print(f"  ✓ バッチ生成完了: {success_count}/{batch_size}枚成功")

    def test_06_parameter_variations(self):
        """テスト6: パラメータを変えた画像生成が成功すること"""
        print("\n[テスト6] パラメータバリエーションテスト")

        # テストケース: (steps, cfg, width, height)
        test_cases = [
            (20, 4.0, 1024, 1024, "低ステップ"),
            (30, 5.45, 1024, 1024, "デフォルト"),
            (40, 7.0, 1024, 1024, "高CFG"),
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt = self.prompt_gen.generate_prompt("abstract_art")

        for i, (steps, cfg, width, height, desc) in enumerate(test_cases):
            print(f"  [{i+1}/{len(test_cases)}] {desc}: steps={steps}, cfg={cfg}")

            output_path = self.test_output_dir / f"test_param_{desc.replace(' ', '_')}_{timestamp}.png"

            try:
                image_data = self.client.generate_image(
                    self.workflow,
                    positive_prompt=prompt,
                    negative_prompt="blurry, low quality",
                    seed=300,
                    steps=steps,
                    cfg=cfg,
                    width=width,
                    height=height,
                    save_path=str(output_path)
                )

                self.assertGreater(len(image_data), 0, "画像データは空でないこと")
                print(f"    ✓ 成功")

            except Exception as e:
                self.fail(f"パラメータ '{desc}' での画像生成に失敗: {e}")

    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        print("\n" + "="*70)
        print("統合テスト完了")
        print(f"テスト出力先: {cls.test_output_dir}")
        print("="*70)


def run_tests():
    """テストを実行"""
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)

    # テストランナーで実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果を返す
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
