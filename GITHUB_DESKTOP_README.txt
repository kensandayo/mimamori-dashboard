【GitHub Desktopへの反映手順】

1. GitHub Desktopで、いつもの見守りシステムのリポジトリを開く
2. Repository → Show in Explorer を押す
3. このv18.4フォルダの「中身」を、そのリポジトリへ上書きコピーする
4. APIキーを使うPCでは .env.example をコピーして .env を作成する
5. .env に本物の OPENAI_API_KEY を入力する
6. GitHub DesktopのChangesを確認する
   ※ .env がChangesに出ていたら絶対にコミットしない
7. Summary例: Update to v18.4
8. Commit to main → Push origin

推奨：Push前に、GitHub DesktopのChangesに「.env」「secrets.toml」が無いことを確認してください。
