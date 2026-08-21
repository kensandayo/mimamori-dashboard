# -*- coding: utf-8 -*-
"""
data_management.py (pages/)
------------------------------
以下4つの機能を提供する画面です。

1. 重みの設定（動的：マスタに登録された評価項目の分だけスライダーが並ぶ）
2. データ管理（CSVアップロード・画面編集・入力チェック・保存・ダウンロード）
3. 評価項目管理（評価項目の追加・編集・削除。ここがコードを直さず指標を
   増減できるようにするための画面です）
4. 評価パターン管理（現在の重みをパターンとして保存・適用・削除）
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.config import COL_NAME
from utils.state import (
    get_raw_data, set_raw_data, get_weights, set_weights,
    get_data_source_info, reset_to_default_data, apply_pattern, get_current_pattern_name,
)
from utils.data_loader import read_uploaded_csv, dataframe_to_csv_bytes, save_dataframe_to_csv
from utils.validation import validate_dataframe
from utils.parameter_loader import (
    load_all_parameters, get_default_weights, add_parameter, delete_parameter, save_all_parameters,
)
from utils.patterns import load_patterns, save_pattern, delete_pattern
from components.header import render_header, render_footer
from components.cards import render_info_strip


@st.dialog("上書き保存の確認")
def _confirm_save_dialog(df_to_save) -> None:
    st.write("現在のデータを **data/sample_data.csv** に上書き保存します。")
    st.caption("保存すると、次回アプリを起動したときも今の内容が自動的に読み込まれます。元のファイルの内容は上書きされ、元に戻せませんのでご注意ください。")
    st.write(f"保存対象：{len(df_to_save)} 件の地区データ")
    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("保存する", type="primary", use_container_width=True):
            is_valid, errors = validate_dataframe(df_to_save)
            if not is_valid:
                st.session_state["_save_result"] = {"ok": False, "errors": errors}
            else:
                save_dataframe_to_csv(df_to_save)
                set_raw_data(df_to_save, source_name="手動保存データ（data/sample_data.csv に保存済み）",
                             updated_at=date.today().isoformat())
                st.session_state["_save_result"] = {"ok": True, "errors": []}
            st.rerun()
    with col_cancel:
        if st.button("キャンセル", use_container_width=True):
            st.rerun()


st.title("設定・データ管理")
render_header()

tab_weight, tab_data, tab_params, tab_patterns = st.tabs(
    ["重みの設定", "データ管理（CSV）", "評価項目管理", "評価パターン管理"]
)

# ============================================================
# 1. 重みの設定（動的）
# ============================================================
with tab_weight:
    active_params = load_all_parameters()
    active_params = [p for p in active_params if p["active"]]

    st.markdown("#### スコア計算に使う重みを設定してください")
    st.caption("重みを変更すると、地図・ランキング・スコアなど全画面が自動的に再計算されます。合計は100%にしてください。")

    current_weights = get_weights()
    new_weights_pct = {}
    for p in active_params:
        current_pct = int(round(current_weights.get(p["weight_key"], 0) * 100))
        new_weights_pct[p["weight_key"]] = st.slider(f"{p['label']}の重み(%)", 0, 100, current_pct, key=f"w_{p['weight_key']}")

    total = sum(new_weights_pct.values())
    st.metric("現在の合計", f"{total}%")
    if total != 100:
        st.error(f"合計が100%になるように調整してください（現在 {total}%）。")
    else:
        st.success("合計は100%です。")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("この重みを適用する", type="primary", disabled=(total != 100)):
            set_weights({k: v / 100 for k, v in new_weights_pct.items()})
            st.success("重みを更新しました。他の画面にも即時反映されます。")
    with col_b:
        if st.button("マスタの初期値に戻す"):
            set_weights(get_default_weights())
            st.success("重みをマスタの初期値に戻しました。")
            st.rerun()

# ============================================================
# 2. データ管理（CSVアップロード・編集・保存・ダウンロード）
# ============================================================
with tab_data:
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
    from utils.parameter_loader import get_required_columns
    st.caption("以下の列を持つCSVファイルをアップロードしてください： " + "、".join(get_required_columns()))

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
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True, key="data_editor")

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
    st.caption("上の「反映」はこのセッションだけの一時的な変更です。アプリを再起動しても内容を残したい場合は、下のボタンで保存してください。")
    if st.button("💾 data/sample_data.csv へ保存", type="primary"):
        _confirm_save_dialog(get_raw_data())

    st.markdown("---")
    col_dl, col_reset = st.columns(2)
    with col_dl:
        st.download_button("📥 現在のデータをCSVでダウンロード", data=dataframe_to_csv_bytes(get_raw_data()),
                           file_name="mimamori_data.csv", mime="text/csv")
    with col_reset:
        if st.button("🔄 標準データ（data/sample_data.csv）に戻す"):
            reset_to_default_data()
            st.success("標準データに戻しました。")
            st.rerun()

# ============================================================
# 3. 評価項目管理（コードを直さず指標を増減できるようにする画面）
# ============================================================
with tab_params:
    st.markdown("#### 評価項目一覧")
    st.caption("スコア計算に使用する評価項目を管理します。ここで追加・編集した項目は、"
              "マップ・ランキング・比較・地区詳細・シミュレーション・総合スコアに自動的に反映されます。")

    all_params = load_all_parameters()
    if all_params:
        params_df = pd.DataFrame([{
            "項目名": p["label"], "CSV列名": p["key"], "単位": p["unit"],
            "評価方向": "高いほど課題" if p["risk_direction"] == "positive" else "高いほど良い",
            "重み(%)": round(p["weight"] * 100, 1), "スコア計算に使用": p["active"],
            "説明": p["description"], "_param_id": p["param_id"],
        } for p in all_params])

        edited_params_df = st.data_editor(
            params_df, use_container_width=True, hide_index=True, key="params_editor",
            column_config={
                "_param_id": None,  # 内部IDは非表示
                "CSV列名": st.column_config.TextColumn(disabled=True),
                "評価方向": st.column_config.SelectboxColumn(options=["高いほど課題", "高いほど良い"]),
                "重み(%)": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
                "スコア計算に使用": st.column_config.CheckboxColumn(),
            },
        )

        if st.button("評価項目の変更を保存", type="primary"):
            updated_params = []
            for _, r in edited_params_df.iterrows():
                orig = next(p for p in all_params if p["param_id"] == r["_param_id"])
                updated_params.append({
                    **orig,
                    "label": r["項目名"], "unit": r["単位"],
                    "risk_direction": "positive" if r["評価方向"] == "高いほど課題" else "negative",
                    "weight": r["重み(%)"] / 100, "active": bool(r["スコア計算に使用"]),
                    "description": r["説明"],
                })
            save_all_parameters(updated_params)
            st.success("評価項目を更新しました。スコア・マップなど全画面に反映されます。")
            st.rerun()

    st.markdown("---")
    st.markdown("#### ＋評価項目を追加")
    with st.form("add_param_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_label = st.text_input("項目名", placeholder="例：配食サービス充足度")
            new_csv_column = st.text_input("CSV上の列名", placeholder="例：meal_delivery_score")
            new_unit = st.text_input("単位", value="指数(0-100)")
        with col2:
            new_direction = st.selectbox("評価方向", options=["高いほど良い", "高いほど課題"])
            new_weight = st.slider("重み(%)", 0, 100, 10)
            new_active = st.checkbox("スコア計算に使用する", value=True)
        new_description = st.text_area("説明", placeholder="この項目が何を表すかを記入してください")
        submitted = st.form_submit_button("追加する", type="primary")

        if submitted:
            if not new_label.strip() or not new_csv_column.strip():
                st.error("項目名とCSV列名は必須です。")
            elif new_csv_column in [p["key"] for p in all_params]:
                st.error(f"CSV列名「{new_csv_column}」は既に使用されています。別の列名にしてください。")
            else:
                risk_direction = "negative" if new_direction == "高いほど良い" else "positive"
                param_id = add_parameter(
                    label=new_label, csv_column=new_csv_column, unit=new_unit,
                    risk_direction=risk_direction, weight=new_weight / 100,
                    description=new_description, source="職員登録項目", active=new_active,
                )
                # 現在のデータに新しい列が無い場合、デフォルト値(50)で自動追加して既存機能が壊れないようにする
                df = get_raw_data()
                if new_csv_column not in df.columns:
                    df = df.copy()
                    df[new_csv_column] = 50.0
                    set_raw_data(df)
                    st.info(f"現在のデータに「{new_csv_column}」列が無かったため、仮の値（50点）で追加しました。"
                           "「データ管理」タブから実際の値に更新してください。")
                st.success(f"評価項目「{new_label}」を追加しました（ID: {param_id}）。")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 評価項目を削除")
    if all_params:
        del_label = st.selectbox("削除する評価項目", options=[p["label"] for p in all_params], key="del_param_select")
        if st.button("🗑️ この評価項目を削除する"):
            del_param_id = next(p["param_id"] for p in all_params if p["label"] == del_label)
            delete_parameter(del_param_id)
            st.success(f"評価項目「{del_label}」を削除しました。")
            st.rerun()

# ============================================================
# 4. 評価パターン管理
# ============================================================
with tab_patterns:
    st.markdown("#### 現在の評価パターン")
    st.info(f"現在適用中のパターン：**{get_current_pattern_name()}**", icon="📌")

    st.markdown("---")
    st.markdown("#### 現在の設定を保存")
    with st.form("save_pattern_form"):
        pattern_name = st.text_input("パターン名", placeholder="例：移動重視")
        pattern_desc = st.text_input("説明（任意）", placeholder="例：移動系の課題を重視するパターン")
        save_submitted = st.form_submit_button("この内容で保存する", type="primary")
        if save_submitted:
            if not pattern_name.strip():
                st.error("パターン名を入力してください。")
            else:
                save_pattern(pattern_name, get_weights(), pattern_desc)
                st.success(f"評価パターン「{pattern_name}」を保存しました。")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 保存済みパターン")
    patterns = load_patterns()
    if not patterns:
        st.caption("保存されたパターンはまだありません。")
    else:
        for name, pattern in patterns.items():
            with st.container(border=True):
                st.markdown(f"**{name}**")
                if pattern.get("description"):
                    st.caption(pattern["description"])
                weights_text = "　".join(f"{k}:{v*100:.0f}%" for k, v in pattern["weights"].items())
                st.caption(weights_text)
                col_apply, col_delete = st.columns(2)
                with col_apply:
                    if st.button(f"このパターンを適用", key=f"apply_{name}", use_container_width=True):
                        apply_pattern(name)
                        st.success(f"「{name}」を適用しました。")
                        st.rerun()
                with col_delete:
                    if st.button(f"削除", key=f"delete_{name}", use_container_width=True):
                        delete_pattern(name)
                        st.success(f"「{name}」を削除しました。")
                        st.rerun()

render_footer()
