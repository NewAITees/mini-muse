#!/usr/bin/env python3
"""
ComfyUI APIを使用して簡単な画像を生成するテストスクリプト
UI形式のワークフローをAPI形式に変換して使用します
"""

import json
import requests
import time
from datetime import datetime

def convert_workflow_to_api_format(workflow):
    """
    UI形式のワークフローをAPI形式に変換
    """
    api_workflow = {}

    # linksをマッピングに変換
    links_map = {}
    if "links" in workflow:
        for link in workflow["links"]:
            # link = [link_id, source_node_id, source_slot, target_node_id, target_slot, type]
            if len(link) >= 6:
                link_id = link[0]
                links_map[link_id] = {
                    "source_node": str(link[1]),
                    "source_slot": link[2],
                    "target_node": str(link[3]),
                    "target_slot": link[4]
                }

    # 各ノードをAPI形式に変換
    for node in workflow["nodes"]:
        node_id = str(node["id"])
        node_type = node["type"]

        # Noteノードはスキップ
        if node_type == "Note":
            continue

        api_node = {
            "inputs": {},
            "class_type": node_type
        }

        # inputsからリンク情報を取得
        if "inputs" in node:
            for idx, input_item in enumerate(node["inputs"]):
                input_name = input_item.get("name", "")
                if "link" in input_item and input_item["link"] is not None:
                    link_id = input_item["link"]
                    if link_id in links_map:
                        source_info = links_map[link_id]
                        api_node["inputs"][input_name] = [
                            source_info["source_node"],
                            source_info["source_slot"]
                        ]

        # widget_valuesを設定
        if "widgets_values" in node:
            # ノードタイプごとに適切なinputsにマッピング
            if node_type == "CLIPTextEncode" and node["widgets_values"]:
                api_node["inputs"]["text"] = node["widgets_values"][0]
            elif node_type == "KSampler" and len(node["widgets_values"]) >= 7:
                api_node["inputs"]["seed"] = node["widgets_values"][0]
                api_node["inputs"]["control_after_generate"] = node["widgets_values"][1]
                api_node["inputs"]["steps"] = node["widgets_values"][2]
                api_node["inputs"]["cfg"] = node["widgets_values"][3]
                api_node["inputs"]["sampler_name"] = node["widgets_values"][4]
                api_node["inputs"]["scheduler"] = node["widgets_values"][5]
                api_node["inputs"]["denoise"] = node["widgets_values"][6]
            elif node_type == "EmptySD3LatentImage" and len(node["widgets_values"]) >= 3:
                api_node["inputs"]["width"] = node["widgets_values"][0]
                api_node["inputs"]["height"] = node["widgets_values"][1]
                api_node["inputs"]["batch_size"] = node["widgets_values"][2]
            elif node_type == "CheckpointLoaderSimple" and node["widgets_values"]:
                api_node["inputs"]["ckpt_name"] = node["widgets_values"][0]
            elif node_type == "DualCLIPLoader" and len(node["widgets_values"]) >= 4:
                api_node["inputs"]["clip_name1"] = node["widgets_values"][0]
                api_node["inputs"]["clip_name2"] = node["widgets_values"][1]
                api_node["inputs"]["type"] = node["widgets_values"][2]
            elif node_type == "CLIPLoader" and len(node["widgets_values"]) >= 2:
                api_node["inputs"]["clip_name"] = node["widgets_values"][0]
                api_node["inputs"]["type"] = node["widgets_values"][1]
            elif node_type == "SaveImage" and node["widgets_values"]:
                api_node["inputs"]["filename_prefix"] = node["widgets_values"][0]

        api_workflow[node_id] = api_node

    return api_workflow

def main():
    print("="*70)
    print("ComfyUI 簡易画像生成テスト")
    print("="*70)

    # ワークフローを読み込み
    print("\n[1] ワークフローを読み込み中...")
    with open("workflows/sd3.5_large_turbo_upscale.json", "r", encoding="utf-8") as f:
        ui_workflow = json.load(f)

    # API形式に変換
    print("\n[2] ワークフローをAPI形式に変換中...")
    api_workflow = convert_workflow_to_api_format(ui_workflow)

    # プロンプトを更新
    print("\n[3] プロンプトを更新中...")
    positive_prompt = "a beautiful sunset over mountains, highly detailed, 8k, masterpiece"
    negative_prompt = "blurry, low quality, distorted, ugly"

    if "16" in api_workflow:
        api_workflow["16"]["inputs"]["text"] = positive_prompt
        print(f"  ポジティブプロンプト設定: {positive_prompt[:50]}...")

    if "54" in api_workflow:
        api_workflow["54"]["inputs"]["text"] = negative_prompt
        print(f"  ネガティブプロンプト設定: {negative_prompt[:50]}...")

    # シードを設定
    if "3" in api_workflow:
        api_workflow["3"]["inputs"]["seed"] = 42
        print("  シード設定: 42")

    # API リクエストを送信
    print("\n[4] ComfyUI APIにリクエストを送信中...")
    url = "http://127.0.0.1:8000/prompt"
    payload = {"prompt": api_workflow}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        prompt_id = result.get("prompt_id")
        print(f"  ✓ プロンプトID: {prompt_id}")

        # 完了を待機
        print("\n[5] 画像生成を待機中...")
        print("  これには数十秒かかる場合があります...")

        max_wait = 300  # 5分
        start_time = time.time()

        while time.time() - start_time < max_wait:
            history_response = requests.get(f"http://127.0.0.1:8000/history/{prompt_id}")
            if history_response.status_code == 200:
                history = history_response.json()
                if prompt_id in history:
                    print("\n  ✓ 画像生成完了！")

                    # 画像情報を取得
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            for image_info in node_output["images"]:
                                filename = image_info["filename"]
                                print(f"\n[6] 画像を保存中...")
                                print(f"  ファイル名: {filename}")

                                # 画像をダウンロード
                                image_url = f"http://127.0.0.1:8000/view?filename={filename}&type=output"
                                image_response = requests.get(image_url)

                                if image_response.status_code == 200:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    output_path = f"stablediffusion/outputs/test_{timestamp}.png"

                                    with open(output_path, "wb") as f:
                                        f.write(image_response.content)

                                    print(f"\n{'='*70}")
                                    print("✓ 画像生成成功！")
                                    print(f"{'='*70}")
                                    print(f"保存先: {output_path}")
                                    print(f"画像サイズ: {len(image_response.content)} bytes")
                                    print(f"{'='*70}")
                                    return True

            time.sleep(2)

        print("\n✗ タイムアウト: 画像生成が完了しませんでした")
        return False
    else:
        print(f"\n✗ エラー: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
