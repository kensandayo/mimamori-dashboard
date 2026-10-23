# HOU-GA v19.9 一部実データ導入

## 導入内容
- `data/official_care_health_39districts.csv`: 宇都宮市「地域別データ分析ブック」(令和6年3月)の地区別介護関連表から抽出済みの39地区データ。出典表の値を保持。
- `data/official_partial_39districts.csv`: 既存アプリが要求する31列を維持し、`要介護認定率` の39地区分のみ実データに置換。その他の数値と緯度経度は従来のデモ値を保持。
- アプリ起動時は `official_partial_39districts.csv` を標準読み込み。すべての画面にデータ区分の注意を表示。
- 要介護認定率のマスタ登録は元のまま **active=False、weight=0**。そのため、この段階では総合スコアやランキングには実データは反映されません。指標の有効化と重み変更は評価の妥当性を検討してから行ってください。

## 出典と注意
- PDF: `060300zenshi (3).pdf`、宇都宮市『地域別データ分析ブック』令和6年3月、全市域編、冊子14ページの39地区介護健康度表。
- 要介護認定率は令和3年度KDB由来。資料の発行年度と指標の測定年度は異なる。
- 既存の `data/sample_data.csv` はバックアップとして維持。
- `data/official_care_health_39districts.csv` の他の指標は分析画面には未接続。
- `設定・データ管理` の「保存」は元の実装では `data/sample_data.csv` に保存されます。標準データの更新にはGitHub上の `official_partial_39districts.csv` を編集してください。
- Streamlit Community Cloudへの反映には変更ファイルをGitHubにCommit/Pushする必要があります。

## 確認方法
1. `streamlit run app.py` で起動。
2. 画面上部に一部実データの注意書きが出ることを確認。
3. `設定・データ管理` → `データ管理（CSV）` で出典と要介護認定率を確認。
4. 施策の費用・人数・効果は引き続き仮定です。
