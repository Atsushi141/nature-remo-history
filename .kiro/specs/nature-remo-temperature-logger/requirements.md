# 要件定義書

## はじめに

本システムは、Nature Remo APIを使用して室温データを10分ごとに取得し、GitHub Actionsを利用して無料で記録するシステムです。GitHub Actionsの無料枠を活用し、温度データを継続的に収集・保存します。

## 用語集

- **System**: 温度記録システム全体
- **Nature_Remo_API**: Nature Remoデバイスから温度データを取得するためのRESTful API
- **GitHub_Actions**: GitHubが提供するCI/CDワークフロー自動化サービス
- **Temperature_Data**: タイムスタンプと温度値を含むデータレコード
- **Data_Store**: 温度データを保存するGitHubリポジトリ内のストレージ（CSVファイルまたはJSON形式）
- **API_Token**: Nature Remo APIへのアクセスに必要な認証トークン
- **GitHub_Secrets**: GitHub Actionsで使用する機密情報を安全に保存する機能
- **Workflow**: GitHub Actionsで実行される自動化タスク

## 要件

### 要件1: API認証とアクセス

**ユーザーストーリー:** システム管理者として、Nature Remo APIに安全にアクセスしたいので、認証情報を適切に管理する必要があります。

#### 受入基準

1. THE System SHALL GitHub_Secretsを使用してAPI_Tokenを保存する
2. WHEN Workflowが実行される時、THE System SHALL GitHub_Secretsから API_Tokenを取得する
3. WHEN API_Tokenが無効または期限切れの場合、THE System SHALL エラーをログに記録し、ワークフローを失敗させる
4. THE System SHALL API_Tokenを平文でログやファイルに出力しない

### 要件2: 温度データの取得

**ユーザーストーリー:** ユーザーとして、現在の室温を正確に取得したいので、Nature Remo APIから最新のデータを読み取る必要があります。

#### 受入基準

1. WHEN Workflowが実行される時、THE System SHALL Nature_Remo_APIにHTTPSリクエストを送信する
2. WHEN APIレスポンスが成功（200 OK）の場合、THE System SHALL 温度データを抽出する
3. WHEN APIレスポンスがエラー（4xx, 5xx）の場合、THE System SHALL エラー内容をログに記録し、リトライを試みる
4. THE System SHALL 取得した温度データにタイムスタンプ（ISO 8601形式）を付与する
5. WHEN APIが応答しない場合、THE System SHALL タイムアウト（30秒）後にエラーを記録する

### 要件3: 定期実行スケジュール

**ユーザーストーリー:** ユーザーとして、10分ごとに自動的に温度を記録したいので、定期的にワークフローを実行する必要があります。

#### 受入基準

1. THE System SHALL GitHub Actionsのcronスケジュールを使用して10分ごとにWorkflowを実行する
2. THE System SHALL GitHub Actionsの無料枠制限内で動作する（月間2000分以内）
3. WHEN スケジュール実行が失敗した場合、THE System SHALL 次回の実行時に再試行する
4. THE System SHALL 手動トリガー（workflow_dispatch）による実行もサポートする

### 要件4: データの保存

**ユーザーストーリー:** ユーザーとして、取得した温度データを長期的に保存したいので、GitHubリポジトリ内にデータを記録する必要があります。

#### 受入基準

1. THE System SHALL Temperature_DataをCSV形式でData_Storeに保存する
2. WHEN 新しいTemperature_Dataが取得された時、THE System SHALL 既存のCSVファイルに新しい行を追加する
3. THE System SHALL CSVファイルのヘッダーとして「timestamp,temperature」を使用する
4. WHEN CSVファイルが存在しない場合、THE System SHALL 新しいファイルを作成する
5. THE System SHALL データ保存後にGitリポジトリにコミットし、プッシュする

### 要件5: エラーハンドリングとログ

**ユーザーストーリー:** システム管理者として、問題が発生した時に原因を特定したいので、適切なエラーハンドリングとログ記録が必要です。

#### 受入基準

1. WHEN エラーが発生した場合、THE System SHALL エラーメッセージ、タイムスタンプ、エラータイプをログに記録する
2. WHEN API呼び出しが失敗した場合、THE System SHALL 最大3回までリトライする
3. WHEN リトライが全て失敗した場合、THE System SHALL ワークフローを失敗ステータスで終了する
4. THE System SHALL GitHub Actionsのログ機能を使用してすべての実行履歴を記録する
5. WHEN データ保存に失敗した場合、THE System SHALL エラーを記録し、データを失わないようにする

### 要件6: データの整合性

**ユーザーストーリー:** ユーザーとして、記録されたデータが正確で信頼できることを確認したいので、データの検証が必要です。

#### 受入基準

1. THE System SHALL 取得した温度値が数値であることを検証する
2. THE System SHALL 温度値が妥当な範囲（-50℃〜50℃）内であることを確認する
3. WHEN 温度値が範囲外の場合、THE System SHALL 警告をログに記録するが、データは保存する
4. THE System SHALL 重複したタイムスタンプのデータを保存しない
5. THE System SHALL CSVファイルの形式が正しいことを保存前に検証する

### 要件7: コスト管理

**ユーザーストーリー:** ユーザーとして、システムを無料で運用したいので、GitHub Actionsの無料枠内で動作する必要があります。

#### 受入基準

1. THE System SHALL パブリックリポジトリを使用する場合、無制限の実行時間を利用できる
2. THE System SHALL プライベートリポジトリを使用する場合、月間2000分の制限内で動作する
3. THE System SHALL 1回のワークフロー実行時間を5分以内に抑える
4. THE System SHALL 不要なステップや処理を含まない効率的なワークフローを実装する

### 要件8: 設定の柔軟性

**ユーザーストーリー:** ユーザーとして、システムの設定を簡単に変更したいので、設定可能なパラメータを提供する必要があります。

#### 受入基準

1. WHERE ユーザーが実行間隔を変更したい場合、THE System SHALL cronスケジュールの変更をサポートする
2. WHERE ユーザーが保存形式を変更したい場合、THE System SHALL CSV以外の形式（JSON）もサポートする
3. THE System SHALL 設定ファイルまたは環境変数を通じて設定を変更可能にする
4. THE System SHALL デフォルト設定で動作可能である

### 要件9: データの可視化準備

**ユーザーストーリー:** ユーザーとして、記録したデータを後で分析・可視化したいので、標準的な形式でデータを保存する必要があります。

#### 受入基準

1. THE System SHALL 保存するデータ形式を機械可読可能な形式（CSV、JSON）にする
2. THE System SHALL タイムスタンプをISO 8601形式で保存する
3. THE System SHALL 温度値を小数点以下1桁まで保存する
4. THE System SHALL データファイルにBOM（Byte Order Mark）を含めない
