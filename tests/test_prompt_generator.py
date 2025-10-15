"""
PromptGeneratorのテストコード

このモジュールは、PromptGeneratorクラスの機能をテストします。

================================================================================
使い方 - test_prompt_generator.py
================================================================================

## 概要

このテストファイルは、PromptGeneratorクラスの全機能をテストし、
正常に動作することを確認します。

## テスト実行方法

### 方法1: 直接実行

```bash
# プロジェクトルートから実行
uv run python tests/test_prompt_generator.py
```

### 方法2: pytestを使用

```bash
# pytestがインストールされている場合
uv run pytest tests/test_prompt_generator.py -v
```

### 方法3: unittestモジュールを使用

```bash
# Pythonの標準unittestモジュールを使用
uv run python -m unittest tests.test_prompt_generator
```

## テスト内容

このテストファイルには、以下のテストケースが含まれています：

### 基本機能のテスト (TestPromptGenerator)

1. **test_01_initialization** - 初期化のテスト
   - PromptGeneratorが正常に初期化されることを確認

2. **test_02_elements_loaded** - 要素の読み込みテスト
   - JSONファイルから要素が正しく読み込まれることを確認

3. **test_03_templates_loaded** - テンプレートの読み込みテスト
   - JSONファイルからテンプレートが正しく読み込まれることを確認

4. **test_04_abstract_art_generation** - abstract_artテンプレートのテスト
   - abstract_artテンプレートでプロンプトが生成されることを確認

5. **test_05_detailed_diorama_generation** - detailed_dioramaテンプレートのテスト
   - detailed_dioramaテンプレートでプロンプトが生成されることを確認

6. **test_06_imaginative_world_generation** - imaginative_worldテンプレートのテスト
   - imaginative_worldテンプレートでプロンプトが生成されることを確認

7. **test_07_miniature_world_generation** - miniature_worldテンプレートのテスト
   - miniature_worldテンプレートでプロンプトが生成されることを確認

8. **test_08_invalid_template** - エラーハンドリングのテスト
   - 存在しないテンプレート名でValueErrorが発生することを確認

9. **test_09_multiple_prompts_generation** - 複数プロンプト生成のテスト
   - 複数のプロンプトが正しく生成されることを確認

10. **test_10_get_element_values** - 要素値取得のテスト
    - 要素カテゴリの値が正しく取得できることを確認

11. **test_11_get_template_info** - テンプレート情報取得のテスト
    - テンプレート情報が正しく取得できることを確認

12. **test_12_randomness_check** - ランダム性のテスト
    - 生成されるプロンプトに多様性があることを確認

### エッジケースのテスト (TestPromptGeneratorEdgeCases)

1. **test_all_templates** - 全テンプレートのテスト
   - すべてのテンプレートでプロンプト生成が成功することを確認

## テスト結果の見方

### 成功例

```
======================================================================
PromptGenerator テスト開始
======================================================================

[テスト1] 初期化のテスト
✓ 初期化成功

...（他のテスト結果）...

======================================================================
テスト結果サマリー
======================================================================
実行したテスト数: 13
成功: 13
失敗: 0
エラー: 0
======================================================================
```

### 失敗例

テストが失敗した場合、以下のような情報が表示されます：

```
FAIL: test_04_abstract_art_generation
----------------------------------------------------------------------
AssertionError: プレースホルダーが残っています
```

## カスタマイズ

### 特定のテストのみを実行

```python
# テストファイルを編集して、実行したいテストのみをコメントアウト解除
if __name__ == "__main__":
    # 特定のテストのみを実行
    suite = unittest.TestSuite()
    suite.addTest(TestPromptGenerator('test_04_abstract_art_generation'))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
```

### 新しいテストの追加

```python
def test_13_my_custom_test(self):
    \"\"\"カスタムテストの説明\"\"\"
    print("\\n[テスト13] カスタムテスト")
    # テストコードをここに記述
    self.assertTrue(True)
    print("✓ カスタムテスト成功")
```

## トラブルシューティング

### Q: テストが失敗する
A: 以下を確認してください：
   1. `prompts/prompt_elements.json` が存在するか
   2. JSONファイルの形式が正しいか
   3. 必要な要素とテンプレートが定義されているか

### Q: インポートエラーが発生する
A: プロジェクトルートから実行しているか確認してください。
   または、PYTHONPATHを設定してください：
   ```bash
   export PYTHONPATH=/home/perso/analysis/mini-muse:$PYTHONPATH
   uv run python tests/test_prompt_generator.py
   ```

### Q: 詳細なデバッグ情報が欲しい
A: verbosityを上げて実行してください：
   ```bash
   uv run python -m unittest tests.test_prompt_generator -v
   ```

## 継続的インテグレーション (CI)

このテストファイルは、CI/CDパイプラインに組み込むことができます：

```yaml
# .github/workflows/test.yml の例
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          uv run python tests/test_prompt_generator.py
```

================================================================================
"""

