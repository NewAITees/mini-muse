"""
ComfyUI パイプライン実行モジュール

このモジュールは、ComfyUI APIを使用して画像→動画生成のワークフローを実行します。
プレースホルダ方式でワークフローJSONを差し替え、柔軟な運用を可能にします。

================================================================================
使い方 - comfy_runner
================================================================================

## 概要

ComfyUI APIを使用して、以下の処理を自動化します：
1. 画像のアップロード
2. ワークフローJSONのプレースホルダ差し替え
3. ワークフローの投入
4. 完了待機（履歴ポーリング）
5. 出力ファイルのダウンロード

## 前提条件

1. **ComfyUIサーバーの起動**
   ComfyUIサーバーが起動している必要があります。
   デフォルトでは `http://127.0.0.1:8188` で起動します。

2. **ワークフローJSON**
   ComfyUIでエクスポートしたワークフローJSONに、以下のプレースホルダを配置：
   - 画像ファイル名: `###IMAGE_FILENAME###`
   - プロンプトテキスト: `###PROMPT###`

3. **必要なPythonパッケージ**
   ```bash
   pip install requests
   ```

## 基本的な使い方

### 1. インポート

```python
from mini_muse.comfy_runner import run_comfy_pipeline
```

### 2. ワンショット実行

```python
# 画像→プロンプト→動画生成を一括実行
output_files = run_comfy_pipeline(
    image_path="input/sample.jpg",
    prompt_text="A dragon flying through clouds",
    workflow_path="workflows/wan22_i2v_workflow.json",
    out_dir="output"
)

print("生成されたファイル:", output_files)
```

## 実践例

### 例1: Ollamaと連携した完全自動化

```python
from mini_muse.ollama_prompt import analyze_image_with_ollama
from mini_muse.comfy_runner import run_comfy_pipeline

# 1. 画像からプロンプト生成
prompt = analyze_image_with_ollama("input/sample.jpg")
print(f"生成されたプロンプト: {prompt}")

# 2. ComfyUIで動画生成
output_files = run_comfy_pipeline(
    image_path="input/sample.jpg",
    prompt_text=prompt,
    workflow_path="workflows/wan22_i2v_workflow.json",
    out_dir="output"
)

print(f"生成された動画: {output_files}")
```

### 例2: 複数画像の一括処理

```python
from pathlib import Path
from mini_muse.ollama_prompt import analyze_image_with_ollama
from mini_muse.comfy_runner import run_comfy_pipeline

input_dir = Path("input")
for image_path in input_dir.glob("*.jpg"):
    print(f"\n処理中: {image_path.name}")

    # プロンプト生成
    prompt = analyze_image_with_ollama(image_path)

    # 動画生成
    outputs = run_comfy_pipeline(
        image_path=image_path,
        prompt_text=prompt,
        workflow_path="workflows/wan22_i2v_workflow.json",
        out_dir=f"output/{image_path.stem}"
    )

    print(f"完了: {outputs}")
```

### 例3: 個別関数の使用

```python
from mini_muse.comfy_runner import (
    upload_image_to_comfyui,
    load_workflow,
    replace_placeholders,
    submit_workflow,
    wait_for_history,
    download_outputs
)

# 1. 画像アップロード
image_filename = upload_image_to_comfyui("input/sample.jpg")
print(f"アップロード完了: {image_filename}")

# 2. ワークフロー読み込み＆差し替え
workflow = load_workflow("workflows/wan22_i2v_workflow.json")
workflow = replace_placeholders(
    workflow,
    image_filename=image_filename,
    prompt_text="A beautiful sunset"
)

# 3. 実行
prompt_id = submit_workflow(workflow)
print(f"実行開始: {prompt_id}")

# 4. 完了待機
wait_for_history(prompt_id, timeout_s=600)
print("実行完了")

# 5. 出力ダウンロード
outputs = download_outputs(prompt_id, save_dir="output")
print(f"保存完了: {outputs}")
```

## 関数詳細

### upload_image_to_comfyui(image_path, *, host) -> str

画像をComfyUIサーバーにアップロードします。

**引数:**
- `image_path` (str | Path): 画像ファイルパス
- `host` (str): ComfyUIサーバーURL（デフォルト: http://127.0.0.1:8188）

**戻り値:**
- `str`: アップロードされたファイル名

### load_workflow(path) -> Dict[str, Any]

ワークフローJSONファイルを読み込みます。

**引数:**
- `path` (str | Path): ワークフローJSONファイルパス

**戻り値:**
- `Dict[str, Any]`: ワークフロー辞書

### replace_placeholders(workflow, image_filename, prompt_text) -> Dict[str, Any]

ワークフロー内のプレースホルダを実際の値に置換します。

**プレースホルダ:**
- `###IMAGE_FILENAME###`: 画像ファイル名
- `###PROMPT###`: プロンプトテキスト

**引数:**
- `workflow` (Dict[str, Any]): ワークフロー辞書
- `image_filename` (str): 画像ファイル名
- `prompt_text` (str): プロンプトテキスト

**戻り値:**
- `Dict[str, Any]`: 置換後のワークフロー辞書

### submit_workflow(workflow, *, host) -> str

ワークフローをComfyUIに投入します。

**引数:**
- `workflow` (Dict[str, Any]): ワークフロー辞書
- `host` (str): ComfyUIサーバーURL

**戻り値:**
- `str`: プロンプトID

### wait_for_history(prompt_id, *, host, timeout_s, poll_s) -> Dict[str, Any]

実行完了を待機します（履歴ポーリング）。

**引数:**
- `prompt_id` (str): プロンプトID
- `host` (str): ComfyUIサーバーURL
- `timeout_s` (int): タイムアウト時間（秒）（デフォルト: 600）
- `poll_s` (float): ポーリング間隔（秒）（デフォルト: 1.5）

**戻り値:**
- `Dict[str, Any]`: 履歴エントリ

### download_outputs(prompt_id, save_dir, *, host) -> List[Path]

生成された出力ファイルをダウンロードします。

**引数:**
- `prompt_id` (str): プロンプトID
- `save_dir` (str | Path): 保存先ディレクトリ
- `host` (str): ComfyUIサーバーURL

**戻り値:**
- `List[Path]`: 保存されたファイルパスのリスト

### run_comfy_pipeline(image_path, prompt_text, workflow_path, *, host, out_dir, timeout_s) -> List[Path]

画像→動画生成の完全自動化パイプライン。

**引数:**
- `image_path` (str | Path): 入力画像パス
- `prompt_text` (str): プロンプトテキスト
- `workflow_path` (str | Path): ワークフローJSONパス
- `host` (str): ComfyUIサーバーURL（デフォルト: http://127.0.0.1:8188）
- `out_dir` (str | Path): 出力ディレクトリ（デフォルト: output）
- `timeout_s` (int): タイムアウト時間（秒）（デフォルト: 600）

**戻り値:**
- `List[Path]`: 生成されたファイルパスのリスト

## プレースホルダの配置方法

ComfyUIでワークフローをエクスポートした後、以下の箇所を手動で編集：

```json
{
  "97": {
    "inputs": {
      "image": "###IMAGE_FILENAME###"
    },
    "class_type": "LoadImage"
  },
  "93": {
    "inputs": {
      "text": "###PROMPT###",
      "clip": ["84", 0]
    },
    "class_type": "CLIPTextEncode"
  }
}
```

## エラーハンドリング

```python
from mini_muse.comfy_runner import run_comfy_pipeline
import requests

try:
    outputs = run_comfy_pipeline(
        image_path="input/sample.jpg",
        prompt_text="A dragon flying",
        workflow_path="workflows/wan22_i2v_workflow.json"
    )
except FileNotFoundError:
    print("エラー: ファイルが見つかりません")
except requests.exceptions.ConnectionError:
    print("エラー: ComfyUIサーバーに接続できません")
except TimeoutError as e:
    print(f"エラー: タイムアウト - {e}")
except RuntimeError as e:
    print(f"エラー: 実行エラー - {e}")
```

## トラブルシューティング

### Q: アップロードエラー（4xx/5xx）
A: 以下を確認してください：
   1. ComfyUIサーバーが起動しているか
   2. サーバーアドレスが正しいか
   3. ファイルパスが正しいか

### Q: ワークフロー投入エラー（400）
A: 以下を確認してください：
   1. プレースホルダが正しく置換されているか
   2. ワークフローJSONの構造が正しいか
   3. ノード接続が整合しているか

### Q: タイムアウトエラー
A: 以下を確認してください：
   1. モデルがロードされているか
   2. VRAMが十分か
   3. 推論時間が長すぎないか（timeout_sを増やす）

### Q: 出力ファイルが見つからない（404）
A: 以下を確認してください：
   1. ワークフローにSaveノードがあるか
   2. /history にエントリがあるか
   3. 出力フォーマットが正しいか

================================================================================
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import requests

COMFY_HOST = "http://127.0.0.1:8000"

# -------- 1) 画像アップロード --------
def upload_image_to_comfyui(image_path: str | Path, *, host: str = COMFY_HOST) -> str:
    """
    画像をComfyUIサーバーにアップロードします。

    Args:
        image_path: 画像ファイルパス
        host: ComfyUIサーバーURL（デフォルト: http://127.0.0.1:8188）

    Returns:
        str: アップロードされたファイル名

    Raises:
        FileNotFoundError: 画像ファイルが見つからない
        requests.HTTPError: アップロードエラー

    Examples:
        >>> filename = upload_image_to_comfyui("input/sample.jpg")
        >>> print(filename)
        "sample.jpg"
    """
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(p)
    with open(p, "rb") as f:
        r = requests.post(
            f"{host}/upload/image",
            files={"image": (p.name, f, "application/octet-stream")},
            data={"overwrite": "true"},
            timeout=120,
        )
    r.raise_for_status()
    # ComfyUI/input/{p.name} に配置される。ワークフローの LoadImage.inputs.image にはこのファイル名を指定する。
    return p.name  # ファイル名のみ返す

# -------- 2) ワークフロー JSON 差し替え（プレースホルダ方式）--------
def load_workflow(path: str | Path) -> Dict[str, Any]:
    """
    ワークフローJSONファイルを読み込みます。

    Args:
        path: ワークフローJSONファイルパス

    Returns:
        Dict[str, Any]: ワークフロー辞書

    Raises:
        FileNotFoundError: ファイルが見つからない
        json.JSONDecodeError: JSON解析エラー

    Examples:
        >>> workflow = load_workflow("workflows/wan22_i2v_workflow.json")
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))

