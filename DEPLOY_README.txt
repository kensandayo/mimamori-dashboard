地域見守り・施策検討支援ツール v10 ヒアリング用公開版

変更点
- AI相談ページをナビゲーションから非表示
- 8_ai_consultation.py / ai_service.py 自体は削除していません
- 後から app.py の該当行の # を外せばAI相談を再表示できます

ローカル起動
1. このフォルダでターミナルを開く
2. pip install -r requirements.txt
3. python -m streamlit run app.py

Streamlit Community Cloudで公開する場合
1. このプロジェクトフォルダをGitHubリポジトリへアップロード
2. Streamlit Community CloudでNew app
3. Main file path に app.py を指定
4. Deploy

注意
- ヒアリング用なので、AI相談は非表示のままにしています
- 施策事例CSVや評価パターン等の既存機能はそのまま残しています
