import pandas as pd
import streamlit as st
import requests
import io

st.title("伝助 日程調整ツール")

# --- Step 1: CSVアップロード ---
uploaded_file = st.file_uploader("伝助のCSVをアップロードしてください", type="csv")


# --- Step 2: データ読み込みとメンバー選択 ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        df = df.rename(columns={df.columns[0]: "日付"})
        df.set_index("日付", inplace=True)

        members = df.columns.tolist()
        st.write("メンバーを選択してください（複数選択可）:")
        selected_members = st.multiselect("メンバー", members)

        # --- Step 3: 候補日抽出 ---
        if selected_members:
            subset = df[selected_members]
            all_circle = subset[(subset == '○').all(axis=1)]
            all_triangle = subset[(subset == '△').all(axis=1)]

            st.subheader("✅ 全員が○の日")
            st.write(all_circle.index.tolist() or "該当なし")

            st.subheader("⚠ 全員が△の日")
            st.write(all_triangle.index.tolist() or "該当なし")

            # --- Step 4: 日付選択と出力 ---
            all_candidates = all_circle.index.tolist() + all_triangle.index.tolist()
            if all_candidates:
                selected_day = st.selectbox("日付を選んでください", all_candidates)
                if st.button("この日に決定"):
                    result_text = f"{selected_day}、メンバー「{', '.join(selected_members)}」"
                    st.success(result_text)

                    # --- Step 5: メンバー名のコピー用（ワンクリックコピー対応） ---
                    st.markdown("**コピー用メンバー一覧：**")
                    st.code(', '.join(selected_members), language=None)
    
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
