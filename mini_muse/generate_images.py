#!/usr/bin/env python3
"""
ComfyUI 画像バッチ生成スクリプト

使い方:
    # 基本的な使用方法（1枚生成）
    python generate_images.py

    # 複数枚生成
    python generate_images.py --count 10

    # テンプレートを指定
    python generate_images.py --template detailed_diorama --count 5

    # パラメータを指定
    python generate_images.py --count 3 --steps 40 --cfg 7.0 --width 1024 --height 1024

    # シード固定で再現性を確保
    python generate_images.py --seed 42 --count 1

機能:
    - プロンプト自動生成（PromptGenerator使用）
    - ComfyUI APIを使用した画像生成
    - バッチ処理（1枚～任意の枚数）
    - 進捗表示とエラーハンドリング
    - 生成パラメータのカスタマイズ
    - 出力ファイル名の自動生成（タイムスタンプ付き）
"""

import argparse
import csv
import random
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from mini_muse.comfyui_client import ComfyUIClient
from mini_muse.prompt_generator import PromptGenerator, list_available_template_files


def parse_server_address(server: str) -> tuple[str, Optional[int]]:
    """host:port 形式の文字列を分解し、ポート未指定の場合は None を返す"""
    if ":" not in server:
        return server, None

    host, port_str = server.rsplit(":", 1)
    if port_str.isdigit():
        return host, int(port_str)
    return server, None


def is_port_in_use(host: str, port: int, timeout: float = 0.25) -> bool:
    """指定ポートに接続できれば使用中とみなす"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def find_available_port(
    host: str, min_port: int = 10000, max_port: int = 65535, max_attempts: int = 50
) -> int:
    """空いている5桁ポートを探索"""
    attempts = 0
    while attempts < max_attempts:
        port = random.randint(min_port, max_port)
        attempts += 1
        if not is_port_in_use(host, port):
            return port
    raise RuntimeError(
        "空きポートを見つけられませんでした。max_attempts を増やすか範囲を見直してください。"
    )


def write_port_registry(registry_path: Path, host: str, port: int) -> None:
    """自動決定したポート番号をファイルに書き出す"""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(f"{host}:{port}\n", encoding="utf-8")


def read_port_registry(registry_path: Path, fallback_host: Optional[str] = None) -> tuple[str, int]:
    """ポートレジストリファイルから host:port を読み取る"""

    if not registry_path.exists():
        raise FileNotFoundError(f"ポートレジストリが見つかりません: {registry_path}")

    content = registry_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"ポートレジストリが空です: {registry_path}")

    if ":" in content:
        host, port = parse_server_address(content)
        if port is None:
            raise ValueError(
                f"レジストリの形式が不正です (host:port を指定してください): {content}"
            )
        return host, port

    if not content.isdigit():
        raise ValueError(f"レジストリの形式が不正です: {content}")

    if fallback_host is None:
        raise ValueError(
            "ホスト名が不明です。--server でホストを指定するか、レジストリに host:port を書き込んでください。"
        )

    return fallback_host, int(content)


def wait_for_server_start(host: str, port: int, wait_seconds: int) -> None:
    """指定秒数サーバー起動を待機し、利用可能になったらログを出す"""
    if wait_seconds <= 0:
        return

    print(f"  サーバー起動を最大 {wait_seconds} 秒待機します...")
    end_time = time.time() + wait_seconds
    while time.time() < end_time:
        if is_port_in_use(host, port):
            print(f"  ✓ サーバー接続を確認しました: {host}:{port}")
            return
        time.sleep(1)
    print("  ⚠️ サーバーの起動を確認できませんでした。続行しますが接続できない場合があります。")


def resolve_dated_output_dir(base_dir: Path, date_str: str) -> tuple[Path, bool]:
    """ベースディレクトリが日付で終わる場合はそのまま使用し、そうでなければサブディレクトリを作成

    Returns:
        (Path, bool): (使用するディレクトリ, 既存ディレクトリだったか)
    """
    target_dir = base_dir if base_dir.name == date_str else base_dir / date_str
    existed = target_dir.exists()
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir, existed


def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="ComfyUIを使用してバッチ画像生成を行います",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --count 10                          # 10枚生成
  %(prog)s --template abstract_art --count 5   # abstract_artテンプレートで5枚生成
  %(prog)s --steps 40 --cfg 7.0 --count 3      # パラメータ指定で3枚生成
        """,
    )

    # 生成枚数
    parser.add_argument(
        "--count", "-c", type=int, default=1, help="生成する画像の枚数（デフォルト: 1）"
    )

    # テンプレートファイル選択
    parser.add_argument(
        "--template-file",
        type=str,
        default=None,
        help="使用するテンプレートファイル名（例: prompt_templates_Tシャツデザイン_20250127.json）",
    )

    # テンプレート選択
    parser.add_argument(
        "--template",
        "-t",
        type=str,
        default=None,
        help="使用するプロンプトテンプレート名（指定しない場合は毎回ランダムに選択）",
    )

    # テンプレートファイル一覧表示
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="利用可能なテンプレートファイル一覧を表示して終了",
    )

    # ComfyUIサーバー
    parser.add_argument(
        "--server",
        type=str,
        default="127.0.0.1:15434",
        help="ComfyUIサーバーアドレス（デフォルト: 127.0.0.1:15434）",
    )

    parser.add_argument(
        "--auto-server-port",
        action="store_true",
        help="5桁の空きポートを自動で割り当てて --server のポート部を上書き",
    )

    parser.add_argument(
        "--auto-server-port-only",
        action="store_true",
        help="ポート割り当てと記録だけを行い、画像生成は実行しない",
    )

    parser.add_argument(
        "--use-port-registry",
        action="store_true",
        help="port_registry_file から host:port を読み取り --server を上書き",
    )

    parser.add_argument(
        "--port-registry-file",
        type=str,
        default="config/auto_server_port.txt",
        help="自動割り当てしたポート番号を書き出すファイルパス",
    )

    parser.add_argument(
        "--server-wait-seconds",
        type=int,
        default=0,
        help="自動割り当て後にComfyUIサーバーの起動を待機する秒数",
    )

    # ワークフローファイル
    parser.add_argument(
        "--workflow",
        type=str,
        default="workflows/sd3.5_large_turbo_upscale.json",
        help="ワークフローファイルのパス（デフォルト: workflows/sd3.5_large_turbo_upscale.json）",
    )

    # 生成パラメータ
    parser.add_argument(
        "--steps", type=int, default=30, help="サンプリングステップ数（デフォルト: 30）"
    )

    parser.add_argument("--cfg", type=float, default=5.45, help="CFGスケール（デフォルト: 5.45）")

    parser.add_argument("--width", type=int, default=1024, help="画像の幅（デフォルト: 1024）")

    parser.add_argument("--height", type=int, default=1024, help="画像の高さ（デフォルト: 1024）")

    parser.add_argument(
        "--seed", type=int, default=None, help="シード値（指定しない場合はランダム）"
    )

    # 出力先
    parser.add_argument(
        "--output-dir",
        type=str,
        default="stablediffusion/outputs",
        help="出力ディレクトリ（デフォルト: stablediffusion/outputs）",
    )

    # ネガティブプロンプト
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default="blurry, low quality, distorted, ugly, deformed",
        help="ネガティブプロンプト",
    )

    return parser.parse_args()


