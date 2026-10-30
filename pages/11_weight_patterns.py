import streamlit as st
import pandas as pd
from utils.patterns import load_patterns,save_pattern,delete_pattern
from utils.weighted_official import METRICS,calculate
from utils.active_weights import get_weights, available_patterns, apply_pattern, apply_weights

st.title('評価重み・パターン保存')
if st.session_state.pop('_pattern_saved_notice', None):
    st.success('パターンを保存・適用しました。')
st.caption('39地区の公開データを各指標0〜100に相対正規化した比較用スコアです。行政判断の確定的な優先順位・施策効果予測ではありません。')
patterns = load_patterns()
compatible, legacy = available_patterns()
# 旧形式のパターンは内部に保持し、通常の画面には表示しません。

choices = list(compatible)
active = st.session_state.get('active_weight_pattern', '標準（公開指標）')
# The page selector is only a pending choice until Apply is pressed.
if st.session_state.get('_page_pattern_synced') != active:
    st.session_state['pattern_select'] = active if active in choices else choices[0]
    st.session_state['_page_pattern_synced'] = active
selected = st.selectbox('保存済み・標準パターンを選ぶ', choices,
                        key='pattern_select')
get_weights()
if st.button('選択したパターンを適用', key='apply_pattern_page'):
    try:
        apply_pattern(selected)
        st.session_state['_page_pattern_synced'] = selected
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
st.info('現在適用中：' + st.session_state.get('active_weight_pattern', 'カスタム'))
# 編集中の値をセッションに保持し、適用時には入力欄を初期化しません。
revision = st.session_state.get('_weight_revision', 0)
# Sliders must live outside a form so saving from a separate form reads the latest edits.
st.subheader('指標ごとの重み（個別調整）')
edited = {}
for k, (label, direction) in METRICS.items():
    edited[k] = st.slider(label, 0.0, 10.0,
                          float(st.session_state.weight_values.get(k, 0.0)), 0.5,
                          key=f'weight_editor_{revision}_{k}')
apply = st.button('この重みをランキングに反映', key='apply_edited_weights')
if apply:
    try:
        apply_weights(edited)
        st.success('重みを反映しました。入力値は保持されます。')
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
if st.button('重みをリセット', key='reset_weight_values'):
    from utils.active_weights import DEFAULT_WEIGHTS
    apply_weights(DEFAULT_WEIGHTS, '標準（公開指標）')
    st.rerun()
weights = get_weights()
st.caption('重みが0の指標は計算対象外。欠損値は0に置換せず、利用可能な重みで再配分します。')
if not any(v>0 for v in weights.values()):
 st.warning('1つ以上の重みを0より大きくしてください。')
else:
 df=calculate(weights).sort_values('weighted_score',ascending=False,na_position='last')
 df.insert(0,'順位',range(1,len(df)+1))
 df['weighted_score'] = df['weighted_score'].round(1)
 st.dataframe(df[['順位','district','weighted_score','coverage_pct']].rename(columns={'district':'地区名','weighted_score':'見守り優先度スコア','coverage_pct':'利用可能な指標の重み割合（%）'}),hide_index=True,use_container_width=False,width=850)
 st.download_button('この重みでの結果をCSV保存',df.to_csv(index=False).encode('utf-8-sig'),'weighted_ranking.csv','text/csv')
st.divider()
st.subheader('パターンを保存')
st.caption('上のスライダーで編集中の値を保存します。保存したパターンを適用すると、ランキングも同じ重みで再計算されます。')
with st.form('save_current_pattern_form', clear_on_submit=False):
    name = st.text_input('パターン名（同名の場合は上書き）', key='save_pattern_name')
    description = st.text_input('説明（任意）', key='save_pattern_description')
    save_clicked = st.form_submit_button('現在の重みを保存')
if save_clicked:
    if not name.strip():
        st.error('パターン名を入力してください。')
    elif name.strip() in legacy:
        st.error('旧パターンと同じ名前は使用できません。')
    else:
        try:
            # Read the current independent slider widget state.
            # Previously `weights` referred only to the last applied values.
            current_revision = st.session_state.get('_weight_revision', 0)
            draft = {
                k: float(st.session_state.get(f'weight_editor_{current_revision}_{k}',
                                              st.session_state.weight_values.get(k, 0.0)))
                for k in METRICS
            }
            if not any(v > 0 for v in draft.values()):
                st.error('少なくとも1つの重みを0より大きくしてください。')
            else:
                save_pattern(name.strip(), draft, description)
                # Apply the exact values just saved; do not reselect an older preset.
                apply_weights(draft, name.strip())
                # The selector already exists in this run. On the next rerun,
                # the top-of-page sync will select the newly active pattern.
                st.session_state['_pattern_saved_notice'] = '「' + name.strip() + '」を保存・適用しました。'
                st.rerun()
        except (OSError, ValueError, TypeError) as e:
            st.error(f'保存できませんでした：{e}')
saved_compatible = {n: v for n, v in patterns.items() if n not in legacy}
if saved_compatible:
 st.subheader('パターン削除')
 to_delete=st.selectbox('削除するパターン',list(saved_compatible),key='delete_pattern')
 confirm=st.checkbox('削除を確認しました')
 if st.button('選択したパターンを削除',disabled=not confirm):
  try:
   delete_pattern(to_delete)
   st.rerun()
  except OSError:st.error('削除できません。保存先のアクセス権限を確認してください。')