def replace_placeholders(workflow: Dict[str, Any], image_filename: str, prompt_text: str) -> Dict[str, Any]:
    """
    ワークフロー内のプレースホルダを実際の値に置換します。

    プレースホルダ:
    - ###IMAGE_FILENAME###: 画像ファイル名
    - ###PROMPT###: プロンプトテキスト

    Args:
        workflow: ワークフロー辞書
        image_filename: 画像ファイル名
        prompt_text: プロンプトテキスト

    Returns:
        Dict[str, Any]: 置換後のワークフロー辞書

    Examples:
        >>> wf = load_workflow("workflow.json")
        >>> wf = replace_placeholders(wf, "sample.jpg", "A dragon flying")
    """
    # ComfyUI ワークフローは { "nodes": { "id": {...} } } 形式だったり配列だったり差があるため包括的に処理
    def _patch(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _patch(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_patch(v) for v in obj]
        elif isinstance(obj, str):
            s = obj
            if "###IMAGE_FILENAME###" in s:
                s = s.replace("###IMAGE_FILENAME###", image_filename)
            if "###PROMPT###" in s:
                s = s.replace("###PROMPT###", prompt_text)
            return s
        else:
            return obj
    return _patch(workflow)

# -------- 3) ワークフロー投入 --------
def submit_workflow(workflow: Dict[str, Any], *, host: str = COMFY_HOST) -> str:
    """
    ワークフローをComfyUIに投入します。

    Args:
        workflow: ワークフロー辞書
        host: ComfyUIサーバーURL

    Returns:
        str: プロンプトID

    Raises:
        requests.HTTPError: 投入エラー
        RuntimeError: prompt_idが取得できない

    Examples:
        >>> prompt_id = submit_workflow(workflow)
        >>> print(prompt_id)
        "abc123-def456-..."
    """
    r = requests.post(f"{host}/prompt", json={"prompt": workflow}, timeout=120)
    r.raise_for_status()
    data = r.json()
    pid = data.get("prompt_id")
    if not pid:
        raise RuntimeError(f"prompt_id not found in response: {data}")
    return pid

# -------- 4) 完了待機（/history/{pid} を優先、無ければ /history で全件から抽出）--------
def wait_for_history(prompt_id: str, *, host: str = COMFY_HOST, timeout_s: int = 600, poll_s: float = 1.5) -> Dict[str, Any]:
    """
    実行完了を待機します（履歴ポーリング）。

    Args:
        prompt_id: プロンプトID
        host: ComfyUIサーバーURL
        timeout_s: タイムアウト時間（秒）（デフォルト: 600）
        poll_s: ポーリング間隔（秒）（デフォルト: 1.5）

    Returns:
        Dict[str, Any]: 履歴エントリ

    Raises:
        TimeoutError: タイムアウト

    Examples:
        >>> history = wait_for_history(prompt_id, timeout_s=600)
    """
    t0 = time.time()
    # まずは /history/{pid} を試す
    while True:
        try:
            r = requests.get(f"{host}/history/{prompt_id}", timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data and "outputs" in data and data["outputs"]:
                    return data
        except requests.RequestException:
            pass
        # /history 全件から拾うフォールバック
        try:
            r = requests.get(f"{host}/history", timeout=30)
            if r.status_code == 200:
                h = r.json() or {}
                if prompt_id in h:
                    data = h[prompt_id]
                    if data and "outputs" in data and data["outputs"]:
                        return data
        except requests.RequestException:
            pass

        if time.time() - t0 > timeout_s:
            raise TimeoutError(f"history not ready within {timeout_s}s (prompt_id={prompt_id})")
        time.sleep(poll_s)

# -------- 5) 出力ファイルのダウンロード --------
def _collect_output_files_from_history(history_entry: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    履歴エントリから出力ファイル情報を収集します。

    Args:
        history_entry: 履歴エントリ辞書

    Returns:
        List[Tuple[str, str]]: (filename, type) のタプルリスト
    """
    files: List[Tuple[str, str]] = []
    outputs = history_entry.get("outputs") or {}
    # outputs は { node_id: { "images": [{filename, type, subfolder, ...}], "gifs": ..., "videos": ... } }
    for _nid, node_out in outputs.items():
        for key in ("images", "gifs", "videos"):
            if key in node_out:
                for item in node_out[key]:
                    fn = item.get("filename")
                    tp = item.get("type", "output")
                    if fn:
                        files.append((fn, tp))
    return files

def download_outputs(prompt_id: str, save_dir: str | Path, *, host: str = COMFY_HOST) -> List[Path]:
    """
    生成された出力ファイルをダウンロードします。

    Args:
        prompt_id: プロンプトID
        save_dir: 保存先ディレクトリ
        host: ComfyUIサーバーURL

    Returns:
        List[Path]: 保存されたファイルパスのリスト

    Raises:
        RuntimeError: 履歴取得エラー
        requests.HTTPError: ダウンロードエラー

    Examples:
        >>> outputs = download_outputs(prompt_id, "output")
        >>> print(outputs)
        [PosixPath('output/video_001.mp4')]
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # history を取得
    try:
        r = requests.get(f"{host}/history/{prompt_id}", timeout=30)
        if r.status_code == 200:
            hist = r.json()
        else:
            raise RuntimeError(f"history/{prompt_id} status={r.status_code}")
    except requests.RequestException as e:
        raise RuntimeError(f"failed to fetch history: {e}")

    files = _collect_output_files_from_history(hist)
    saved: List[Path] = []
    for fn, tp in files:
        # /view?filename=XXX&type=output で取得可能
        params = {"filename": fn, "type": tp}
        rv = requests.get(f"{host}/view", params=params, timeout=120)
        rv.raise_for_status()
        out_path = save_dir / Path(fn).name
        out_path.write_bytes(rv.content)
        saved.append(out_path)
    return saved

# -------- まとめ：ワンショット実行 --------
def run_comfy_pipeline(
    image_path: str | Path,
    prompt_text: str,
    workflow_path: str | Path,
    *,
    host: str = COMFY_HOST,
    out_dir: str | Path = "output",
    timeout_s: int = 600,
) -> List[Path]:
    """
    画像→動画生成の完全自動化パイプライン。

    処理フロー:
    1. 画像アップロード
    2. ワークフロー読み込み＆プレースホルダ置換
    3. ワークフロー投入
    4. 完了待機（履歴ポーリング）
    5. 出力ファイルダウンロード

    Args:
        image_path: 入力画像パス
        prompt_text: プロンプトテキスト
        workflow_path: ワークフローJSONパス
        host: ComfyUIサーバーURL（デフォルト: http://127.0.0.1:8188）
        out_dir: 出力ディレクトリ（デフォルト: output）
        timeout_s: タイムアウト時間（秒）（デフォルト: 600）

    Returns:
        List[Path]: 生成されたファイルパスのリスト

    Raises:
        FileNotFoundError: ファイルが見つからない
        requests.HTTPError: API エラー
        TimeoutError: タイムアウト
        RuntimeError: 実行エラー

    Examples:
        >>> outputs = run_comfy_pipeline(
        ...     image_path="input/sample.jpg",
        ...     prompt_text="A dragon flying through clouds",
        ...     workflow_path="workflows/wan22_i2v_workflow.json",
        ...     out_dir="output"
        ... )
        >>> print(outputs)
        [PosixPath('output/video_001.mp4')]
    """
    # 1) 画像アップロード
    image_filename = upload_image_to_comfyui(image_path, host=host)

    # 2) ワークフロー読み込み＆差し替え
    wf = load_workflow(workflow_path)
    wf = replace_placeholders(wf, image_filename=image_filename, prompt_text=prompt_text)

    # 3) 実行
    pid = submit_workflow(wf, host=host)

    # 4) 完了待機
    wait_for_history(pid, host=host, timeout_s=timeout_s)

    # 5) 出力取得
    return download_outputs(pid, save_dir=out_dir, host=host)
