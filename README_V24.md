# HOU-GA v24.0

- v23の既存画面・モジュールを保持し、評価重み・パターン保存画面を追加。
- 39地区の公開データから計算する相対比較スコアを提供。効果予測ではありません。
- 保存先: `data/patterns.json`。旧版の未対応パターンは保持し、勝手に変換しません。
- AI相談はアプリ直下の `.env` を明示的に読み込みます。Streamlit secrets、環境変数も対応。
- `.env` を `.env.example` からコピーし、`OPENAI_API_KEY=...` を設定。ZIPには秘密鍵を含めないでください。
- 起動: `pip install -r requirements.txt` → `streamlit run app.py`。
- 注意: Streamlit Cloud等の読み取り専用・再起動される環境ではJSONの永続保存を保証しません。
- API利用にはOpenAI APIの別途契約・利用枠が必要です。APIキーはログや画面に表示しません。
