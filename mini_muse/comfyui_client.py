"""
ComfyUI APIクライアント

このモジュールは、ComfyUI サーバーとの通信を行うクライアントクラスを提供します。
ワークフローの読み込み、プロンプトの更新、画像生成を簡単に実行できます。

================================================================================
使い方 - ComfyUIClient
================================================================================

## 概要

ComfyUIClientは、ComfyUI サーバーとHTTP/WebSocket通信を行い、
画像生成ワークフローを実行するためのクライアントクラスです。

## 前提条件

1. **ComfyUIサーバーの起動**
   ComfyUIサーバーが起動している必要があります。
   デフォルトでは `127.0.0.1:8188` で起動します。

2. **必要なPythonパッケージ**
   ```bash
   pip install requests websocket-client
   ```

## 基本的な使い方

### 1. インポート

```python
from mini_muse.comfyui_client import ComfyUIClient
```

### 2. クライアントの初期化

```python
# デフォルト（127.0.0.1:8188）に接続
client = ComfyUIClient()

# カスタムアドレスに接続
client = ComfyUIClient("192.168.1.100:8188")
```

### 3. ワークフローの読み込み

```python
# ワークフローJSONファイルを読み込み
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")
```

### 4. 画像生成

```python
# 単一の画像を生成
image_data = client.generate_image(
    workflow,
    positive_prompt="a beautiful landscape with mountains",
    negative_prompt="blurry, low quality",
    seed=12345,
    steps=30,
    cfg=5.45,
    width=1024,
    height=1024,
    save_path="output.png"
)
```

## 実践例

### 例1: 基本的な画像生成

```python
from mini_muse.comfyui_client import ComfyUIClient

# クライアント初期化
client = ComfyUIClient()

# ワークフロー読み込み
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

# 画像生成
client.generate_image(
    workflow,
    positive_prompt="a cute cat sitting on a windowsill",
    negative_prompt="blurry, low quality",
    save_path="stablediffusion/outputs/cat.png"
)
print("画像生成完了！")
```

### 例2: 複数のプロンプトで画像生成

```python
from mini_muse.comfyui_client import ComfyUIClient

client = ComfyUIClient()
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

prompts = [
    "a futuristic cityscape at night",
    "a serene forest with morning mist",
    "a steampunk mechanical robot"
]

for i, prompt in enumerate(prompts):
    print(f"Generating image {i+1}/{len(prompts)}: {prompt}")
    client.generate_image(
        workflow,
        positive_prompt=prompt,
        negative_prompt="blurry, low quality, distorted",
        seed=None,  # ランダムシード
        save_path=f"stablediffusion/outputs/image_{i:03d}.png"
    )
    print(f"  ✓ 完了")

print("全ての画像生成が完了しました！")
```

### 例3: PromptGeneratorと連携

```python
from mini_muse.comfyui_client import ComfyUIClient
from mini_muse.prompt_generator import PromptGenerator

# 初期化
client = ComfyUIClient()
prompt_gen = PromptGenerator()

# ワークフロー読み込み
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

# プロンプト自動生成 + 画像生成
for i in range(5):
    # ランダムなプロンプトを生成
    prompt = prompt_gen.generate_prompt("abstract_art")
    print(f"\n=== 画像 {i+1}/5 ===")
    print(f"プロンプト: {prompt[:100]}...")

    # 画像生成
    client.generate_image(
        workflow,
        positive_prompt=prompt,
        negative_prompt="low quality, blurry",
        save_path=f"stablediffusion/outputs/generated_{i:03d}.png"
    )
    print("✓ 生成完了")
```

### 例4: パラメータを変えて複数生成

```python
from mini_muse.comfyui_client import ComfyUIClient

client = ComfyUIClient()
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

prompt = "a magical crystal cave with glowing minerals"

# 異なるCFG値でテスト
cfg_values = [3.0, 5.45, 7.5, 10.0]

for cfg in cfg_values:
    print(f"Generating with CFG={cfg}")
    client.generate_image(
        workflow,
        positive_prompt=prompt,
        negative_prompt="blurry, low quality",
        cfg=cfg,
        save_path=f"stablediffusion/outputs/cfg_{cfg:.1f}.png"
    )
```

### 例5: 異なる解像度で生成

```python
from mini_muse.comfyui_client import ComfyUIClient

client = ComfyUIClient()
workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

prompt = "a cyberpunk street scene at night"

resolutions = [
    (512, 512, "square_small"),
    (1024, 1024, "square_large"),
    (1024, 768, "landscape"),
    (768, 1024, "portrait")
]

for width, height, name in resolutions:
    print(f"Generating {name} ({width}x{height})")
    client.generate_image(
        workflow,
        positive_prompt=prompt,
        negative_prompt="blurry, low quality",
        width=width,
        height=height,
        save_path=f"stablediffusion/outputs/{name}.png"
    )
```

## メソッド詳細

### load_workflow(workflow_path: str) -> Dict

ワークフローJSONファイルを読み込みます。

**引数:**
- `workflow_path`: ワークフローJSONファイルのパス

**戻り値:**
- ワークフロー辞書

### queue_prompt(workflow: Dict) -> str

プロンプトをキューに追加して実行を開始します。

**引数:**
- `workflow`: ワークフロー辞書

**戻り値:**
- プロンプトID（実行の追跡に使用）

### wait_for_completion(prompt_id: str, timeout: int = 300) -> Dict

実行完了を待機します（ポーリング方式）。

**引数:**
- `prompt_id`: プロンプトID
- `timeout`: タイムアウト時間（秒）

**戻り値:**
- 実行結果の辞書

### generate_image(...) -> bytes

画像を生成して取得します。

**引数:**
- `workflow`: ワークフロー辞書
- `positive_prompt`: ポジティブプロンプト
- `negative_prompt`: ネガティブプロンプト（デフォルト: ""）
- `seed`: シード値（Noneでランダム）
- `steps`: サンプリングステップ数（デフォルト: 30）
- `cfg`: CFGスケール（デフォルト: 5.45）
- `width`: 画像の幅（デフォルト: 1024）
- `height`: 画像の高さ（デフォルト: 1024）
- `save_path`: 保存先パス（Noneで保存しない）

**戻り値:**
- 画像データ（bytes）

## ワークフロー構造の理解

ComfyUIのワークフローは、ノードIDで管理されています。
デフォルトの `sd3.5_large_turbo_upscale.json` では：

- **ノード3**: KSampler（サンプリング設定）
  - `seed`: シード値
  - `steps`: ステップ数
  - `cfg`: CFGスケール

- **ノード16**: CLIPTextEncode（ポジティブプロンプト）
  - `text`: プロンプトテキスト

- **ノード53**: EmptySD3LatentImage（画像サイズ）
  - `width`: 幅
  - `height`: 高さ

- **ノード54**: CLIPTextEncode（ネガティブプロンプト）
  - `text`: ネガティブプロンプトテキスト

## エラーハンドリング

```python
from mini_muse.comfyui_client import ComfyUIClient
import requests.exceptions

client = ComfyUIClient()

try:
    workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")
    image_data = client.generate_image(
        workflow,
        positive_prompt="a beautiful landscape",
        save_path="output.png"
    )
except FileNotFoundError:
    print("エラー: ワークフローファイルが見つかりません")
except requests.exceptions.ConnectionError:
    print("エラー: ComfyUIサーバーに接続できません")
    print("ComfyUIが起動しているか確認してください")
except TimeoutError as e:
    print(f"エラー: タイムアウト - {e}")
except Exception as e:
    print(f"エラー: {e}")
```

## 注意事項

1. **ComfyUIサーバーの起動**
   - このクライアントを使用する前に、ComfyUIサーバーが起動している必要があります

2. **ワークフロー形式**
   - ComfyUIで保存したワークフローJSON（APIフォーマット）を使用してください

3. **ノードID**
   - ワークフローのノードIDは固定されていません
   - 異なるワークフローを使用する場合は、`update_prompt`メソッドを修正してください

4. **タイムアウト**
   - 大きな画像や複雑なワークフローは時間がかかります
   - 必要に応じて`timeout`パラメータを調整してください

## トラブルシューティング

### Q: 接続エラーが発生する
A: 以下を確認してください：
   1. ComfyUIサーバーが起動しているか
   2. サーバーアドレスが正しいか（デフォルト: 127.0.0.1:8188）
   3. ファイアウォールで通信がブロックされていないか

### Q: 画像が生成されない
A: 以下を確認してください：
   1. ワークフローJSONファイルが正しいか
   2. モデルファイルがComfyUIに配置されているか
   3. ComfyUIのコンソールにエラーが出ていないか

### Q: タイムアウトエラーが出る
A: `wait_for_completion`の`timeout`パラメータを増やしてください：
   ```python
   result = client.wait_for_completion(prompt_id, timeout=600)  # 10分
   ```

### Q: 生成された画像の品質が悪い
A: 以下のパラメータを調整してください：
   - `steps`: 増やすと品質向上（20-50推奨）
   - `cfg`: 7.0-10.0程度が一般的
   - プロンプトをより詳細に記述

================================================================================
"""

