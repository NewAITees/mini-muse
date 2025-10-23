# Event Viewer エラー分析プロジェクト 引継ぎ資料

**作成日**: 2025-10-21
**対象環境**: Windows (WSL2経由でアクセス可能)
**目的**: Event Viewerのエラーログを自動取得・分析し、解決可能な問題を特定・解消する

---

## 1. プロジェクト概要

### 1.1 目的
Windows Event Viewerに記録されているエラーログを定期的に取得・分析し、システムの健全性を維持する。

### 1.2 作業フロー
```
[Event Viewer]
    ↓ (エラー取得)
[テキストファイル出力]
    ↓ (読み込み)
[Claude による分析]
    ↓ (解決策提案)
[ユーザー確認]
    ↓ (実行)
[エラー解消]
```

---

## 2. Event Viewer エラー取得方法

### 2.1 対象ログ
- **System**: システム関連のエラー
- **Application**: アプリケーション関連のエラー
- **Security**: セキュリティ関連のエラー（必要に応じて）

### 2.2 取得対象レベル
- **Error** (Level 2): エラー
- **Critical** (Level 1): 重大なエラー

---

## 3. スクリプト実装

### 3.1 PowerShellスクリプト版

**ファイル名**: `Get-EventViewerErrors.ps1`

```powershell
# Event Viewer エラー取得スクリプト
# 使用方法: powershell.exe -ExecutionPolicy Bypass -File Get-EventViewerErrors.ps1

# 出力ファイル名（タイムスタンプ付き）
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = "event_errors_$timestamp.txt"

# ヘッダー出力
"=" * 80 | Out-File $outputFile -Encoding UTF8
"Windows Event Viewer エラーログ" | Out-File $outputFile -Append -Encoding UTF8
"取得日時: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $outputFile -Append -Encoding UTF8
"=" * 80 | Out-File $outputFile -Append -Encoding UTF8
"`n" | Out-File $outputFile -Append -Encoding UTF8

# 取得期間（過去24時間）
$startTime = (Get-Date).AddHours(-24)

# ログの種類
$logNames = @("System", "Application")

foreach ($logName in $logNames) {
    "`n" + "=" * 80 | Out-File $outputFile -Append -Encoding UTF8
    "ログ種類: $logName" | Out-File $outputFile -Append -Encoding UTF8
    "=" * 80 | Out-File $outputFile -Append -Encoding UTF8
    "`n" | Out-File $outputFile -Append -Encoding UTF8

    # エラーレベル（Error=2, Critical=1）を取得
    $events = Get-WinEvent -FilterHashtable @{
        LogName = $logName
        Level = 1,2
        StartTime = $startTime
    } -ErrorAction SilentlyContinue | Select-Object -First 100

    if ($events) {
        $count = 0
        foreach ($event in $events) {
            $count++
            "-" * 80 | Out-File $outputFile -Append -Encoding UTF8
            "[$count] イベントID: $($event.Id)" | Out-File $outputFile -Append -Encoding UTF8
            "レベル: $($event.LevelDisplayName)" | Out-File $outputFile -Append -Encoding UTF8
            "ソース: $($event.ProviderName)" | Out-File $outputFile -Append -Encoding UTF8
            "日時: $($event.TimeCreated)" | Out-File $outputFile -Append -Encoding UTF8
            "メッセージ:" | Out-File $outputFile -Append -Encoding UTF8
            "$($event.Message)" | Out-File $outputFile -Append -Encoding UTF8
            "`n" | Out-File $outputFile -Append -Encoding UTF8
        }
        "合計: $count 件のエラー" | Out-File $outputFile -Append -Encoding UTF8
    } else {
        "エラーは見つかりませんでした。" | Out-File $outputFile -Append -Encoding UTF8
    }
}

"`n" + "=" * 80 | Out-File $outputFile -Append -Encoding UTF8
"取得完了" | Out-File $outputFile -Append -Encoding UTF8
"=" * 80 | Out-File $outputFile -Append -Encoding UTF8

