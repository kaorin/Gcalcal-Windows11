# GitHub公開前の注意

このソース一式はOAuthクライアントJSONを除外してあります。

## 公開前チェック
- `client_secret_*.json` が含まれていないこと
- `token.json` が含まれていないこと
- 個人用 `settings.json` が含まれていないこと
- `.gitignore` が有効であること

各利用者は自分のGoogle Cloudプロジェクトでデスクトップアプリ用OAuthクライアントJSONを作成し、Gcalcalの設定画面から指定してください。

もし過去にOAuthクライアントJSONを公開リポジトリへpushした場合、ファイルを削除するだけではGit履歴に残る可能性があります。Google Cloud Consoleで該当OAuthクライアントを削除・再作成し、必要に応じてGit履歴からも除去してください。