def write_csv_log(csv_path, data, is_new_file):
    """CSVログファイルに生成情報を書き込む"""
    fieldnames = [
        "filename",
        "template",
        "positive_prompt",
        "negative_prompt",
        "seed",
        "steps",
        "cfg",
        "width",
        "height",
        "image_size_bytes",
        "generation_time_seconds",
        "timestamp",
    ]

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # 新規ファイルの場合はヘッダーを書き込む
        if is_new_file:
            writer.writeheader()

        writer.writerow(data)


def main():
    """メイン処理"""
    args = parse_arguments()

    if args.auto_server_port_only:
        args.auto_server_port = True

    registry_path = Path(args.port_registry_file)

    server_host, explicit_port = parse_server_address(args.server)

    if args.use_port_registry and args.auto_server_port:
        raise ValueError("--use-port-registry と --auto-server-port は同時に指定できません。")

    if args.use_port_registry:
        server_host, explicit_port = read_port_registry(registry_path, fallback_host=server_host)
        args.server = f"{server_host}:{explicit_port}"

    if args.auto_server_port:
        assigned_port = find_available_port(server_host)
        args.server = f"{server_host}:{assigned_port}"
        write_port_registry(registry_path, server_host, assigned_port)
        print("=" * 70)
        print("ComfyUI サーバーポート自動割り当て")
        print("=" * 70)
        print(f"  ホスト: {server_host}")
        print(f"  割り当てポート: {assigned_port}")
        print(f"  記録ファイル: {registry_path}")

        if args.auto_server_port_only:
            print("  ※ ポートをレジストリに書き出しただけで処理を終了しました。")
            print(
                "    ComfyUI をこのポートで起動した後、--use-port-registry などで再実行してください。"
            )
            return 0

        wait_for_server_start(server_host, assigned_port, args.server_wait_seconds)
    else:
        if explicit_port is None:
            raise ValueError(
                "--auto-server-port を使用しない場合、--server には host:port 形式を指定してください。"
            )

    # テンプレートファイル一覧表示モード
    if args.list_templates:
        print("=" * 70)
        print("利用可能なテンプレートファイル")
        print("=" * 70)
        template_files = list_available_template_files()
        if template_files:
            for i, filename in enumerate(template_files, 1):
                print(f"{i:2d}. {filename}")
        else:
            print("テンプレートファイルが見つかりません。")
        print("=" * 70)
        return 0

    print("=" * 70)
    print("ComfyUI バッチ画像生成")
    print("=" * 70)

    # 出力ディレクトリの確認
    base_output_dir = Path(args.output_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)

    # ComfyUIクライアント初期化
    print("\n[1] ComfyUIクライアントを初期化中...")
    print(f"  サーバー: {args.server}")
    client = ComfyUIClient(args.server)

    # ワークフロー読み込み
    print("\n[2] ワークフローを読み込み中...")
    print(f"  ワークフロー: {args.workflow}")
    workflow = client.load_workflow(args.workflow)

    # プロンプト生成器初期化
    print("\n[3] プロンプト生成器を初期化中...")
    if args.template_file:
        print(f"  テンプレートファイル: {args.template_file}")
        prompt_gen = PromptGenerator(elements_file=args.template_file)
    else:
        prompt_gen = PromptGenerator()

    # 生成設定表示
    print("\n[4] 生成設定:")
    print(f"  生成枚数: {args.count}枚")
    print(f"  テンプレート: {args.template if args.template else '毎回ランダム選択'}")
    print(f"  ステップ数: {args.steps}")
    print(f"  CFGスケール: {args.cfg}")
    print(f"  解像度: {args.width}x{args.height}")
    print(f"  シード: {args.seed if args.seed else 'ランダム'}")
    print(f"  出力先: {base_output_dir}")

    # バッチ生成開始
    print("\n[5] 画像生成を開始...")
    print("=" * 70)

    success_count = 0
    failed_count = 0
    start_time = time.time()
    current_date = None
    current_date_dir = None
    current_csv_path = None

    for i in range(args.count):
        print(f"\n[{i+1}/{args.count}] 画像生成中...")

        try:
            # 日付をチェックして、変わっていたら新しいフォルダを作成
            generation_date = datetime.now().strftime("%Y%m%d")
            if generation_date != current_date:
                current_date = generation_date
                current_date_dir, existed = resolve_dated_output_dir(
                    base_output_dir, generation_date
                )
                current_csv_path = current_date_dir / f"generation_log_{current_date}.csv"
                action = "既存フォルダ使用" if existed else "日付フォルダ作成"
                print(f"  {action}: {current_date_dir}")

            # プロンプト生成
            print("  プロンプト生成中...")
            prompt = prompt_gen.generate_prompt(args.template)
            print(f"  プロンプト: {prompt[:80]}...")

            # シード値の設定
            seed = args.seed if args.seed else None
            if seed is not None and args.count > 1:
                # 複数枚生成時はシードをインクリメント
                seed = seed + i

            # 出力パス生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            template_name = args.template if args.template else "random"
            filename = f"{template_name}_{timestamp}_{i+1:04d}.png"
            output_path = current_date_dir / filename

            # 画像生成開始時刻
            gen_start_time = time.time()

            # 画像生成
            print("  画像生成中...")
            image_data = client.generate_image(
                workflow,
                positive_prompt=prompt,
                negative_prompt=args.negative_prompt,
                seed=seed,
                steps=args.steps,
                cfg=args.cfg,
                width=args.width,
                height=args.height,
                save_path=str(output_path),
            )

            # 生成時間を計算
            gen_time = time.time() - gen_start_time

            # CSVログに記録
            csv_data = {
                "filename": filename,
                "template": template_name,
                "positive_prompt": prompt,
                "negative_prompt": args.negative_prompt,
                "seed": seed if seed is not None else "random",
                "steps": args.steps,
                "cfg": args.cfg,
                "width": args.width,
                "height": args.height,
                "image_size_bytes": len(image_data),
                "generation_time_seconds": f"{gen_time:.2f}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # CSVファイルが新規かどうかをチェック
            is_new_csv = not current_csv_path.exists()
            write_csv_log(current_csv_path, csv_data, is_new_csv)

            print(f"  ✓ 成功: {filename}")
            print(f"  画像サイズ: {len(image_data):,} bytes")
            print(f"  生成時間: {gen_time:.1f}秒")
            print(f"  CSVログ: {current_csv_path.name}")
            success_count += 1

        except Exception as e:
            print(f"  ✗ エラー: {e}")
            failed_count += 1
            continue

    # 結果サマリー
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("生成完了")
    print("=" * 70)
    print(f"成功: {success_count}枚")
    print(f"失敗: {failed_count}枚")
    print(f"合計時間: {elapsed_time:.1f}秒")
    if success_count > 0:
        print(f"平均生成時間: {elapsed_time/success_count:.1f}秒/枚")
    print(f"出力先: {base_output_dir}")
    if current_csv_path:
        print(f"CSVログ: {current_csv_path}")
    print("=" * 70)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
