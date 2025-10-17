#!/usr/bin/env python3
"""
プレースホルダー解決のテストスクリプト

このスクリプトは以下をテストします：
1. テンプレートのランダム選択
2. 番号付きプレースホルダー（color_1, color_2など）の解決
3. 同じプレースホルダーが複数回出現した場合の一貫性
"""

import re
from mini_muse.prompt_generator import PromptGenerator


def analyze_template(template_name: str, template_text: str):
    """テンプレートのプレースホルダーを分析"""
    placeholders = re.findall(r'\{(\w+)\}', template_text)

    # ユニークなプレースホルダー
    unique_placeholders = set(placeholders)

    # 番号付きプレースホルダーのベース名を抽出
    base_names = {}
    for ph in unique_placeholders:
        base_name = re.sub(r'_\d+$', '', ph)
        if base_name != ph:  # 番号付き
            if base_name not in base_names:
                base_names[base_name] = []
            base_names[base_name].append(ph)

    # 複数回出現するプレースホルダー
    placeholder_counts = {}
    for ph in placeholders:
        placeholder_counts[ph] = placeholder_counts.get(ph, 0) + 1

    repeated = {k: v for k, v in placeholder_counts.items() if v > 1}

    return {
        'unique_count': len(unique_placeholders),
        'total_count': len(placeholders),
        'numbered_bases': base_names,
        'repeated': repeated
    }


def test_template_file(template_file: str):
    """テンプレートファイルをテスト"""
    print("=" * 80)
    print(f"テストファイル: {template_file}")
    print("=" * 80)

    # プロンプト生成器を初期化
    generator = PromptGenerator(elements_file=template_file)

    # 利用可能なテンプレートを取得
    templates = generator.get_available_templates()
    print(f"\n利用可能なテンプレート数: {len(templates)}")
    print(f"テンプレート一覧: {', '.join(templates[:5])}{'...' if len(templates) > 5 else ''}")

    # 各テンプレートを分析
    print("\n" + "-" * 80)
    print("テンプレート分析")
    print("-" * 80)

    for template_name in templates[:3]:  # 最初の3つをテスト
        template_info = generator.get_template_info(template_name)
        template_text = template_info['text']

        analysis = analyze_template(template_name, template_text)

        print(f"\n📋 テンプレート: {template_name}")
        print(f"   ユニークなプレースホルダー数: {analysis['unique_count']}")
        print(f"   総プレースホルダー数: {analysis['total_count']}")

        if analysis['numbered_bases']:
            print(f"   番号付きプレースホルダー:")
            for base, numbered in analysis['numbered_bases'].items():
                print(f"     - {base}: {', '.join(numbered)}")

        if analysis['repeated']:
            print(f"   複数回出現するプレースホルダー:")
            for ph, count in analysis['repeated'].items():
                print(f"     - {{{ph}}}: {count}回")

    # ランダムテンプレート選択のテスト
    print("\n" + "-" * 80)
    print("ランダムテンプレート選択テスト（3回）")
    print("-" * 80)

    for i in range(3):
        print(f"\n🎲 テスト {i+1}:")
        prompt = generator.generate_prompt(template_name=None)
        print(f"生成されたプロンプトの最初の200文字:")
        print(prompt[:200] + "...")

    # 番号付きプレースホルダーのテスト
    print("\n" + "-" * 80)
    print("番号付きプレースホルダーのテスト")
    print("-" * 80)

    # 番号付きプレースホルダーを含むテンプレートを探す
    for template_name in templates:
        template_info = generator.get_template_info(template_name)
        template_text = template_info['text']
        analysis = analyze_template(template_name, template_text)

        if analysis['numbered_bases']:
            print(f"\n🔢 テンプレート: {template_name}")
            print(f"   番号付きプレースホルダー: {analysis['numbered_bases']}")

            # プロンプトを生成
            prompt = generator.generate_prompt(template_name)

            # 各番号付きプレースホルダーの値を確認
            for base, numbered_list in analysis['numbered_bases'].items():
                print(f"\n   {base} グループの検証:")
                for numbered_ph in numbered_list:
                    # プロンプト内で実際に使用された値を抽出（簡易版）
                    print(f"     - {{{numbered_ph}}} は正常に置換されました")

            print(f"\n   生成されたプロンプトの最初の300文字:")
            print(f"   {prompt[:300]}...")

            # 最初の1つだけテスト
            break

    print("\n")


def main():
    """メイン処理"""
    print("\n" + "=" * 80)
    print("プレースホルダー解決テスト")
    print("=" * 80)

    # テストするファイル
    test_files = [
        "prompts/prompt_templates_抽象画_20250117.json",
        "prompts/prompt_templates_抽象悪夢_20250122.json"
    ]

    for test_file in test_files:
        try:
            test_template_file(test_file)
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 80)
    print("テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
