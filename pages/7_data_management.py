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
from typing import Dict

import pandas as pd
import streamlit as st

from utils.config import COL_NAME, DATA_TYPE_OPTIONS, DATA_TYPE_SURVEY
from utils.state import (
    get_raw_data, set_raw_data, get_weights, set_weights,
    get_data_source_info, reset_to_default_data, apply_pattern, get_current_pattern_name,
)
from utils.data_loader import read_uploaded_csv, dataframe_to_csv_bytes, save_dataframe_to_csv
from utils.survey_loader import read_survey_file, merge_survey_into_data
from utils.validation import validate_dataframe
from utils.parameter_loader import (
    load_all_parameters, get_default_weights, add_parameter, delete_parameter, save_all_parameters,
)
from utils.category_loader import (
    load_all_categories, get_category_label, add_category, update_category, delete_category,
    UNCATEGORIZED_ID,
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

tab_weight, tab_data, tab_survey, tab_params, tab_categories, tab_patterns = st.tabs(
    ["重みの設定", "データ管理（CSV）", "アンケート取り込み", "評価項目管理", "カテゴリ管理", "評価パターン管理"]
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
# 2.5 アンケート取り込み
# ------------------------------------------------------------
# 宇都宮市が既に保有しているアンケート調査結果（CSV/Excel）を取り込みます。
# 質問項目名はコード内に一切固定しておらず、アップロードされたファイルの
# 列名をその場で確認しながら、
#   ・既存の評価項目に紐付ける（同じ観点の値を更新する）
#   ・新しい評価項目として登録する
# のどちらかを列ごとに選べます。手順は以下の3ステップです。
#   ① ファイルをアップロードして中身を確認
#   ② 地区名の列・取り込みたい列を選ぶ
#   ③ 列ごとの紐付け方法を指定して取り込みを確定する
# ============================================================
with tab_survey:
    st.markdown("#### アンケート調査結果の取り込み")
    st.caption(
        "自治体が既に保有しているアンケート調査結果（CSV／Excel）を取り込み、地区データと結合します。"
        "ここで新しくアンケートを実施するものではありません。質問項目はファイルの内容に応じてその場で選べるため、"
        "コード内に固定の質問項目はありません。"
    )

    import_result = st.session_state.pop("_survey_import_result", None)
    if import_result is not None:
        st.success(f"{import_result['n_columns']}列を取り込みました。他の画面にも即時反映されます。"
                  "内容を確認後、「データ管理（CSV）」タブから永続保存できます。")
        if import_result["unmatched"]:
            st.warning("以下の地区名は既存データと一致しなかったため、取り込まれませんでした： "
                      + "、".join(import_result["unmatched"]))
        for key, fill_value, missing_names in import_result["filled_info"]:
            st.warning(
                f"「{key}」はアンケートが回答されていない地区があったため、"
                f"取り込めた地区の平均値（{fill_value}）を仮の値として設定しました"
                f"（該当地区：{'、'.join(missing_names)}）。"
                "実際の値が分かり次第、「データ管理（CSV）」タブから更新してください。",
                icon="⚠️",
            )

    survey_file = st.file_uploader("アンケート結果ファイルを選択（CSV または Excel）",
                                   type=["csv", "xlsx", "xls"], key="survey_uploader")

    if survey_file is not None:
        # アップロードのたびに読み直すと選択状態が消えるため、同じファイルの間はセッションに保持する
        if st.session_state.get("_survey_file_name") != survey_file.name:
            try:
                st.session_state["_survey_df"] = read_survey_file(survey_file)
                st.session_state["_survey_file_name"] = survey_file.name
                st.session_state.pop("_survey_mapping_ready", None)
            except ValueError as e:
                st.error(str(e))
                st.session_state.pop("_survey_df", None)

    survey_df = st.session_state.get("_survey_df")
    if survey_df is not None:
        st.markdown("**① アップロードされたファイルの中身（先頭5行）**")
        st.dataframe(survey_df.head(), use_container_width=True, hide_index=True)
        st.caption(f"{len(survey_df)}行 × {len(survey_df.columns)}列")

        st.markdown("---")
        st.markdown("**② 地区名の列・取り込む列を選択**")
        all_columns = list(survey_df.columns)
        name_col = st.selectbox("地区名として使う列", options=all_columns, key="survey_name_col")
        importable_columns = [c for c in all_columns if c != name_col]
        selected_columns = st.multiselect(
            "取り込みたい列（複数選択可）", options=importable_columns, key="survey_import_cols",
            help="ここで選んだ列だけを地区データに取り込みます。",
        )

        if selected_columns:
            st.markdown("---")
            st.markdown("**③ 列ごとの紐付け方法を指定**")
            st.caption("それぞれの列を、既存の評価項目の値として使うか、新しい評価項目として登録するかを選んでください。")

            existing_params = load_all_parameters()
            existing_labels = [p["label"] for p in existing_params]
            category_options = load_all_categories()
            category_labels = [c["label"] for c in category_options]
            category_id_by_label = {c["label"]: c["category_id"] for c in category_options}

            column_plans = {}
            for col in selected_columns:
                with st.container(border=True):
                    st.markdown(f"**列：「{col}」**")
                    mode = st.radio(
                        "紐付け方法", options=["既存の評価項目に紐付ける", "新しい評価項目として登録する"],
                        key=f"survey_mode_{col}", horizontal=True,
                    )
                    if mode == "既存の評価項目に紐付ける":
                        if not existing_labels:
                            st.warning("登録済みの評価項目がありません。「新しい評価項目として登録する」を選んでください。")
                            column_plans[col] = None
                            continue
                        target_label = st.selectbox("紐付け先の評価項目", options=existing_labels, key=f"survey_target_{col}")
                        target_param = next(p for p in existing_params if p["label"] == target_label)
                        column_plans[col] = {"type": "existing", "param": target_param}
                        st.caption(f"「{col}」の値で、既存の評価項目「{target_label}」（列名：{target_param['key']}）を更新します。")
                    else:
                        c1, c2 = st.columns(2)
                        with c1:
                            new_label = st.text_input("項目名", value=col, key=f"survey_label_{col}")
                            new_key = st.text_input("内部キー（CSV列名）", value=col, key=f"survey_key_{col}")
                            new_unit = st.text_input("単位", value="%", key=f"survey_unit_{col}")
                            new_category_label = st.selectbox("カテゴリ", options=category_labels, key=f"survey_cat_{col}")
                        with c2:
                            new_direction = st.selectbox(
                                "評価方向", options=["高いほど着目度が高い", "低いほど着目度が高い"],
                                key=f"survey_dir_{col}",
                                help="例：「周囲からサポートを受けられる割合」は低いほど着目度が高い、"
                                     "「地域活動参加率」も低いほど着目度が高い、といったように選んでください。",
                            )
                            new_weight = st.slider("初期重み(%)", 0, 100, 5, key=f"survey_weight_{col}")
                            new_target_year = st.text_input("対象年度", placeholder="例：令和7年度", key=f"survey_year_{col}")
                        column_plans[col] = {
                            "type": "new",
                            "label": new_label, "key": new_key, "unit": new_unit,
                            "category": category_id_by_label.get(new_category_label, UNCATEGORIZED_ID),
                            "risk_direction": "positive" if new_direction == "高いほど着目度が高い" else "negative",
                            "weight": new_weight / 100, "target_year": new_target_year,
                        }

            st.markdown("---")
            if st.button("この内容で取り込む", type="primary"):
                # 【重要】評価項目の登録（add_parameter）は、データ結合・検証がすべて
                # 成功した後に行う。先に登録してしまうと、後続の検証で失敗した場合に
                # 「評価項目としては存在するが、対応するデータ列が無い」状態になり、
                # スコア計算がKeyErrorで壊れてしまうため（実機テストで発見・修正）。
                mapping = {}
                new_plans = []  # (col, plan) のうち新規登録予定のもの。検証後にまとめて登録する
                errors = []
                existing_keys = [p["key"] for p in load_all_parameters()]
                seen_new_keys = set()
                for col, plan in column_plans.items():
                    if plan is None:
                        errors.append(f"「{col}」の紐付け先が選択されていません。")
                        continue
                    if plan["type"] == "existing":
                        mapping[col] = plan["param"]["key"]
                    else:
                        if not plan["label"].strip() or not plan["key"].strip():
                            errors.append(f"「{col}」の項目名・内部キーは必須です。")
                            continue
                        if plan["key"] in existing_keys or plan["key"] in seen_new_keys:
                            errors.append(f"「{col}」の内部キー「{plan['key']}」は既に使用されています。")
                            continue
                        seen_new_keys.add(plan["key"])
                        mapping[col] = plan["key"]
                        new_plans.append((col, plan))

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    merged_df, unmatched = merge_survey_into_data(
                        get_raw_data(), COL_NAME, survey_df, name_col, mapping,
                    )

                    # アンケートは全地区が回答するとは限らない（回収率100%が前提ではない）。
                    # 新規登録予定の列に欠損がある場合は、取り込み自体をブロックするのではなく、
                    # 「取り込めた地区の平均値」で一時的に穴埋めしたうえで取り込みを完了させる。
                    # どの地区が穴埋めされたかを明示し、「データ管理（CSV）」タブから
                    # 実際の値に更新するよう案内する（既存項目への紐付けは、未回答地区は
                    # 元の値がそのまま維持されるため対象外）。
                    filled_info = []
                    for _, plan in new_plans:
                        key = plan["key"]
                        missing_mask = merged_df[key].isna()
                        if missing_mask.any():
                            fill_value = round(merged_df[key].mean(), 1)
                            missing_names = merged_df.loc[missing_mask, COL_NAME].tolist()
                            merged_df.loc[missing_mask, key] = fill_value
                            filled_info.append((key, fill_value, missing_names))

                    is_valid, val_errors = validate_dataframe(merged_df)
                    if not is_valid:
                        st.error("取り込み後のデータに問題があります。数値以外の値が含まれていないか確認してください。"
                                 "評価項目は登録されていません。")
                        for e in val_errors:
                            st.write(f"❌ {e}")
                    else:
                        # ここまで来て初めて、新しい評価項目を確定登録する
                        for col, plan in new_plans:
                            add_parameter(
                                label=plan["label"], csv_column=plan["key"], unit=plan["unit"],
                                risk_direction=plan["risk_direction"], weight=plan["weight"],
                                category=plan["category"], data_type=DATA_TYPE_SURVEY,
                                target_year=plan["target_year"], description=f"アンケート取り込み（列名：{col}）",
                                source="自治体アンケート調査結果", active=True,
                            )
                        set_raw_data(merged_df, source_name=f"アンケート取り込み（{survey_file.name}）")
                        st.session_state["_survey_import_result"] = {
                            "n_columns": len(mapping), "unmatched": unmatched, "filled_info": filled_info,
                        }
                        st.session_state.pop("_survey_df", None)
                        st.session_state.pop("_survey_file_name", None)
                        st.rerun()

# ============================================================
# 3. 評価項目管理（コードを直さず指標を増減できるようにする画面）
# ============================================================
with tab_params:
    st.markdown("#### 評価項目一覧")
    st.caption("スコア計算に使用する評価項目を管理します。ここで追加・編集した項目は、"
              "マップ・ランキング・比較・地区詳細・シミュレーション・総合スコア・カテゴリ別分析に自動的に反映されます。")

    category_options = load_all_categories()
    category_label_by_id = {c["category_id"]: c["label"] for c in category_options}
    category_id_by_label = {c["label"]: c["category_id"] for c in category_options}
    category_labels = [c["label"] for c in category_options]

    all_params = load_all_parameters()
    if all_params:
        params_df = pd.DataFrame([{
            "項目名": p["label"],
            "カテゴリ": category_label_by_id.get(p["category"], "その他"),
            "CSV列名": p["key"], "単位": p["unit"],
            "データ種別": p["data_type"],
            "評価方向": "高いほど課題" if p["risk_direction"] == "positive" else "高いほど良い",
            "重み(%)": round(p["weight"] * 100, 1), "スコア計算に使用": p["active"],
            "対象年度": p.get("target_year", ""),
            "説明": p["description"], "_param_id": p["param_id"],
        } for p in all_params])

        edited_params_df = st.data_editor(
            params_df, use_container_width=True, hide_index=True, key="params_editor",
            column_config={
                "_param_id": None,  # 内部IDは非表示
                "CSV列名": st.column_config.TextColumn(disabled=True),
                "カテゴリ": st.column_config.SelectboxColumn(options=category_labels),
                "データ種別": st.column_config.SelectboxColumn(options=DATA_TYPE_OPTIONS),
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
                    "label": r["項目名"],
                    "category": category_id_by_label.get(r["カテゴリ"], UNCATEGORIZED_ID),
                    "unit": r["単位"],
                    "data_type": r["データ種別"],
                    "risk_direction": "positive" if r["評価方向"] == "高いほど課題" else "negative",
                    "weight": r["重み(%)"] / 100, "active": bool(r["スコア計算に使用"]),
                    "target_year": r["対象年度"],
                    "description": r["説明"],
                })
            save_all_parameters(updated_params)
            st.success("評価項目を更新しました。スコア・マップ・カテゴリ別分析など全画面に反映されます。")
            st.rerun()

    st.markdown("---")
    st.markdown("#### ＋評価項目を追加")
    with st.form("add_param_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_label = st.text_input("項目名", placeholder="例：配食サービス充足度")
            new_csv_column = st.text_input("CSV上の列名", placeholder="例：meal_delivery_score")
            new_unit = st.text_input("単位", value="指数(0-100)")
            new_category_label = st.selectbox("カテゴリ", options=category_labels,
                                               help="人口・世帯／介護・健康／移動・生活環境などの分類です。"
                                                    "「カテゴリ管理」タブで種類を追加・編集できます。")
            new_target_year = st.text_input("対象年度", placeholder="例：令和7年度")
        with col2:
            new_direction = st.selectbox("評価方向", options=["高いほど良い", "高いほど課題"])
            new_data_type = st.selectbox("データ種別", options=DATA_TYPE_OPTIONS)
            new_weight = st.slider("重み(%)", 0, 100, 10)
            new_active = st.checkbox("スコア計算に使用する", value=True)
        new_description = st.text_area("説明", placeholder="この項目が何を表すかを記入してください")
        new_source = st.text_input("データ出典", placeholder="例：高齢福祉課 事業実績")
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
                    category=category_id_by_label.get(new_category_label, UNCATEGORIZED_ID),
                    data_type=new_data_type, target_year=new_target_year,
                    description=new_description, source=new_source or "職員登録項目", active=new_active,
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
# 3.5 カテゴリ管理
# ------------------------------------------------------------
# 評価項目を束ねる「人口・世帯」「移動・生活環境」などのカテゴリを
# 追加・編集・削除できる画面です。カテゴリを削除しても、それを使っていた
# 評価項目は自動的に「その他」として扱われます（データは失われません）。
# ============================================================
with tab_categories:
    st.markdown("#### カテゴリ一覧")
    st.caption("評価項目を束ねる分類（カテゴリ）を管理します。ダッシュボード・市全体分析・地区詳細の"
              "カテゴリ別集計に反映されます。")

    categories = load_all_categories()
    param_count_by_category: Dict[str, int] = {}
    for p in load_all_parameters():
        param_count_by_category[p["category"]] = param_count_by_category.get(p["category"], 0) + 1

    cat_table = [{
        "カテゴリ名": c["label"], "表示順": c["display_order"],
        "所属する評価項目数": param_count_by_category.get(c["category_id"], 0),
        "_category_id": c["category_id"],
    } for c in categories]
    st.dataframe(cat_table, use_container_width=True, hide_index=True,
                column_config={"_category_id": None})

    st.markdown("---")
    st.markdown("#### ＋カテゴリを追加")
    with st.form("add_category_form"):
        new_cat_label = st.text_input("カテゴリ名", placeholder="例：住まい・防災")
        new_cat_order = st.number_input("表示順（小さいほど先に表示）", min_value=1, value=len(categories))
        add_cat_submitted = st.form_submit_button("追加する", type="primary")
        if add_cat_submitted:
            if not new_cat_label.strip():
                st.error("カテゴリ名を入力してください。")
            elif new_cat_label in [c["label"] for c in categories]:
                st.error(f"カテゴリ「{new_cat_label}」は既に存在します。")
            else:
                add_category(new_cat_label, display_order=int(new_cat_order))
                st.success(f"カテゴリ「{new_cat_label}」を追加しました。")
                st.rerun()

    st.markdown("---")
    st.markdown("#### カテゴリ名・表示順を編集")
    editable_categories = [c for c in categories if c["category_id"] != UNCATEGORIZED_ID]
    if editable_categories:
        edit_cat_target_label = st.selectbox(
            "編集するカテゴリ", options=[c["label"] for c in editable_categories], key="edit_cat_select")
        edit_cat_target = next(c for c in editable_categories if c["label"] == edit_cat_target_label)
        with st.form("edit_category_form"):
            edited_label = st.text_input("カテゴリ名", value=edit_cat_target["label"])
            edited_order = st.number_input("表示順", min_value=1, value=edit_cat_target["display_order"])
            edit_submitted = st.form_submit_button("この内容で更新する", type="primary")
            if edit_submitted:
                update_category(edit_cat_target["category_id"], label=edited_label, display_order=int(edited_order))
                st.success(f"カテゴリ「{edited_label}」を更新しました。")
                st.rerun()
    else:
        st.caption("編集できるカテゴリがありません。")

    st.markdown("---")
    st.markdown("#### カテゴリを削除")
    st.caption("「その他」は削除できません。削除すると、そのカテゴリに属していた評価項目は自動的に「その他」として扱われます。")
    if editable_categories:
        del_cat_label = st.selectbox(
            "削除するカテゴリ", options=[c["label"] for c in editable_categories], key="del_cat_select")
        if st.button("🗑️ このカテゴリを削除する"):
            del_cat_id = next(c["category_id"] for c in editable_categories if c["label"] == del_cat_label)
            delete_category(del_cat_id)
            st.success(f"カテゴリ「{del_cat_label}」を削除しました。所属していた評価項目は「その他」に移動しました。")
            st.rerun()
    else:
        st.caption("削除できるカテゴリがありません。")

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
