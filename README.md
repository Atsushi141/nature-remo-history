# Nature Remo 温度記録システム

Nature Remo APIを使用して10分ごとに室温を記録し、GitHub Actionsで自動実行するシステムです。データはCSV形式でGitHubリポジトリに保存され、長期的な温度履歴の記録と分析を可能にします。

## 特徴

- 🆓 完全無料（GitHub Actionsの無料枠を活用）
- 🔄 10分ごとの自動実行
- 📊 CSV形式でのデータ保存
- 🔒 GitHub Secretsによる安全な認証情報管理
- 📈 長期的な温度履歴の記録

## セットアップ手順

### 1. リポジトリのフォーク/クローン

このリポジトリをフォークするか、クローンしてください。

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Nature Remo APIトークンの取得

1. [Nature Remo Cloud](https://home.nature.global/) にアクセス
2. ログイン後、右上のメニューから「API Settings」を選択
3. 「Generate Access Token」をクリックしてトークンを生成
4. 生成されたトークンをコピー（このトークンは一度しか表示されません）

### 3. GitHub Secretsの設定

**重要**: APIトークンを安全に保管するため、GitHub Secretsを使用します。

#### 設定手順:

1. GitHubリポジトリのページを開く
2. 「Settings」タブをクリック
3. 左サイドバーの「Secrets and variables」→「Actions」を選択
4. 「New repository secret」ボタンをクリック
5. 以下の情報を入力:
   - **Name**: `NATURE_REMO_TOKEN`
   - **Secret**: 手順2で取得したAPIトークンを貼り付け
6. 「Add secret」をクリック


### 4. GitHub Actionsの有効化

1. リポジトリの「Actions」タブを開く
2. ワークフローの実行を許可する
3. 「Temperature Logger」ワークフローが表示されることを確認

### 5. 動作確認

#### 手動実行でテスト:

1. 「Actions」タブを開く
2. 左サイドバーから「Temperature Logger」を選択
3. 「Run workflow」ボタンをクリック
4. ワークフローが正常に完了することを確認
5. `data/temperature.csv` ファイルが作成され、データが記録されていることを確認

#### 自動実行の確認:

- ワークフローは10分ごとに自動実行されます
- 「Actions」タブで実行履歴を確認できます

## 使用方法

### ローカルでの実行

環境変数を設定してローカルで実行することもできます:

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
export NATURE_REMO_TOKEN="your-api-token-here"

# スクリプトの実行
python logger.py
```

### データの確認

温度データは `data/temperature.csv` に保存されます:

```csv
timestamp,temperature
2024-01-01T00:00:00+09:00,25.5
2024-01-01T00:10:00+09:00,25.3
2024-01-01T00:20:00+09:00,25.4
```

## プロジェクト構造

```
.
├── .github/
│   └── workflows/
│       └── temperature-logger.yml  # GitHub Actionsワークフロー
├── data/
│   └── temperature.csv             # 温度データ（自動生成）
├── tests/
│   ├── unit/                       # ユニットテスト
│   └── property/                   # プロパティベーステスト
├── logger.py                       # メインスクリプト
├── requirements.txt                # Python依存関係
└── README.md                       # このファイル
```

## トラブルシューティング

### ワークフローが失敗する

**症状**: GitHub Actionsのワークフローが失敗する

**確認事項**:
1. `NATURE_REMO_TOKEN` が正しく設定されているか確認
2. APIトークンが有効期限内か確認
3. Nature Remo デバイスがオンラインか確認
4. Actions タブのログで詳細なエラーメッセージを確認

### APIトークンエラー

**症状**: `401 Unauthorized` エラーが発生

**解決方法**:
1. Nature Remo Cloudで新しいトークンを生成
2. GitHub Secretsの `NATURE_REMO_TOKEN` を更新
3. ワークフローを再実行

### データが記録されない

**症状**: CSVファイルが更新されない

**確認事項**:
1. ワークフローが正常に完了しているか確認
2. logger.py が正常に実行されているか確認
3. エラーログを確認

### レート制限エラー

**症状**: `429 Too Many Requests` エラーが発生

**解決方法**:
- Nature Remo APIのレート制限は5分間に30リクエスト
- 10分ごとの実行では通常問題ありませんが、手動実行を頻繁に行うと制限に達する可能性があります
- 時間をおいてから再実行してください

## テスト

```bash
# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit/

# プロパティテストのみ
pytest tests/property/

# カバレッジレポート付き
pytest --cov=logger --cov-report=html
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 参考リンク

- [Nature Remo Cloud API ドキュメント](https://developer.nature.global/)
- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
- [GitHub Secrets の使用方法](https://docs.github.com/ja/actions/security-guides/encrypted-secrets)