import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import websocket


class ComfyUIClient:
    """ComfyUI APIクライアント"""

    def __init__(self, server_address: str = "127.0.0.1:8188"):
        """
        ComfyUIクライアントを初期化します。

        Args:
            server_address: ComfyUIサーバーのアドレス（デフォルト: 127.0.0.1:8188）
        """
        self.server_address = server_address
        self.base_url = f"http://{server_address}"
        self.ws_url = f"ws://{server_address}/ws"
        print(f"ComfyUIクライアント初期化: {self.base_url}")

    def load_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """
        ワークフローJSONファイルを読み込みます。

        Args:
            workflow_path: ワークフローJSONファイルのパス

        Returns:
            Dict[str, Any]: ワークフロー辞書

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            json.JSONDecodeError: JSON解析エラーの場合
        """
        workflow_path = Path(workflow_path)
        if not workflow_path.exists():
            raise FileNotFoundError(f"ワークフローファイルが見つかりません: {workflow_path}")

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        print(f"ワークフローを読み込みました: {workflow_path}")
        return workflow

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        プロンプトをキューに追加して実行を開始します。

        Args:
            workflow: ワークフロー辞書

        Returns:
            str: プロンプトID

        Raises:
            requests.exceptions.ConnectionError: サーバーに接続できない場合
        """
        payload = {"prompt": workflow}
        response = requests.post(f"{self.base_url}/prompt", json=payload)
        response.raise_for_status()
        return response.json()["prompt_id"]

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        実行履歴を取得します。

        Args:
            prompt_id: プロンプトID

        Returns:
            Dict[str, Any]: 履歴辞書
        """
        response = requests.get(f"{self.base_url}/history/{prompt_id}")
        response.raise_for_status()
        return response.json()

    def get_image(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes:
        """
        生成された画像を取得します。

        Args:
            filename: ファイル名
            subfolder: サブフォルダ
            folder_type: フォルダタイプ（デフォルト: output）

        Returns:
            bytes: 画像データ
        """
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        response = requests.get(f"{self.base_url}/view", params=params)
        response.raise_for_status()
        return response.content

    def wait_for_completion(
        self, prompt_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """
        実行完了を待機します（ポーリング方式）。

        Args:
            prompt_id: プロンプトID
            timeout: タイムアウト時間（秒）

        Returns:
            Dict[str, Any]: 実行結果

        Raises:
            TimeoutError: タイムアウトした場合
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(1)
        raise TimeoutError(
            f"プロンプト {prompt_id} が {timeout} 秒以内に完了しませんでした"
        )

    def update_prompt(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        steps: int = 30,
        cfg: float = 5.45,
        width: int = 1024,
        height: int = 1024,
    ) -> Dict[str, Any]:
        """
        ワークフローのパラメータを更新します（API形式のワークフロー用）。

        Args:
            workflow: ワークフロー辞書（API形式）
            positive_prompt: ポジティブプロンプト
            negative_prompt: ネガティブプロンプト
            seed: シード値（Noneでランダム）
            steps: サンプリングステップ数
            cfg: CFGスケール
            width: 画像の幅
            height: 画像の高さ

        Returns:
            Dict[str, Any]: 更新されたワークフロー
        """
        # プロンプトの更新
        if "16" in workflow:
            workflow["16"]["inputs"]["text"] = positive_prompt  # Positive Prompt
        if "54" in workflow:
            workflow["54"]["inputs"]["text"] = negative_prompt  # Negative Prompt

        # サンプリング設定の更新
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        if "3" in workflow:
            workflow["3"]["inputs"]["seed"] = seed
            workflow["3"]["inputs"]["steps"] = steps
            workflow["3"]["inputs"]["cfg"] = cfg

        # 画像サイズの更新
        if "53" in workflow:
            workflow["53"]["inputs"]["width"] = width
            workflow["53"]["inputs"]["height"] = height

        return workflow

    def generate_image(
        self,
        workflow: Dict[str, Any],
        positive_prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        steps: int = 30,
        cfg: float = 5.45,
        width: int = 1024,
        height: int = 1024,
        save_path: Optional[str] = None,
    ) -> bytes:
        """
        画像を生成して取得します。

        Args:
            workflow: ワークフロー辞書
            positive_prompt: ポジティブプロンプト
            negative_prompt: ネガティブプロンプト
            seed: シード値（Noneでランダム）
            steps: サンプリングステップ数
            cfg: CFGスケール
            width: 画像の幅
            height: 画像の高さ
            save_path: 保存先パス（Noneで保存しない）

        Returns:
            bytes: 画像データ

        Raises:
            Exception: 画像が見つからない場合
        """
        # ワークフローを更新
        updated_workflow = self.update_prompt(
            workflow.copy(),
            positive_prompt,
            negative_prompt,
            seed,
            steps,
            cfg,
            width,
            height,
        )

        # 実行をキューに追加
        prompt_id = self.queue_prompt(updated_workflow)
        print(f"プロンプトをキューに追加: {prompt_id}")

        # 完了を待機
        result = self.wait_for_completion(prompt_id)
        print(f"生成完了: {prompt_id}")

        # 画像を取得
        outputs = result["outputs"]
        for node_id in outputs:
            if "images" in outputs[node_id]:
                for image_info in outputs[node_id]["images"]:
                    image_data = self.get_image(
                        image_info["filename"],
                        image_info.get("subfolder", ""),
                        image_info.get("type", "output"),
                    )

                    # 保存（オプション）
                    if save_path:
                        save_path = Path(save_path)
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(image_data)
                        print(f"画像を保存しました: {save_path}")

                    return image_data

        raise Exception("出力に画像が見つかりませんでした")


# 使用例
if __name__ == "__main__":
    # クライアント初期化
    client = ComfyUIClient("127.0.0.1:8188")

    # ワークフローを読み込み
    workflow = client.load_workflow("workflows/sd3.5_large_turbo_upscale.json")

    # 単一画像生成
    print("単一画像を生成中...")
    client.generate_image(
        workflow,
        positive_prompt="a beautiful landscape with mountains and a lake at sunset",
        negative_prompt="blurry, low quality",
        seed=12345,
        steps=30,
        cfg=5.45,
        save_path="stablediffusion/outputs/output_single.png",
    )

    # 複数画像生成（異なるプロンプト）
    print("\n複数画像を生成中...")
    prompts = [
        "a cute cat sitting on a windowsill",
        "a futuristic cityscape at night",
        "a serene forest with morning mist",
    ]

    for i, prompt in enumerate(prompts):
        client.generate_image(
            workflow,
            positive_prompt=prompt,
            negative_prompt="blurry, low quality, distorted",
            seed=None,  # ランダムシード
            steps=30,
            cfg=5.45,
            save_path=f"stablediffusion/outputs/output_{i:03d}.png",
        )
        print(f"画像 {i+1}/{len(prompts)} 完了")

    print("\n全ての画像生成が完了しました！")
