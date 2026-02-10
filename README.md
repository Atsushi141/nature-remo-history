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

### 3. GitHub Environment と Secrets の設定

**重要**: APIトークンを安全に保管するため、GitHub Environment Secretsを使用します。

#### Environment の作成:

1. GitHubリポジトリのページを開く
2. 「Settings」タブをクリック
3. 左サイドバーの「Environments」を選択
4. 「New environment」ボタンをクリック
5. Environment name に `production` と入力
6. 「Configure environment」をクリック

#### Environment Secret の設定:

1. 作成した `production` environment のページで、「Add secret」をクリック
2. 以下の情報を入力:
   - **Name**: `NATURE_REMO_TOKEN`
   - **Secret**: 手順2で取得したAPIトークンを貼り付け
3. 「Add secret」をクリック


### 4. GitHub Actionsの有効化と権限設定

1. リポジトリの「Actions」タブを開く
2. ワークフローの実行を許可する
3. 「Temperature Logger」ワークフローが表示されることを確認

**重要**: ワークフローがデータをコミット・プッシュできるように、以下の権限設定を確認してください:

1. リポジトリの「Settings」→「Actions」→「General」を開く
2. 「Workflow permissions」セクションで以下を選択:
   - 「Read and write permissions」を選択
   - 「Allow GitHub Actions to create and approve pull requests」にチェック（オプション）
3. 「Save」をクリック

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
1. `production` environment に `NATURE_REMO_TOKEN` が正しく設定されているか確認
2. APIトークンが有効期限内か確認
3. Nature Remo デバイスがオンラインか確認
4. Actions タブのログで詳細なエラーメッセージを確認

### APIトークンエラー

**症状**: `401 Unauthorized` エラーが発生

**解決方法**:
1. Nature Remo Cloudで新しいトークンを生成
2. GitHub の `production` environment の `NATURE_REMO_TOKEN` を更新
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

### Git Push 権限エラー

**症状**: `Permission denied to github-actions[bot]` または `403 error` が発生

**解決方法**:
1. リポジトリの「Settings」→「Actions」→「General」を開く
2. 「Workflow permissions」で「Read and write permissions」を選択
3. 「Save」をクリック
4. ワークフローを再実行

### Cron スケジュールが実行されない

**症状**: 定期実行が動作しない、またはスケジュール通りに実行されない

**原因と解決方法**:

1. **リポジトリの活動が少ない**
   - GitHubは非アクティブなリポジトリのcronを自動的に無効化します
   - 解決策: 定期的に手動実行するか、リポジトリに活動を持たせる

2. **実行の遅延**
   - GitHub Actionsのcronは正確な時刻に実行されません
   - 高負荷時は数分〜数十分遅延することがあります
   - 解決策: 遅延を許容する設計にする

3. **デフォルトブランチの確認**
   - ワークフローファイルがデフォルトブランチ（main/master）に存在することを確認
   - 解決策: `git push origin main` でデフォルトブランチにプッシュ

4. **60日間の非活動で無効化**
   - 60日間リポジトリに活動がないとcronが無効化されます
   - 解決策: 定期的に手動実行するか、コミットを行う

**推奨される対策**:
- 手動実行（workflow_dispatch）を定期的に使用する
- より長い間隔（15分、30分、1時間など）に変更する
- 外部のcronサービス（GitHub API経由でworkflow_dispatchをトリガー）を使用する

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

## 代替案: 外部Cronサービスの使用

GitHub Actionsのcronスケジュールが不安定な場合、外部サービスを使用してワークフローをトリガーできます。

### 方法1: cron-job.org を使用

1. [cron-job.org](https://cron-job.org/) にアクセス
2. アカウントを作成（無料）
3. 新しいcron jobを作成:
   - URL: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/temperature-logger.yml/dispatches`
   - Method: POST
   - Headers:
     ```
     Authorization: Bearer YOUR_GITHUB_TOKEN
     Accept: application/vnd.github.v3+json
     ```
   - Body:
     ```json
     {"ref":"main"}
     ```
   - Schedule: 10分ごと

### 方法2: GitHub Personal Access Token の作成

外部サービスからワークフローをトリガーするには、Personal Access Tokenが必要です：

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token」をクリック
3. Scopes: `repo` と `workflow` を選択
4. トークンを生成してコピー
5. 外部cronサービスで使用

### 方法3: 自前のサーバーでcronを実行

```bash
# crontabに追加
*/10 * * * * curl -X POST \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/temperature-logger.yml/dispatches \
  -d '{"ref":"main"}'
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 参考リンク

- [Nature Remo Cloud API ドキュメント](https://developer.nature.global/)
- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
- [GitHub Environments の使用方法](https://docs.github.com/ja/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Environment Secrets の設定](https://docs.github.com/ja/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-an-environment)
