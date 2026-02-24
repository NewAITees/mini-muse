# Lessons - 過去の失敗と学び
## 記録ルール
- バグを解決したら、ここにパターンと対策を追記する
- 設計上の判断ミスや整合性の注意点も記録する
- 同じ失敗を繰り返さないための知見をまとめる

## 2026-02-20
- パターン: 新規プロンプトJSON追加時は、`elements` を `description` と `values` に統一し、`templates` は `description` と `text` に揃えると `PromptGenerator` に無変更で取り込める。
- 対策: 追加直後に `jq empty <file>` と `uv run python -c "from mini_muse.prompt_generator import PromptGenerator ..."` の2段確認を必ず実施する。
- パターン: 動物モチーフ系のホラーは「種名ベース」の語彙を残すと実在生物に寄りやすい。
- 対策: `motif_transformation_rules` のような「モチーフは痕跡のみ・種同定不可」を明示する要素をテンプレート本文に必ず差し込む。
- パターン: モノトーン指定だけでは中間調寄りに出力され、白黒の迫力が弱くなることがある。
- 対策: `monochrome_value_design` を独立させ、高キー/低キー/黒潰し/白飛び寄りの明暗設計を明示して分散させる。

## 2026-02-24
- パターン: 新規テンプレートで `templates.text` に書いたプレースホルダ（例: `artistic_styles`）が `elements` 側に未定義でも、`PromptGenerator` は警告のみで生成を続行し、品質低下を見逃しやすい。
- 対策: 追加テンプレートは「プレースホルダ差分チェック（正規表現で抽出）」と「全テンプレート1回生成」をセットで実施し、警告ゼロを確認してからコミットする。
- パターン: pre-commitが一時的なネットワーク障害で失敗した際に `--no-verify` でスキップすると、既存の lint/format 違反が蓄積してしまう。
- 対策: ネットワーク障害でフック取得失敗の場合は `--no-verify` を使わず、障害解消後に `uv run pre-commit run --all-files` を実行して違反を洗い出し、修正してから改めてコミットする。E402（sys.path後のimport）はテストの正当なパターンなので `# noqa: E402` で抑制、B007（未使用ループ変数）は `_` プレフィックスでリネームで解消できる。
