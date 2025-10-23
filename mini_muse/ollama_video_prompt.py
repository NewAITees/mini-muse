"""
Ollama画像分析モジュール

このモジュールは、Ollama LMM (Large Multimodal Model) を使用して、
画像から動画化プロンプトを生成する機能を提供します。

================================================================================
使い方 - analyze_image_with_ollama
================================================================================

## 概要

analyze_image_with_ollama関数は、画像ファイルをOllama LMMで分析し、
5秒間の動画アニメーション用プロンプトを1行で生成します。

## 前提条件

1. **Ollamaサーバーの起動**
   Ollamaサーバーが起動している必要があります。
   デフォルトでは `http://localhost:11434` で起動します。

2. **必要なモデル**
   ```bash
   ollama pull llava
   ```

3. **必要なPythonパッケージ**
   ```bash
   pip install requests pillow
   ```

## 基本的な使い方

### 1. インポート

```python
from mini_muse.ollama_prompt import analyze_image_with_ollama
```

### 2. 画像分析

```python
# 基本的な使用方法
prompt = analyze_image_with_ollama("input/sample.jpg")
print(prompt)
# 例: "Anime girl portrait, gentle hair movement, slow camera dolly, soft golden hour lighting"

# カスタムモデルを使用
prompt = analyze_image_with_ollama(
    "input/sample.jpg",
    model="bakllava",
    host="http://localhost:11434"
)

# カスタムプロンプトを使用
custom_prompt = "Describe this image in 10 words or less"
prompt = analyze_image_with_ollama(
    "input/sample.jpg",
    prompt=custom_prompt
)
```

## パラメータ詳細

### analyze_image_with_ollama(image_path, *, model, host, prompt, timeout)

画像をOllama LMMで分析し、1行の動画化プロンプトを返します。

**引数:**
- `image_path` (str | Path): 画像ファイルパス（jpg/png/webp）
- `model` (str): 使用するモデル名（デフォルト: "llava"）
- `host` (str): OllamaサーバーURL（デフォルト: "http://localhost:11434"）
- `prompt` (Optional[str]): カスタム分析プロンプト（デフォルト: None）
- `timeout` (int): タイムアウト時間（秒）（デフォルト: 120）

**戻り値:**
- `str`: 1行の動画化プロンプト

**例外:**
- `FileNotFoundError`: 画像ファイルが見つからない
- `requests.HTTPError`: Ollama APIエラー
- `requests.Timeout`: タイムアウト
- `KeyError`: レスポンス形式が不正
- `ValueError`: 空のレスポンス

## 実践例

### 例1: 基本的な画像分析

```python
from mini_muse.ollama_prompt import analyze_image_with_ollama

# 画像分析
prompt = analyze_image_with_ollama("input/anime_girl.jpg")
print(prompt)
# → "Anime girl portrait, gentle hair movement, slow camera dolly, soft golden hour lighting"
```

### 例2: 複数画像の分析

```python
from pathlib import Path
from mini_muse.ollama_prompt import analyze_image_with_ollama

input_dir = Path("input")
for image_path in input_dir.glob("*.jpg"):
    print(f"\n=== {image_path.name} ===")
    try:
        prompt = analyze_image_with_ollama(image_path)
        print(f"プロンプト: {prompt}")
    except Exception as e:
        print(f"エラー: {e}")
```

### 例3: エラーハンドリング

```python
from mini_muse.ollama_prompt import analyze_image_with_ollama
import requests

try:
    prompt = analyze_image_with_ollama("input/sample.jpg")
    print(prompt)
except FileNotFoundError:
    print("エラー: 画像ファイルが見つかりません")
except requests.exceptions.ConnectionError:
    print("エラー: Ollamaサーバーに接続できません")
    print("Ollamaが起動しているか確認してください")
except requests.exceptions.Timeout:
    print("エラー: タイムアウトしました")
except Exception as e:
    print(f"エラー: {e}")
```

## 画像の前処理

入力画像は自動的に以下の処理が行われます：

1. **RGB変換**: すべての画像をRGBモードに変換
2. **リサイズ**: 短辺を768pxに縮小（メモリ節約）
3. **JPEG圧縮**: 品質90%でJPEG圧縮
4. **Base64エンコード**: API送信用にエンコード

## デフォルト分析プロンプト

デフォルトでは以下のプロンプトを使用：

```
Analyze this image and output a single concise prompt for a 5-second video animation.
Format strictly: "[subject], [motion], [camera movement], [atmosphere]".
No extra words.
```

## トラブルシューティング

### Q: 接続エラーが発生する
A: 以下を確認してください：
   1. Ollamaサーバーが起動しているか（`ollama serve`）
   2. サーバーアドレスが正しいか（デフォルト: http://localhost:11434）
   3. ファイアウォールで通信がブロックされていないか

### Q: モデルが見つからない
A: モデルをpullしてください：
   ```bash
   ollama pull llava
   ```

### Q: タイムアウトエラー
A: `timeout`パラメータを増やしてください：
   ```python
   prompt = analyze_image_with_ollama("image.jpg", timeout=300)
   ```

### Q: 空のレスポンスが返る
A: 以下を試してください：
   1. 画像サイズを小さくする
   2. 別のモデルを使用（`bakllava`など）
   3. カスタムプロンプトを指定

================================================================================
"""

