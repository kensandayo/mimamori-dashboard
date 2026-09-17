【AI相談機能：ローカル / GitHub Desktop 用設定】

1. プロジェクト直下の「.env.example」をコピーする
2. コピーしたファイル名を「.env」に変更する
3. .env を開いて次の行を書き換える

   OPENAI_API_KEY=sk-自分のAPIキー

4. ターミナルで依存関係を入れる

   pip install -r requirements.txt

5. Streamlitを起動する

   streamlit run app.py

【重要】
・本物のAPIキーは .env にだけ書いてください。
・.env は .gitignore に登録済みなのでGitHub DesktopのChangesには通常表示されません。
・.env.example は見本なのでGitHubへコミットしてOKです。
・APIキーを app.py / ai_service.py / README / .env.example に直接書かないでください。

【Streamlit Community Cloudで公開する場合】
公開環境ではローカルの .env はGitHubへ送られないため、Streamlit側のSecretsに以下を設定します。

OPENAI_API_KEY = "sk-自分のAPIキー"
OPENAI_MODEL = "gpt-5.6-luna"
DAILY_AI_LIMIT = "50"