Write-Host "エラーログを $outputFile に出力しました。"
```

### 3.2 Python スクリプト版

**ファイル名**: `event_viewer_errors.py`

```python
#!/usr/bin/env python3
"""
Event Viewer エラー取得スクリプト
Windows Event Viewerから過去24時間のエラーログを取得し、テキストファイルに出力する
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_event_logs(log_name: str, max_events: int = 100) -> str:
    """
    PowerShellを使用してEvent Viewerからエラーログを取得

    Args:
        log_name: ログ名（System, Application等）
        max_events: 最大取得件数

    Returns:
        エラーログのテキスト
    """
    # PowerShellコマンド（過去24時間のエラー・重大なエラーを取得）
    ps_command = f"""
    $startTime = (Get-Date).AddHours(-24)
    $events = Get-WinEvent -FilterHashtable @{{
        LogName = '{log_name}'
        Level = 1,2
        StartTime = $startTime
    }} -ErrorAction SilentlyContinue | Select-Object -First {max_events}

    if ($events) {{
        $count = 0
        foreach ($event in $events) {{
            $count++
            Write-Output ('-' * 80)
            Write-Output "[$count] イベントID: $($event.Id)"
            Write-Output "レベル: $($event.LevelDisplayName)"
            Write-Output "ソース: $($event.ProviderName)"
            Write-Output "日時: $($event.TimeCreated)"
            Write-Output "メッセージ:"
            Write-Output "$($event.Message)"
            Write-Output ""
        }}
        Write-Output "合計: $count 件のエラー"
    }} else {{
        Write-Output "エラーは見つかりませんでした。"
    }}
    """

    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"タイムアウト: {log_name} ログの取得に失敗しました。"
    except Exception as e:
        return f"エラー: {log_name} ログの取得に失敗しました。\n{str(e)}"


def main():
    """メイン処理"""
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"event_errors_{timestamp}.txt")

    print(f"Event Viewer エラーログを取得中...")
    print(f"出力先: {output_file}")

    # ログの種類
    log_names = ["System", "Application"]

    with open(output_file, "w", encoding="utf-8") as f:
        # ヘッダー
        f.write("=" * 80 + "\n")
        f.write("Windows Event Viewer エラーログ\n")
        f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # 各ログを取得
        for log_name in log_names:
            print(f"  - {log_name} ログを取得中...")

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"ログ種類: {log_name}\n")
            f.write("=" * 80 + "\n\n")

            log_content = get_event_logs(log_name)
            f.write(log_content)
            f.write("\n")

        # フッター
        f.write("\n" + "=" * 80 + "\n")
        f.write("取得完了\n")
        f.write("=" * 80 + "\n")

    print(f"✓ エラーログを {output_file} に出力しました。")
    print(f"\n次のステップ:")
    print(f"  1. {output_file} をClaudeに読み込ませる")
    print(f"  2. エラーの分析を依頼する")
    print(f"  3. 解決可能なエラーの対処を進める")


if __name__ == "__main__":
    main()
```

---

## 4. 実行方法

### 4.1 WSL2環境から実行（Pythonスクリプト）

```bash
# スクリプトに実行権限を付与
chmod +x event_viewer_errors.py

# 実行
python event_viewer_errors.py
```

### 4.2 Windows環境から実行（PowerShellスクリプト）

```powershell
# PowerShellを管理者権限で起動し、実行
powershell.exe -ExecutionPolicy Bypass -File Get-EventViewerErrors.ps1
```

### 4.3 出力ファイル

実行すると、以下の形式でファイルが生成されます：
```
event_errors_20251021_143052.txt
```

---

## 5. Claude による分析フロー

### 5.1 分析依頼の手順

1. **出力ファイルを読み込む**
   ```
   「event_errors_YYYYMMDD_HHMMSS.txt を分析してください」
   ```

2. **Claudeが実施する分析内容**
   - エラーの種類と頻度の集計
   - 重大度の評価
   - 関連するエラーのグループ化
   - 既知の問題かどうかの判定
   - 解決可能性の評価

3. **解決策の提案**
   - 各エラーに対する具体的な解決方法
   - 実行すべきコマンド
   - 設定変更の手順
   - 優先順位の提示

4. **ユーザー確認**
   - 提案された解決策を確認
   - 実行するかどうかを判断（y/n）

5. **実行と検証**
   - 承認された解決策を実行
   - 結果の確認
   - 再度エラーログを取得して改善を確認

---

## 6. 分析時の注意事項

### 6.1 エラー分類

- **無視可能なエラー**: 既知で影響のないもの
- **要監視エラー**: 頻度や状況を監視すべきもの
- **即時対応エラー**: すぐに対処が必要なもの

### 6.2 解決の優先順位

1. **Critical（重大）**: システムクラッシュ、データ損失の可能性
2. **Error（高）**: 機能不全、パフォーマンス低下
3. **Error（中）**: 特定機能の問題
4. **Error（低）**: 軽微な問題、警告レベル

### 6.3 解決前の確認事項

- システム再起動が必要か
- データバックアップが必要か
- 他のプロセスへの影響はあるか
- ロールバック方法は準備されているか

---

## 7. 定期実行の設定（オプション）

### 7.1 Windowsタスクスケジューラで定期実行

```powershell
# 毎日午前2時に実行するタスクを作成
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\path\to\Get-EventViewerErrors.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "EventViewerErrorCollection" -Description "毎日Event Viewerのエラーを収集"
```

### 7.2 WSL2のcronで定期実行

```bash
# crontabを編集
crontab -e

# 毎日午前2時に実行（以下を追加）
0 2 * * * /usr/bin/python3 /path/to/event_viewer_errors.py
```

---

## 8. トラブルシューティング

### 8.1 PowerShell実行ポリシーエラー

**エラー**: "このシステムではスクリプトの実行が無効になっているため..."

**解決策**:
```powershell
# 管理者権限でPowerShellを起動
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 8.2 アクセス許可エラー

**エラー**: "アクセスが拒否されました"

**解決策**:
- PowerShellまたはコマンドプロンプトを管理者権限で実行
- Securityログにアクセスする場合は特に必要

### 8.3 WSL2からPowerShellが実行できない

**確認事項**:
```bash
# PowerShellが実行可能か確認
powershell.exe -Command "Write-Host 'Test'"

# パスが通っているか確認
which powershell.exe
```

---

## 9. 参考情報

### 9.1 Event Viewer の主要なイベントID

| イベントID | ログ | 内容 |
|-----------|------|------|
| 1001 | System | Windows Error Reporting |
| 7000 | System | サービス起動失敗 |
| 7001 | System | サービス依存関係エラー |
| 10016 | System | DCOM権限エラー |
| 1000 | Application | アプリケーションクラッシュ |
| 1002 | Application | アプリケーションハング |

### 9.2 有用なコマンド

```powershell
# 特定のイベントIDのみ取得
Get-WinEvent -FilterHashtable @{LogName='System'; ID=7000}

# 特定のソースのみ取得
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'}

# XMLフォーマットで詳細取得
Get-WinEvent -LogName System -MaxEvents 10 | Format-List *
```

---

## 10. 次のステップ

1. ✅ この引継ぎ資料を確認
2. ⬜ スクリプトを実行してエラーログを取得
3. ⬜ 出力ファイルをClaude（別セッション）に読み込ませる
4. ⬜ エラー分析を依頼
5. ⬜ 解決策を実行
6. ⬜ 改善を確認

---

## 11. 連絡事項

- このドキュメントは `/home/perso/analysis/mini-muse/` に保存されています
- 別プロジェクト（Event Viewer分析用）で使用してください
- AI運用5原則に従って作業を進めてください
- 不明点があれば、このドキュメントを参照しながら確認してください

**作成者**: Claude (mini-muse プロジェクト環境)
**引継ぎ先**: Claude (Event Viewer分析プロジェクト環境)
