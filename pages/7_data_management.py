# -*- coding: utf-8 -*-
"""
settings.py (pages/)
----------------------
以下2つの機能を提供する画面です。

1. スコア計算の重み変更（スライダー、合計値を表示）→ 変更すると地図・ランキング・
   スコアなど全画面が自動的に再計算される
2. データ管理（CSVアップロード・画面上での編集・入力チェック・CSVダウンロード、
   現在使用しているデータ出典／対象年度／更新日の表示）
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from utils.config import DEFAULT_WEIGHTS, REQUIRED_COLUMNS
from utils.state import (
    get_raw_data, set_raw_data, get_weights, set_weights,
    get_data_source_info, reset_to_default_data,
)
from utils.data_loader import read_uploaded_csv, dataframe_to_csv_bytes, save_dataframe_to_csv
from utils.validation import validate_dataframe
from components.header import render_header, render_footer
from components.cards import render_info_strip


@st.dialog("上書き保存の確認")
def _confirm_save_dialog(df_to_save) -> None:
    """
    「data/sample_data.csv への保存」を実行する前の確認ダイアログです。
    ここで「保存する」を押すまでは、ファイルへの書き込みは一切行われません。
    """
    st.write("現在のデータを **data/sample_data.csv** に上書き保存します。")
    st.caption(
        "保存すると、次回アプリを起動したときも今の内容が自動的に読み込まれます。"
        "元のファイルの内容は上書きされ、元に戻せませんのでご注意ください。"
    )
    st.write(f"保存対象：{len(df_to_save)} 件の地区データ")

    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("保存する", type="primary", use_container_width=True):
            # 保存の直前にもう一度バリデーションを行い、不正なデータの書き込みを防ぐ
            is_valid, errors = validate_dataframe(df_to_save)
            if not is_valid:
                st.session_state["_save_result"] = {"ok": False, "errors": errors}
            else:
                save_dataframe_to_csv(df_to_save)
                # 保存日を今日の日付で更新し、画面表示にも反映する
                set_raw_data(
                    df_to_save,
                    source_name="手動保存データ（data/sample_data.csv に保存済み）",
                    updated_at=date.today().isoformat(),
                )
                st.session_state["_save_result"] = {"ok": True, "errors": []}
            st.rerun()
    with col_cancel:
        if st.button("キャンセル", use_container_width=True):
            st.rerun()


st.title("設定・データ管理")
render_header()

tab_weight, tab_data = st.tabs(["重みの設定", "データ管理（CSV）"])

# ============================================================
# 重みの設定
# ============================================================
with tab_weight:
    st.markdown("#### スコア計算に使う重みを設定してください")
    st.caption("重みを変更すると、地図・ランキング・スコアなど全画面が自動的に再計算されます。合計は100%にしてください。")

    current_weights = get_weights()

    w1 = st.slider("高齢化率の重み(%)", 0, 100, int(current_weights["aging"] * 100))
    w2 = st.slider("単身高齢者割合の重み(%)", 0, 100, int(current_weights["single_elderly"] * 100))
    w3 = st.slider("医療アクセスの重み(%)", 0, 100, int(current_weights["medical"] * 100))
    w4 = st.slider("公共交通の重み(%)", 0, 100, int(current_weights["transport"] * 100))

    total = w1 + w2 + w3 + w4
    st.metric("現在の合計", f"{total}%")
    if total != 100:
        st.error(f"合計が100%になるように調整してください（現在 {total}%）。")
    else:
        st.success("合計は100%です。")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("この重みを適用する", type="primary", disabled=(total != 100)):
            set_weights({
                "aging": w1 / 100,
                "single_elderly": w2 / 100,
                "medical": w3 / 100,
                "transport": w4 / 100,
            })
            st.success("重みを更新しました。他の画面にも即時反映されます。")
    with col_b:
        if st.button("初期値（30/30/20/20）に戻す"):
            set_weights(dict(DEFAULT_WEIGHTS))
            st.success("重みを初期値に戻しました。")
            st.rerun()

# ============================================================
# データ管理（CSVアップロード・編集・ダウンロード）
# ============================================================
with tab_data:
    # 保存ダイアログでの操作結果（成功／失敗）を、ダイアログが閉じた直後に表示する
    save_result = st.session_state.pop("_save_result", None)
    if save_result is not None:
        if save_result["ok"]:
            st.success("保存が完了しました。")
        else:
            st.error("CSVの形式が不正なため保存できませんでした。以下の列を確認してください。")
            for e in save_result["errors"]:
                st.write(f"❌ {e}")

    source_info = get_data_source_info()
    st.markdown("#### 現在使用しているデータ")
    render_info_strip([
        {"label": "データ出典", "value": source_info["source_name"]},
        {"label": "対象年度", "value": source_info["target_year"]},
        {"label": "更新日", "value": source_info["updated_at"]},
    ])

    st.markdown("---")
    st.markdown("#### CSVアップロード")
    st.caption("以下の列を持つCSVファイルをアップロードしてください： " + "、".join(REQUIRED_COLUMNS))

    uploaded_file = st.file_uploader("CSVファイルを選択", type=["csv"])

    if uploaded_file is not None:
        try:
            new_df = read_uploaded_csv(uploaded_file)
            is_valid, errors = validate_dataframe(new_df)
            if is_valid:
                set_raw_data(new_df, source_name=f"アップロードデータ（{uploaded_file.name}）")
                st.success("CSVを読み込み、データを更新しました。")
            else:
                st.error("CSVの内容に問題があります。以下のエラーを確認してください。")
                for e in errors:
                    st.write(f"❌ {e}")
        except ValueError as e:
            st.error(str(e))

    st.markdown("---")
    st.markdown("#### 画面上でデータを編集")
    st.caption("表を直接編集できます。編集後は自動的に入力チェック・再計算が行われます。")

    df = get_raw_data()
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="data_editor",
    )

    is_valid, errors = validate_dataframe(edited_df)
    if not is_valid:
        st.error("入力内容に以下の問題があります。修正してください（修正されるまで前回の正常なデータが使用されます）。")
        for e in errors:
            st.write(f"❌ {e}")
    else:
        if not edited_df.equals(df):
            set_raw_data(edited_df)
            st.success("編集内容を反映しました。")

    st.markdown("---")
    st.markdown("#### データの永続保存")
    st.caption(
        "上の「反映」はこのセッション（ブラウザを開いている間）だけの一時的な変更です。"
        "アプリを再起動しても内容を残したい場合は、下のボタンで data/sample_data.csv に保存してください。"
    )
    if st.button("💾 data/sample_data.csv へ保存", type="primary"):
        _confirm_save_dialog(get_raw_data())

    st.markdown("---")
    col_dl, col_reset = st.columns(2)
    with col_dl:
        st.download_button(
            "📥 現在のデータをCSVでダウンロード",
            data=dataframe_to_csv_bytes(get_raw_data()),
            file_name="mimamori_data.csv",
            mime="text/csv",
        )
    with col_reset:
        if st.button("🔄 標準データ（data/sample_data.csv）に戻す"):
            reset_to_default_data()
            st.success("標準データに戻しました。")
            st.rerun()

render_footer()
