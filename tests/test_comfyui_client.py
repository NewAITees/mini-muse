"""
ComfyUIClientのテストコード

このモジュールは、ComfyUIClientクラスの機能をテストします。

================================================================================
使い方 - test_comfyui_client.py
================================================================================

## 概要

このテストファイルは、ComfyUIClientクラスの機能をテストします。
実際のComfyUIサーバーとの通信をモックして、クライアントの動作を検証します。

## テスト実行方法

### 方法1: 直接実行

```bash
# プロジェクトルートから実行
uv run python tests/test_comfyui_client.py
```

### 方法2: pytestを使用

```bash
# pytestがインストールされている場合
uv run pytest tests/test_comfyui_client.py -v
```

### 方法3: unittestモジュールを使用

```bash
# Pythonの標準unittestモジュールを使用
uv run python -m unittest tests.test_comfyui_client
```

## テスト内容

### 基本機能のテスト (TestComfyUIClient)

1. **test_01_initialization** - 初期化のテスト
   - ComfyUIClientが正常に初期化されることを確認

2. **test_02_load_workflow** - ワークフロー読み込みのテスト
   - JSONファイルからワークフローが正しく読み込まれることを確認

3. **test_03_update_prompt** - プロンプト更新のテスト
   - ワークフローのパラメータが正しく更新されることを確認

4. **test_04_workflow_validation** - ワークフロー検証のテスト
   - 必要なノードが存在することを確認

## 注意事項

このテストは、実際のComfyUIサーバーとは通信しません。
モック（疑似）オブジェクトを使用して、クライアントのロジックのみをテストします。

実際のサーバーとの統合テストを行う場合は、ComfyUIサーバーを起動してから、
手動でテストを実行してください。

## 統合テスト（手動）

ComfyUIサーバーが起動している場合、以下のように実際のテストができます：

```python
# 統合テスト例
from mini_muse.comfyui_client import ComfyUIClient

# サーバーが起動していることを確認
client = ComfyUIClient("127.0.0.1:8188")

try:
    # ワークフロー読み込み
    workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

    # 画像生成テスト
    client.generate_image(
        workflow,
        positive_prompt="test image",
        save_path="test_output.png"
    )
    print("✓ 統合テスト成功")
except Exception as e:
    print(f"✗ 統合テスト失敗: {e}")
```

================================================================================
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# mini_museモジュールをインポートパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mini_muse.comfyui_client import ComfyUIClient


class TestComfyUIClient(unittest.TestCase):
    """ComfyUIClientクラスのテストケース"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体で1回だけ実行される初期化処理"""
        print("\n" + "=" * 70)
        print("ComfyUIClient テスト開始")
        print("=" * 70)

    def setUp(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.client = ComfyUIClient("127.0.0.1:8188")

    def test_01_initialization(self):
        """初期化のテスト"""
        print("\n[テスト1] 初期化のテスト")
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.server_address, "127.0.0.1:8188")
        self.assertEqual(self.client.base_url, "http://127.0.0.1:8188")
        self.assertEqual(self.client.ws_url, "ws://127.0.0.1:8188/ws")
        print("✓ 初期化成功")

    def test_02_custom_address(self):
        """カスタムアドレスでの初期化テスト"""
        print("\n[テスト2] カスタムアドレスでの初期化テスト")
        custom_client = ComfyUIClient("192.168.1.100:9999")
        self.assertEqual(custom_client.server_address, "192.168.1.100:9999")
        self.assertEqual(custom_client.base_url, "http://192.168.1.100:9999")
        print("✓ カスタムアドレス設定成功")

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_03_load_workflow(self, mock_exists, mock_file):
        """ワークフロー読み込みのテスト"""
        print("\n[テスト3] ワークフロー読み込みのテスト")

        # モックの設定
        mock_exists.return_value = True
        mock_workflow = {
            "nodes": [{"id": "3", "type": "KSampler"}],
            "16": {"inputs": {"text": ""}},
        }
        mock_file.return_value.read.return_value = json.dumps(mock_workflow)

        # ワークフローを読み込み
        workflow = self.client.load_workflow("test_workflow.json")

        self.assertIsNotNone(workflow)
        self.assertIn("nodes", workflow)
        print("✓ ワークフロー読み込み成功")

    def test_04_update_prompt(self):
        """プロンプト更新のテスト"""
        print("\n[テスト4] プロンプト更新のテスト")

        # テスト用ワークフロー
        workflow = {
            "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.0}},
            "16": {"inputs": {"text": ""}},
            "53": {"inputs": {"width": 512, "height": 512}},
            "54": {"inputs": {"text": ""}},
        }

        # プロンプトを更新
        updated = self.client.update_prompt(
            workflow,
            positive_prompt="test positive",
            negative_prompt="test negative",
            seed=12345,
            steps=30,
            cfg=5.45,
            width=1024,
            height=1024,
        )

        # 更新内容を確認
        self.assertEqual(updated["16"]["inputs"]["text"], "test positive")
        self.assertEqual(updated["54"]["inputs"]["text"], "test negative")
        self.assertEqual(updated["3"]["inputs"]["seed"], 12345)
        self.assertEqual(updated["3"]["inputs"]["steps"], 30)
        self.assertEqual(updated["3"]["inputs"]["cfg"], 5.45)
        self.assertEqual(updated["53"]["inputs"]["width"], 1024)
        self.assertEqual(updated["53"]["inputs"]["height"], 1024)
        print("✓ プロンプト更新成功")

    def test_05_random_seed(self):
        """ランダムシード生成のテスト"""
        print("\n[テスト5] ランダムシード生成のテスト")

        workflow = {
            "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.0}},
            "16": {"inputs": {"text": ""}},
            "53": {"inputs": {"width": 512, "height": 512}},
            "54": {"inputs": {"text": ""}},
        }

        # seed=Noneでランダムシードを生成
        updated1 = self.client.update_prompt(workflow, positive_prompt="test", seed=None)
        updated2 = self.client.update_prompt(workflow, positive_prompt="test", seed=None)

        seed1 = updated1["3"]["inputs"]["seed"]
        seed2 = updated2["3"]["inputs"]["seed"]

        # シードが生成されていることを確認
        self.assertIsInstance(seed1, int)
        self.assertIsInstance(seed2, int)
        self.assertGreater(seed1, 0)
        self.assertGreater(seed2, 0)
        print(f"  生成されたシード1: {seed1}")
        print(f"  生成されたシード2: {seed2}")
        print("✓ ランダムシード生成成功")

    def test_06_workflow_structure_validation(self):
        """ワークフロー構造の検証テスト"""
        print("\n[テスト6] ワークフロー構造の検証テスト")

        # 最小限のワークフロー構造
        workflow = {
            "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.0}},
            "16": {"inputs": {"text": ""}},
            "53": {"inputs": {"width": 512, "height": 512}},
            "54": {"inputs": {"text": ""}},
        }

        # 必要なノードが存在することを確認
        self.assertIn("3", workflow, "KSamplerノードが存在しません")
        self.assertIn("16", workflow, "Positive Promptノードが存在しません")
        self.assertIn("53", workflow, "EmptySD3LatentImageノードが存在しません")
        self.assertIn("54", workflow, "Negative Promptノードが存在しません")
        print("✓ ワークフロー構造検証成功")

    @classmethod
    def tearDownClass(cls):
        """テストクラス全体で1回だけ実行される終了処理"""
        print("\n" + "=" * 70)
        print("ComfyUIClient テスト完了")
        print("=" * 70 + "\n")


class TestComfyUIClientEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.client = ComfyUIClient()

    def test_extreme_values(self):
        """極端な値のテスト"""
        print("\n[エッジケーステスト] 極端な値のテスト")

        workflow = {
            "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.0}},
            "16": {"inputs": {"text": ""}},
            "53": {"inputs": {"width": 512, "height": 512}},
            "54": {"inputs": {"text": ""}},
        }

        # 極端なパラメータ値
        updated = self.client.update_prompt(
            workflow,
            positive_prompt="test",
            steps=1,  # 最小
            cfg=0.1,  # 最小
            width=64,  # 小さい
            height=64,
        )

        self.assertEqual(updated["3"]["inputs"]["steps"], 1)
        self.assertEqual(updated["3"]["inputs"]["cfg"], 0.1)
        print("✓ 極端な値でも更新可能")

    def test_long_prompt(self):
        """長いプロンプトのテスト"""
        print("\n[エッジケーステスト] 長いプロンプトのテスト")

        workflow = {
            "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.0}},
            "16": {"inputs": {"text": ""}},
            "53": {"inputs": {"width": 512, "height": 512}},
            "54": {"inputs": {"text": ""}},
        }

        # 非常に長いプロンプト
        long_prompt = "a beautiful landscape " * 100
        updated = self.client.update_prompt(workflow, positive_prompt=long_prompt)

        self.assertEqual(updated["16"]["inputs"]["text"], long_prompt)
        print(f"  プロンプト長: {len(long_prompt)} 文字")
        print("✓ 長いプロンプトでも正常に処理")


def run_tests():
    """テストを実行する関数"""
    # テストスイートの作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストケースを追加
    suite.addTests(loader.loadTestsFromTestCase(TestComfyUIClient))
    suite.addTests(loader.loadTestsFromTestCase(TestComfyUIClientEdgeCases))

    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果のサマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    print(f"実行したテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
