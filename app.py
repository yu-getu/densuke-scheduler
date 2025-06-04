import pandas as pd
import streamlit as st
import requests
import io

st.title("伝助 日程・シナリオ調整ツール")

# --- Step 1: 伝助URLまたはCSVアップロード ---
input_method = st.radio("CSVファイルの取得方法を選択してください:", ["CSVアップロード", "伝助URLから取得"])

# upload_fileの初期化
uploaded_file = None

if input_method == "CSVアップロード":
    uploaded_file = st.file_uploader("伝助のCSVをアップロード", type="csv")
elif input_method == "伝助URLから取得":
    with st.expander("🔰 伝助からCSVファイルのURLを取得する手順（画像付き）"):
        st.markdown("""
        #### 手順1: 伝助の日程ページを下にスクロールし、ボタンを押す
        """)
        st.image("images/step1.png", caption="伝助で作成された日程調整ページ", use_container_width=True)
        st.markdown("""
        #### 手順2: 「CSVデータを取得する」ボタンを右クリックして、**リンクのアドレスをコピー**します
        """)
        st.image("images/step2.png", caption="CSVリンクをコピーする手順", use_container_width=True)
        st.markdown("#### 手順3: 下の入力欄にコピーしたURLを貼り付けてください。")

    densuke_url = st.text_input("伝助のCSVダウンロードURLを入力:")
    if densuke_url:
        try:
            response = requests.get(densuke_url)
            response.encoding = 'shift_jis'
            uploaded_file = io.StringIO(response.text)
        except Exception as e:
            st.error(f"ダウンロードに失敗しました: {e}")
            uploaded_file = None

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        df = df.rename(columns={df.columns[0]: "項目"})
        df.set_index("項目", inplace=True)

        schedule_rows = df.index[df.index.str.contains(r"\d{1,2}/\d{1,2}")]
        # 日付ではない行をまず抽出
        scenario_rows = df.index[~df.index.isin(schedule_rows)]

        # 不要な行を除外
        scenario_rows = scenario_rows[
            ~scenario_rows.str.contains('----') &                      # 「----」を含む行
            ~scenario_rows.str.match(r"^【.*】$") &                    # 「【】」で囲まれている行
            ~(scenario_rows == "最終更新日時")                        # 「最終更新日時」行
        ]


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

                def show_dates(title, date_index):
                    st.subheader(title)
                    if date_index.empty:
                        st.info("該当なし")
                    else:
                        df_dates = pd.DataFrame(date_index.index.tolist(), columns=["日付"])
                        st.dataframe(df_dates, use_container_width=True)

                show_dates("✅ 全員が◎の日", all_double_circle)
                show_dates("✅ 全員が○の日", all_circle)
                show_dates("⚠ 全員が△の日", all_triangle)

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

                    def show_participants(title, participants):
                        st.subheader(title)
                        if not participants:
                            st.info("該当なし")
                        else:
                            df_participants = pd.DataFrame(participants, columns=["参加者"])
                            st.dataframe(df_participants, use_container_width=True)

                    show_participants("◎（GM希望など）", double_circles)
                    show_participants("○（PL希望など）", single_circles)

                    if double_circles:
                        selected_gm = st.selectbox("GM希望者から1人選んでください", double_circles)
                        if selected_gm:
                            st.markdown(f"### 📅 {selected_gm} のスケジュールに基づくPL希望者の参加可能日")

                            required_count = st.slider("必要な参加人数を選択してください", min_value=1, max_value=15, value=3)

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

                            # 必要人数を満たす日程のみ表示
                            filtered_info = [info for info in sorted_info if info["count"] >= required_count]

                            if filtered_info:
                                table_data = []
                                for info in filtered_info:
                                    table_data.append({
                                        "日付": info["day"],
                                        "GMマーク": info["mark"],
                                        "参加人数": info["count"],
                                        "参加者": ', '.join(info["participants"])
                                    })
                                st.markdown("### 📋 参加可能日リスト（多い順）")
                                st.dataframe(pd.DataFrame(table_data), use_container_width=True)

                                candidate_days = [info['day'] for info in filtered_info]
                                if candidate_days:
                                    selected_scenario_day = st.selectbox("日付を選んでメンバー表示:", candidate_days)
                                    for info in filtered_info:
                                        if info['day'] == selected_scenario_day:
                                            st.markdown("**参加メンバーを選んでください**")
                                            selected_pl = st.multiselect(
                                                f"参加メンバーを選んでください（最大 {required_count} 人まで）",
                                                options=info['participants'],
                                                default=info['participants'][:required_count],
                                                key=f"{info['day']}_select"
                                            )

                                            if len(selected_pl) > required_count:
                                                st.warning(f"{required_count} 人までしか選べません。選び直してください。")
                                                selected_pl = selected_pl[:required_count]

                                            result_text = f"「{selected_scenario}」：GM：{selected_gm}, PL:{', '.join(selected_pl)}"
                                            st.success(result_text)
                                            st.markdown("**コピー用：**")
                                            st.code(result_text, language=None)
                                            break
                            else:
                                st.warning("選択した必要人数を満たす日程がありません。")

    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