from __future__ import annotations
import io
import base64
import json
from pathlib import Path
from typing import Optional
import requests
from PIL import Image

DEFAULT_ANALYSIS_PROMPT = (
    "Analyze this image and output a single concise prompt for a 5-second video animation. "
    "Format strictly: \"[subject], [motion], [camera movement], [atmosphere]\". "
    "No extra words."
)

def _load_and_resize_to_base64(image_path: str | Path, short_side: int = 768) -> str:
    """
    画像を読み込み、リサイズし、base64エンコードします。

    Args:
        image_path: 画像ファイルパス
        short_side: 短辺のピクセル数（デフォルト: 768）

    Returns:
        str: base64エンコードされた画像データ

    Raises:
        FileNotFoundError: 画像ファイルが見つからない
    """
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"image not found: {p}")
    with Image.open(p) as im:
        im = im.convert("RGB")
        w, h = im.size
        if min(w, h) > short_side:
            if w <= h:
                new_w = short_side
                new_h = int(h * (short_side / w))
            else:
                new_h = short_side
                new_w = int(w * (short_side / h))
            im = im.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def analyze_image_with_ollama(
    image_path: str | Path,
    *,
    model: str = "llava",
    host: str = "http://localhost:11434",
    prompt: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """
    画像 → LMM 分析 → 1行の動画化プロンプト文字列を返す。
    失敗時は requests.HTTPError / KeyError / Timeout など例外を送出。

    Args:
        image_path: 画像ファイルパス（jpg/png/webp）
        model: 使用するモデル名（デフォルト: "llava"）
        host: OllamaサーバーURL（デフォルト: "http://localhost:11434"）
        prompt: カスタム分析プロンプト（Noneの場合はデフォルトプロンプトを使用）
        timeout: タイムアウト時間（秒）（デフォルト: 120）

    Returns:
        str: 1行の動画化プロンプト文字列

    Raises:
        FileNotFoundError: 画像ファイルが見つからない
        requests.HTTPError: HTTP エラー
        requests.Timeout: タイムアウト
        KeyError: レスポンス形式が不正
        ValueError: 空のレスポンス

    Examples:
        >>> prompt = analyze_image_with_ollama("input/sample.jpg")
        >>> print(prompt)
        "Anime girl portrait, gentle hair movement, slow camera dolly, soft golden hour lighting"

        >>> prompt = analyze_image_with_ollama("image.jpg", model="bakllava", timeout=300)
    """
    img64 = _load_and_resize_to_base64(image_path)
    body = {
        "model": model,
        "prompt": prompt or DEFAULT_ANALYSIS_PROMPT,
        "images": [img64],
        "stream": False,
    }
    url = f"{host.rstrip('/')}/api/generate"
    r = requests.post(url, json=body, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if "response" not in data:
        raise KeyError(f"unexpected response fields: {list(data.keys())}")
    text = (data["response"] or "").strip().replace("\n", " ")
    if not text:
        raise ValueError("empty response from model")
    # 1行フォーマットの軽い正規化（末尾ピリオド削除）
    if text.endswith("."):
        text = text[:-1]
    return text
