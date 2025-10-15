# mini_muse

ComfyUIベースの画像生成システム

## 概要

Mini-MuseはComfyUIを使用した画像生成プロジェクトです。プロンプト管理から画像生成、出力まで一貫して行うことができます。

## プロジェクト構成

```
mini-muse/
├── config/
│   └── config.yaml          # プロジェクト設定ファイル
├── prompts/                 # プロンプトファイル保存場所
├── stablediffusion/         # シンボリックリンク (/mnt/d/python/stablediffusion)
│   └── outputs/             # 生成画像の出力先
├── workflows/               # ComfyUIワークフローファイル
└── README.md                # このファイル
```

## フォルダ説明

### `prompts/`
- 画像生成に使用するプロンプトファイルを保存する場所
- テキストファイル形式で管理
- プロンプトの履歴やバリエーションを管理可能

### `stablediffusion/outputs/`
- 生成された画像の保存先
- シンボリックリンク先 (`/mnt/d/python/stablediffusion`) 配下に配置
- 日付やプロンプト名でサブフォルダ分けすることを推奨

### `config/`
- プロジェクトの設定ファイルを格納
- `config.yaml`: パス設定、ComfyUI設定、生成パラメータなど

### `workflows/`
- ComfyUIのワークフローファイル（JSON形式）を保存
- 異なる生成スタイルやモデルごとにワークフローを管理

## 設定ファイル

`config/config.yaml` で以下の設定を管理します：

- **パス設定**: プロンプトフォルダ、出力フォルダ
- **ComfyUI設定**: ベースURL、ワークフローパス
- **生成設定**: デフォルトの画像サイズ、ステップ数、CFGスケール

詳細は `config/config.yaml` を参照してください。

## 使用方法

1. ComfyUIを起動
2. `prompts/` にプロンプトファイルを配置
3. 必要に応じて `config/config.yaml` を編集
4. 画像生成を実行
5. 生成された画像は `stablediffusion/outputs/` に保存されます

## 必要な環境

- Python 3.x
- ComfyUI
- Stable Diffusion モデル

## ライセンス

MIT License

## 更新履歴

変更履歴は `doc/CHANGELOG_*.md` を参照してください。