import unittest
from pathlib import Path
import sys

# mini_museモジュールをインポートパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mini_muse.prompt_generator import PromptGenerator


class TestPromptGenerator(unittest.TestCase):
    """PromptGeneratorクラスのテストケース"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体で1回だけ実行される初期化処理"""
        print("\n" + "="*70)
        print("PromptGenerator テスト開始")
        print("="*70)
        cls.generator = PromptGenerator()

    def test_01_initialization(self):
        """初期化のテスト"""
        print("\n[テスト1] 初期化のテスト")
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.elements)
        self.assertIsNotNone(self.generator.templates)
        print("✓ 初期化成功")

    def test_02_elements_loaded(self):
        """要素の読み込みテスト"""
        print("\n[テスト2] 要素の読み込みテスト")
        elements = self.generator.get_available_elements()
        self.assertGreater(len(elements), 0, "要素が読み込まれていません")
        print(f"✓ {len(elements)}個の要素カテゴリが読み込まれました")
        print(f"  要素カテゴリ: {', '.join(elements[:5])}...")

    def test_03_templates_loaded(self):
        """テンプレートの読み込みテスト"""
        print("\n[テスト3] テンプレートの読み込みテスト")
        templates = self.generator.get_available_templates()
        self.assertGreater(len(templates), 0, "テンプレートが読み込まれていません")
        print(f"✓ {len(templates)}個のテンプレートが読み込まれました")
        print(f"  テンプレート: {', '.join(templates)}")

    def test_04_abstract_art_generation(self):
        """abstract_artテンプレートでのプロンプト生成テスト"""
        print("\n[テスト4] abstract_art プロンプト生成テスト")
        prompt = self.generator.generate_prompt("abstract_art")
        self.assertIsNotNone(prompt)
        self.assertGreater(len(prompt), 0)
        self.assertNotIn("{", prompt, "プレースホルダーが残っています")
        self.assertNotIn("}", prompt, "プレースホルダーが残っています")
        print("✓ プロンプト生成成功")
        print(f"  生成されたプロンプト長: {len(prompt)} 文字")
        print(f"  プロンプトの一部: {prompt[:150]}...")

    def test_05_detailed_diorama_generation(self):
        """detailed_dioramaテンプレートでのプロンプト生成テスト"""
        print("\n[テスト5] detailed_diorama プロンプト生成テスト")
        prompt = self.generator.generate_prompt("detailed_diorama")
        self.assertIsNotNone(prompt)
        self.assertGreater(len(prompt), 0)
        self.assertNotIn("{", prompt, "プレースホルダーが残っています")
        print("✓ プロンプト生成成功")
        print(f"  生成されたプロンプト長: {len(prompt)} 文字")

    def test_06_imaginative_world_generation(self):
        """imaginative_worldテンプレートでのプロンプト生成テスト"""
        print("\n[テスト6] imaginative_world プロンプト生成テスト")
        prompt = self.generator.generate_prompt("imaginative_world")
        self.assertIsNotNone(prompt)
        self.assertGreater(len(prompt), 0)
        self.assertNotIn("{", prompt, "プレースホルダーが残っています")
        print("✓ プロンプト生成成功")
        print(f"  生成されたプロンプト長: {len(prompt)} 文字")

    def test_07_miniature_world_generation(self):
        """miniature_worldテンプレートでのプロンプト生成テスト"""
        print("\n[テスト7] miniature_world プロンプト生成テスト")
        prompt = self.generator.generate_prompt("miniature_world")
        self.assertIsNotNone(prompt)
        self.assertGreater(len(prompt), 0)
        self.assertNotIn("{", prompt, "プレースホルダーが残っています")
        print("✓ プロンプト生成成功")
        print(f"  生成されたプロンプト長: {len(prompt)} 文字")

    def test_08_invalid_template(self):
        """存在しないテンプレート名でのエラーテスト"""
        print("\n[テスト8] 無効なテンプレート名のテスト")
        with self.assertRaises(ValueError) as context:
            self.generator.generate_prompt("nonexistent_template")
        print("✓ 期待通りValueErrorが発生しました")
        print(f"  エラーメッセージ: {context.exception}")

    def test_09_multiple_prompts_generation(self):
        """複数プロンプトの生成テスト"""
        print("\n[テスト9] 複数プロンプト生成テスト")
        prompts = self.generator.generate_multiple_prompts("abstract_art", count=3)
        self.assertEqual(len(prompts), 3)
        for i, prompt in enumerate(prompts, 1):
            self.assertGreater(len(prompt), 0)
            self.assertNotIn("{", prompt)
            print(f"  プロンプト{i}: {len(prompt)} 文字")
        print("✓ 3個のプロンプト生成成功")

    def test_10_get_element_values(self):
        """要素値の取得テスト"""
        print("\n[テスト10] 要素値の取得テスト")
        values = self.generator.get_element_values("frame_settings")
        self.assertIsNotNone(values)
        self.assertIsInstance(values, list)
        self.assertGreater(len(values), 0)
        print(f"✓ frame_settingsの値: {len(values)}個")
        print(f"  例: {values[0]}")

    def test_11_get_template_info(self):
        """テンプレート情報の取得テスト"""
        print("\n[テスト11] テンプレート情報の取得テスト")
        info = self.generator.get_template_info("abstract_art")
        self.assertIsNotNone(info)
        self.assertIn("description", info)
        self.assertIn("japanese_description", info)
        self.assertIn("text", info)
        print(f"✓ テンプレート情報取得成功")
        print(f"  説明: {info['description']}")
        print(f"  日本語説明: {info['japanese_description']}")

    def test_12_randomness_check(self):
        """ランダム性の確認テスト"""
        print("\n[テスト12] ランダム性の確認テスト")
        prompts = self.generator.generate_multiple_prompts("abstract_art", count=5)
        unique_prompts = set(prompts)
        # 5個中少なくとも3個は異なるプロンプトが生成されることを期待
        self.assertGreaterEqual(len(unique_prompts), 3,
                               "生成されたプロンプトの多様性が不足しています")
        print(f"✓ 5個中{len(unique_prompts)}個のユニークなプロンプトが生成されました")

    @classmethod
    def tearDownClass(cls):
        """テストクラス全体で1回だけ実行される終了処理"""
        print("\n" + "="*70)
        print("PromptGenerator テスト完了")
        print("="*70 + "\n")


class TestPromptGeneratorEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.generator = PromptGenerator()

    def test_all_templates(self):
        """すべてのテンプレートでプロンプト生成が成功することを確認"""
        print("\n[エッジケーステスト] 全テンプレートのテスト")
        templates = self.generator.get_available_templates()
        for template_name in templates:
            with self.subTest(template=template_name):
                prompt = self.generator.generate_prompt(template_name)
                self.assertIsNotNone(prompt)
                self.assertGreater(len(prompt), 0)
                self.assertNotIn("{", prompt)
                print(f"  ✓ {template_name}: OK")


def run_tests():
    """テストを実行する関数"""
    # テストスイートの作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストケースを追加
    suite.addTests(loader.loadTestsFromTestCase(TestPromptGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptGeneratorEdgeCases))

    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果のサマリー
    print("\n" + "="*70)
    print("テスト結果サマリー")
    print("="*70)
    print(f"実行したテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
