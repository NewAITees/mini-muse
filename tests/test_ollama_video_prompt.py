"""
Ollama動画プロンプト生成モジュールのテスト

このモジュールは、mini_muse.ollama_video_prompt の機能をテストします。
"""

import os
import pytest
from mini_muse.ollama_video_prompt import analyze_image_with_ollama

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llava:7b")

@pytest.mark.timeout(30)
def test_analyze_returns_nonempty(tmp_path):
    """
    正常系テスト：画像分析が空でない文字列を返すことを確認

    テスト内容：
    1. テスト用の小画像を生成
    2. analyze_image_with_ollama を呼び出し
    3. 返り値が文字列であることを確認
    4. 返り値が空でないことを確認
    5. フォーマットの最低限チェック（カンマで区切られた要素があること）
    """
    # テスト用の小画像を生成
    from PIL import Image
    p = tmp_path / "tiny.jpg"
    Image.new("RGB", (256, 256), (200, 160, 120)).save(p, "JPEG", quality=85)

    out = analyze_image_with_ollama(p, model=MODEL, host=OLLAMA_HOST, timeout=20)
    assert isinstance(out, str)
    assert len(out) > 0
    # フォーマットの最低限チェック（カンマで区切られた要素があること）
    assert "," in out

def test_error_when_missing_file():
    """
    異常系テスト：存在しないファイルを指定した場合にFileNotFoundErrorが発生することを確認

    テスト内容：
    1. 存在しないファイルパスを指定
    2. FileNotFoundError が発生することを確認
    """
    with pytest.raises(FileNotFoundError):
        analyze_image_with_ollama("no_such_file.jpg", host=OLLAMA_HOST)
