import pandas as pd
import streamlit as st
import requests
import io

st.title("伝助 日程・シナリオ調整ツール")

# --- Step 1: 伝助URLまたはCSVアップロード ---
input_method = st.radio("CSVファイルの取得方法を選択してください:", ["CSVアップロード", "伝助URLから取得"])

#upload_fileの初期化
uploaded_file = None

if input_method == "CSVアップロード":
    uploaded_file = st.file_uploader("伝助のCSVをアップロード", type="csv")
elif input_method == "伝助URLから取得":
    densuke_url = st.text_input("伝助のCSVダウンロードURLを入力:")
    if densuke_url:
        try:
            response = requests.get(densuke_url)
            response.encoding = 'shift_jis'
            uploaded_file = io.StringIO(response.text)
        except Exception as e:
            st.error(f"ダウンロードに失敗しました: {e}")
            uploaded_file = None
else:
    uploaded_file = None

# --- Step 2: データ読み込みと処理 ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        df = df.rename(columns={df.columns[0]: "項目"})
        df.set_index("項目", inplace=True)

        schedule_rows = df.index[df.index.str.contains(r"\d{1,2}/\d{1,2}")]
        scenario_rows = df.index[~df.index.isin(schedule_rows)]

        tab1, tab2 = st.tabs(["\U0001F4C5 日程調整", "\U0001F4D8 シナリオ希望"])

        # --- タブ1: 日程調整 ---
        with tab1:
            members = df.columns.tolist()
            st.write("メンバーを選択してください（複数選択可）:")
            selected_members = st.multiselect("メンバー", members)
            if selected_members:
                subset = df.loc[schedule_rows, selected_members]
                all_circle = subset[(subset == '○').all(axis=1)]
                all_triangle = subset[(subset == '△').all(axis=1)]
                all_double_circle = subset[(subset == '◎').all(axis=1)]

                st.subheader("✅ 全員が◎の日")
                st.write(all_double_circle.index.tolist() or "該当なし")

                st.subheader("✅ 全員が○の日")
                st.write(all_circle.index.tolist() or "該当なし")

                st.subheader("⚠ 全員が△の日")
                st.write(all_triangle.index.tolist() or "該当なし")

                all_candidates = all_double_circle.index.tolist() + all_circle.index.tolist() + all_triangle.index.tolist()
                if all_candidates:
                    selected_day = st.selectbox("日付を選んでください", all_candidates)
                    if st.button("この日に決定"):
                        result_text = f"{selected_day}、メンバー「{', '.join(selected_members)}」"
                        st.success(result_text)
                        st.markdown("**コピー用メンバー一覧：**")
                        st.code(', '.join(selected_members), language=None)

        # --- タブ2: シナリオ希望 ---
        with tab2:
            if len(scenario_rows) > 0:
                selected_scenario = st.selectbox("シナリオ名を選択してください", scenario_rows)
                if selected_scenario:
                    scenario_row = df.loc[selected_scenario]

                    double_circles = scenario_row[scenario_row == '◎'].index.tolist()
                    single_circles = scenario_row[scenario_row == '○'].index.tolist()

                    st.subheader("◎（GM希望など）")
                    st.write(double_circles or "該当なし")

                    st.subheader("○（PL希望など）")
                    st.write(single_circles or "該当なし")

                    # --- 新機能: GM選択と日程調査 ---
                    if double_circles:
                        selected_gm = st.selectbox("GM希望者から1人選んでください", double_circles)
                        if selected_gm:
                            st.markdown(f"### \U0001F4C5 {selected_gm} のスケジュールに基づくPL希望者の参加可能日")
                            gm_schedule = df.loc[schedule_rows, selected_gm]

                            participation_info = []
                            for mark in ['◎', '○', '△']:
                                days = gm_schedule[gm_schedule == mark].index.tolist()
                                for day in days:
                                    pl_available = df.loc[day, single_circles]
                                    matching_pl = pl_available[pl_available.isin([mark, '◎'])].index.tolist()
                                    participation_info.append({
                                        "day": day,
                                        "mark": mark,
                                        "count": len(matching_pl),
                                        "participants": matching_pl
                                    })

                            sorted_info = sorted(participation_info, key=lambda x: x["count"], reverse=True)
                            for info in sorted_info:
                                st.markdown(f"**{info['day']} ({info['mark']}) - {info['count']}人**")
                                st.write(info['participants'])

                            # --- 日付ごとの詳細出力 ---
                            target_days = sorted(set([info['day'] for info in participation_info]))
                            selected_detail_day = st.selectbox("参加者を確認したい日付を選んでください", target_days)
                            if selected_detail_day:
                                selected_info = [i for i in participation_info if i['day'] == selected_detail_day]
                                for entry in selected_info:
                                    st.markdown(f"#### 「{selected_scenario}」：GM：{selected_gm}、メンバー")
                                    st.write(entry['participants'])

    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
