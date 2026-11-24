# Gcalcal for Windows 11

Linux版 `gcalcal` の機能・操作を参考に、Windows 11向けに PySide6 と Google Calendar API で再構築した移植版です。

## 主な機能

- 月間カレンダー（週始まりは日曜日）
- 前月・次月・今日への移動
- 今日・選択日・予定のある日・祝日の表示
- 日付にマウスを合わせると予定タイトルを表示
- 選択日から14日間の予定一覧
- Googleカレンダーの予定取得・追加・削除
- 祝日カレンダーIDを指定した祝日表示
- 15分ごとの自動更新（設定変更可）
- 透過ウィンドウ、最前面表示、タイトルバーなし、ドラッグ移動
- Windowsユーザーごとの設定保存

## 必要環境

- Windows 11 64-bit
- Python 3.10以降（Python 3.12推奨）
- Googleアカウント

## 起動

1. Pythonをインストールします。インストーラーで `Add Python to PATH` を有効にしてください。
2. `run_windows.bat` を実行します。仮想環境を作成し、起動のたびに `requirements.txt` の依存ライブラリを確認・補完します。

依存ライブラリ不足のエラーが出た場合は `repair_dependencies.bat` を実行してください。

またはコマンドプロンプトで次を実行します。

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Google Calendar API の初期設定

このアプリは従来版の `gcalcli` を使わず、Google Calendar API を直接利用します。Google Cloud側でOAuthクライアントを用意する必要があります。

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成または選択します。
2. **Google Calendar API** を有効にします。
3. OAuth同意画面を設定します。個人利用のテスト段階では対象ユーザーに自分のGoogleアカウントを追加してください。
4. 認証情報で **OAuthクライアントID** を作成し、アプリケーションの種類は **デスクトップアプリ** を選択します。
5. JSONをダウンロードします。
6. Gcalcalの「⋯」→「設定」でOAuthクライアントJSONを選択します。
7. 予定カレンダーIDは通常 `primary` で構いません。祝日表示を使う場合は祝日カレンダーIDを指定します。
8. 「⋯」→「Googleアカウントに接続」を選択し、ブラウザーで認証します。

OAuthのアクセストークンは `%APPDATA%\Gcalcal\token.json` に保存されます。認証情報JSONとトークンは配布物に含めないでください。

### カレンダーID

Googleカレンダーの設定画面で対象カレンダーを開き、「カレンダーの統合」にあるカレンダーIDを使用します。祝日カレンダーも同様です。

## EXEの作成

Windows上で `build_exe.bat` を実行してください。PyInstallerでビルドし、`dist\Gcalcal\Gcalcal.exe` を生成します。ビルドはWindows上で行ってください。

## 設定・データ保存先

- 設定: `%APPDATA%\Gcalcal\settings.json`
- OAuthトークン: `%APPDATA%\Gcalcal\token.json`

## 元版からの主な変更

- GTK3 / Glade / Cairo を PySide6 に置き換え
- gcalcliコマンド実行を廃止し、Google Calendar APIへ変更
- Linuxの `~/.config/Gcalcal.xml` をWindowsのAppData JSON設定へ変更
- GTK CSSをQtスタイルシートへ置き換え
- 旧版の画面操作を参考にしつつ、Windows向けのダークUIに再設計

## 注意事項・今後の改善候補

- Google API接続には利用者自身のOAuthクライアントJSONが必要です。
- 祝日カレンダーIDは環境により異なるため、自動決め打ちしていません。
- Google APIの通信は現段階ではUIスレッド上で実行します。大量の予定や通信が遅い環境では画面が一時的に待機する可能性があります。
- 旧版の壁紙ローテーション・個別色設定は、初期移植版では簡略化しています。


## Windows batch file note
The .bat files use ASCII-only text and Windows CRLF line endings to avoid command prompt encoding issues.


予定一覧は初期設定で、Googleアカウントのカレンダーリストにあるすべてのカレンダーから取得します。設定画面で全カレンダー表示をオフにすると、指定したカレンダーIDのみを取得します。


## GitHubへの公開・認証情報の取り扱い

- OAuthクライアントJSON（`client_secret_*.json`）はリポジトリに追加しないでください。
- `token.json`、`.env`、個人用の `settings.json` も公開しないでください。
- OAuthクライアントJSONは各利用者がGoogle Cloud Consoleで作成し、アプリの設定画面から指定します。
- このリポジトリには認証情報そのものを含めていません。
