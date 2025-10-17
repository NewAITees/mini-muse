"""
プロンプト生成エンジン

このモジュールは、テンプレートベースのプロンプト生成機能を提供します。
新しいJSON形式のプロンプト要素とテンプレートを使用して、
多様な画像生成プロンプトを作成できます。

================================================================================
使い方 - PromptGenerator
================================================================================

## 概要

PromptGeneratorは、JSON形式のプロンプト要素とテンプレートを使用して、
画像生成AIのための詳細なプロンプトを自動生成するクラスです。

## 基本的な使い方

### 1. インポート

```python
from mini_muse.prompt_generator import PromptGenerator
```

### 2. インスタンスの作成

```python
# デフォルトパス（prompts/prompt_elements.json）を使用
generator = PromptGenerator()

# カスタムパスを指定
generator = PromptGenerator(elements_file="path/to/your/elements.json")
```

### 3. プロンプトの生成

```python
# 単一のプロンプトを生成
prompt = generator.generate_prompt("abstract_art")
print(prompt)

# 複数のプロンプトを生成
prompts = generator.generate_multiple_prompts("detailed_diorama", count=5)
for i, prompt in enumerate(prompts, 1):
    print(f"プロンプト {i}: {prompt}")
```

## 利用可能なテンプレート

1. **abstract_art** - 抽象芸術の生成
   - 抽象的な要素を組み合わせた芸術作品

2. **detailed_diorama** - 詳細なジオラマの生成
   - 詳細な要素を組み合わせたジオラマ作品

3. **imaginative_world** - 想像力豊かな世界の生成
   - 想像力と科学的精密さが融合した世界

4. **miniature_world** - ティルトシフトを使用したミニチュアワールド
   - ティルトシフト効果で表現された小人の世界観

## 高度な使い方

### テンプレート情報の取得

```python
# 利用可能なテンプレート一覧を取得
templates = generator.get_available_templates()
print(f"利用可能なテンプレート: {templates}")

# 特定のテンプレートの情報を取得
info = generator.get_template_info("abstract_art")
print(f"説明: {info['description']}")
print(f"日本語説明: {info['japanese_description']}")
```

### 要素情報の取得

```python
# 利用可能な要素カテゴリ一覧を取得
elements = generator.get_available_elements()
print(f"要素カテゴリ: {elements}")

# 特定の要素カテゴリの値を取得
frame_settings = generator.get_element_values("frame_settings")
print(f"フレーム設定の選択肢: {frame_settings}")
```

## 実践例

### 例1: 基本的なプロンプト生成

```python
from mini_muse.prompt_generator import PromptGenerator

# ジェネレーターを初期化
generator = PromptGenerator()

# abstract_artテンプレートでプロンプトを生成
prompt = generator.generate_prompt("abstract_art")
print(prompt)
```

### 例2: 複数のバリエーションを生成

```python
# 同じテンプレートで5個のプロンプトを生成
prompts = generator.generate_multiple_prompts("miniature_world", count=5)

# 生成したプロンプトをファイルに保存
with open("generated_prompts.txt", "w", encoding="utf-8") as f:
    for i, prompt in enumerate(prompts, 1):
        f.write(f"=== プロンプト {i} ===\n")
        f.write(prompt)
        f.write("\n\n")
```

### 例3: 全テンプレートで生成

```python
# すべてのテンプレートでプロンプトを生成
templates = generator.get_available_templates()

for template_name in templates:
    print(f"\n=== {template_name} ===")
    prompt = generator.generate_prompt(template_name)
    print(prompt[:200] + "...")  # 最初の200文字を表示
```

### 例4: ComfyUIとの連携

```python
import json
from mini_muse.prompt_generator import PromptGenerator

# プロンプトを生成
generator = PromptGenerator()
prompt = generator.generate_prompt("detailed_diorama")

# ComfyUIのワークフローJSONにプロンプトを埋め込む
with open("workflows/sd3.5_large_turbo_upscale.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)

# ポジティブプロンプトノードを探して更新
for node in workflow["nodes"]:
    if node.get("title") == "Positive Prompt":
        node["widgets_values"][0] = prompt
        break

# 更新したワークフローを保存
with open("workflows/updated_workflow.json", "w", encoding="utf-8") as f:
    json.dump(workflow, f, ensure_ascii=False, indent=2)
```

## データ構造

### JSONファイルの構造

```json
{
  "elements": {
    "カテゴリ名": {
      "description": "カテゴリの説明",
      "values": ["値1", "値2", "値3", ...]
    }
  },
  "templates": {
    "テンプレート名": {
      "description": "英語説明",
      "japanese_description": "日本語説明",
      "text": "テンプレート本文（{プレースホルダー}を含む）"
    }
  }
}
```

## エラーハンドリング

```python
from mini_muse.prompt_generator import PromptGenerator

generator = PromptGenerator()

try:
    # 存在しないテンプレート名を指定
    prompt = generator.generate_prompt("nonexistent_template")
except ValueError as e:
    print(f"エラー: {e}")
    # 利用可能なテンプレート一覧を表示
    templates = generator.get_available_templates()
    print(f"利用可能なテンプレート: {', '.join(templates)}")
```

## 注意事項

1. **JSONファイルのパス**
   - デフォルトでは `prompts/prompt_elements.json` を使用
   - カスタムパスを指定する場合は、絶対パスまたは正しい相対パスを指定

2. **ランダム性**
   - 各プレースホルダーはランダムに選択されるため、同じテンプレートでも
     毎回異なるプロンプトが生成されます

3. **文字数**
   - 生成されるプロンプトは通常900-1000文字程度
   - ComfyUIなどで使用する際は、モデルの最大トークン数に注意

## トラブルシューティング

### Q: ファイルが見つからないエラーが出る
A: JSONファイルのパスを確認してください。デフォルトでは
   `プロジェクトルート/prompts/prompt_elements.json` を参照します。

### Q: プレースホルダーが置換されない
A: JSONファイルの要素カテゴリ名とテンプレート内のプレースホルダー名が
   一致しているか確認してください。

### Q: 生成されたプロンプトが長すぎる
A: テンプレートを編集するか、生成後に必要な部分だけを抽出してください。

================================================================================
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional


def list_available_template_files() -> List[str]:
    """
    promptsフォルダ内の利用可能なテンプレートファイルを一覧表示します。

    Returns:
        List[str]: テンプレートファイル名のリスト
    """
    project_root = Path(__file__).parent.parent
    prompts_dir = project_root / "prompts"

    if not prompts_dir.exists():
        return []

    # .jsonファイルのみを取得
    json_files = sorted([f.name for f in prompts_dir.glob("*.json")])
    return json_files


class PromptGenerator:
    """
    プロンプト生成エンジン

    JSON形式のプロンプト要素とテンプレートを読み込み、
    ランダムな組み合わせでプロンプトを生成します。
    """

    def __init__(self, elements_file: Optional[str] = None):
        """
        プロンプト生成エンジンを初期化します。

        Args:
            elements_file: プロンプト要素のJSONファイルパス
                          Noneの場合はデフォルトパス（prompt_elements.json）を使用
                          ファイル名のみの場合はpromptsフォルダから検索
        """
        if elements_file is None:
            # デフォルトパス: prompts/prompt_elements.json
            project_root = Path(__file__).parent.parent
            elements_file = project_root / "prompts" / "prompt_elements.json"
        else:
            # ファイル名のみの場合はpromptsフォルダから検索
            elements_path = Path(elements_file)
            if not elements_path.is_absolute() and elements_path.parent == Path('.'):
                project_root = Path(__file__).parent.parent
                elements_file = project_root / "prompts" / elements_file

        self.elements_file = Path(elements_file)
        self.elements: Dict = {}
        self.templates: Dict = {}

        self._load_elements()
        print(f"PromptGeneratorの初期化が完了しました。")
        print(f"読み込んだファイル: {self.elements_file.name}")
        print(f"要素カテゴリ数: {len(self.elements)}")
        print(f"テンプレート数: {len(self.templates)}")

    def _load_elements(self):
        """JSONファイルから要素とテンプレートを読み込みます。"""
        try:
            with open(self.elements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.elements = data.get("elements", {})
            self.templates = data.get("templates", {})

            print(f"要素を読み込みました: {self.elements_file}")
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {self.elements_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"エラー: JSONの解析に失敗しました: {e}")
            raise

    def generate_prompt(self, template_name: Optional[str] = None) -> str:
        """
        指定されたテンプレートに基づいてプロンプトを生成します。

        Args:
            template_name: 使用するテンプレート名
                          Noneの場合は利用可能なテンプレートからランダムに選択

        Returns:
            str: 生成されたプロンプト

        Raises:
            ValueError: 指定されたテンプレートが存在しない場合、またはテンプレートがない場合
        """
        # テンプレートがない場合はエラー
        if not self.templates:
            raise ValueError("利用可能なテンプレートがありません。")

        # template_nameが指定されていない場合はランダムに選択
        if template_name is None:
            template_name = random.choice(list(self.templates.keys()))
            print(f"テンプレートをランダムに選択: '{template_name}'")

        if template_name not in self.templates:
            available = ", ".join(self.templates.keys())
            raise ValueError(
                f"テンプレート '{template_name}' が見つかりません。"
                f"利用可能なテンプレート: {available}"
            )

        template = self.templates[template_name]["text"]
        print(f"テンプレート '{template_name}' を使用してプロンプトを生成します。")

        # テンプレート内のプレースホルダーを検出
        placeholders = re.findall(r'\{(\w+)\}', template)
        print(f"検出されたプレースホルダー: {set(placeholders)}")

        # プレースホルダーごとに選択された値を保存する辞書
        placeholder_values = {}

        # ベース名ごとに既に選択された値を追跡（重複を避けるため）
        used_values_by_base = {}

        # 各ユニークなプレースホルダーに対して値を選択
        for placeholder in set(placeholders):
            # プレースホルダーのベース名を取得 (例: color_1 -> color, texture_2 -> texture)
            base_name = re.sub(r'_\d+$', '', placeholder)

            # ベース名が要素に存在するか確認
            if base_name in self.elements:
                values = self.elements[base_name]["values"]

                # このベース名で既に使用された値を取得
                if base_name not in used_values_by_base:
                    used_values_by_base[base_name] = []

                # 未使用の値からランダムに選択
                available_values = [v for v in values if v not in used_values_by_base[base_name]]

                # すべて使用済みの場合は、全体からランダムに選択
                if not available_values:
                    available_values = values
                    used_values_by_base[base_name] = []  # リセット

                selected_value = random.choice(available_values)
                used_values_by_base[base_name].append(selected_value)
                placeholder_values[placeholder] = selected_value
                print(f"  {placeholder} ({base_name}) -> {selected_value}")

            # プレースホルダー名そのままが要素に存在するか確認
            elif placeholder in self.elements:
                values = self.elements[placeholder]["values"]
                selected_value = random.choice(values)
                placeholder_values[placeholder] = selected_value
                print(f"  {placeholder} -> {selected_value}")
            else:
                print(f"警告: 要素 '{placeholder}' (ベース名: '{base_name}') が見つかりません。")
                placeholder_values[placeholder] = f"[{placeholder}]"

        # すべてのプレースホルダーを置換
        filled_template = template
        for placeholder, value in placeholder_values.items():
            filled_template = filled_template.replace(f"{{{placeholder}}}", value)

        print(f"生成されたプロンプト長: {len(filled_template)} 文字")
        return filled_template

    def get_available_templates(self) -> List[str]:
        """
        利用可能なテンプレート名のリストを取得します。

        Returns:
            List[str]: テンプレート名のリスト
        """
        return list(self.templates.keys())

    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """
        指定されたテンプレートの情報を取得します。

        Args:
            template_name: テンプレート名

        Returns:
            Optional[Dict]: テンプレート情報、存在しない場合はNone
        """
        return self.templates.get(template_name)

    def get_available_elements(self) -> List[str]:
        """
        利用可能な要素カテゴリ名のリストを取得します。

        Returns:
            List[str]: 要素カテゴリ名のリスト
        """
        return list(self.elements.keys())

    def get_element_values(self, element_name: str) -> Optional[List[str]]:
        """
        指定された要素カテゴリの値リストを取得します。

        Args:
            element_name: 要素カテゴリ名

        Returns:
            Optional[List[str]]: 値のリスト、存在しない場合はNone
        """
        if element_name in self.elements:
            return self.elements[element_name]["values"]
        return None

    def generate_multiple_prompts(
        self,
        template_name: Optional[str] = None,
        count: int = 5
    ) -> List[str]:
        """
        複数のプロンプトを生成します。

        Args:
            template_name: 使用するテンプレート名
                          Noneの場合は毎回ランダムにテンプレートを選択
            count: 生成するプロンプトの数

        Returns:
            List[str]: 生成されたプロンプトのリスト
        """
        if template_name is None:
            print(f"{count}個のプロンプトを生成します（テンプレート: 毎回ランダム選択）")
        else:
            print(f"{count}個のプロンプトを生成します（テンプレート: {template_name}）")

        prompts = []
        for i in range(count):
            prompt = self.generate_prompt(template_name)
            prompts.append(prompt)
            print(f"  [{i+1}/{count}] 生成完了")
        return prompts


# 旧式のPromptGeneratorクラス（互換性のため保持）
class LegacyPromptGenerator:
    """
    旧形式のプロンプト生成エンジン（互換性維持用）

    注意: このクラスは旧システムとの互換性のためのみ提供されています。
    新規開発では PromptGenerator クラスを使用してください。
    """

    def __init__(self, app=None):
        """
        プロンプト生成エンジンを初期化し、JSONデータストアからデータを読み込みます。

        注意: この実装は data_store に依存しますが、現在は利用できません。
        """
        print("警告: LegacyPromptGenerator は非推奨です。PromptGenerator を使用してください。")
        # 旧実装のコードは省略（data_store が利用できないため）
        pass

    def generate_prompt(self, tag_names: List[str]) -> Optional[str]:
        """
        指定された複数のタグに基づいてプロンプトを生成します（旧形式）。

        Args:
            tag_names: プロンプト生成に使用するタグ名のリスト

        Returns:
            Optional[str]: 生成されたプロンプト
        """
        print("警告: この機能は現在利用できません。新しい PromptGenerator を使用してください。")
        return None
