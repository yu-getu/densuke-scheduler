import pandas as pd
import streamlit as st
import requests
import io

st.set_page_config(page_title="伝助日程抽出ツール", layout="centered")

st.title("📅 伝助 日程調整ツール")

# --- ユーザー案内セクション ---
with st.expander("🔰 伝助からCSVファイルのURLを取得する手順（画像付き）"):
    st.markdown("""
    #### 手順1: 伝助の日程ページを開きます
    下記のようなページです：
    """)
    st.image("images/step1.png", caption="伝助で作成された日程調整ページ", use_container_width=True)

    st.markdown("""
    #### 手順2: 「CSVデータを取得する」ボタンを右クリックして、**リンクのアドレスをコピー**します
    """)
    st.image("images/step2.png", caption="CSVリンクをコピーする手順", use_container_width=True)

    st.markdown("#### 手順3: 下の入力欄にコピーしたURLを貼り付けてください。")

# --- 入力方法の選択 ---
st.markdown("## 1️⃣ CSVファイルの取得方法を選択してください")
input_method = st.radio("取得方法:", ["アップロード", "URLから取得"])

uploaded_file = None
if input_method == "アップロード":
    uploaded_file = st.file_uploader("CSVファイルを選択", type="csv")
elif input_method == "URLから取得":
    densuke_url = st.text_input("📎 伝助のCSVダウンロードURLを貼り付けてください")
    if densuke_url:
        try:
            response = requests.get(densuke_url)
            response.encoding = 'shift_jis'
            uploaded_file = io.StringIO(response.text)
        except Exception as e:
            st.error(f"CSVのダウンロードに失敗しました: {e}")

# --- CSV読み込みと処理 ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        df = df.rename(columns={df.columns[0]: "日付"})
        df.set_index("日付", inplace=True)

        members = df.columns.tolist()
        selected_members = st.multiselect("メンバーを選択してください", members)

        if selected_members:
            subset = df[selected_members]

            all_double_circle = subset[(subset == '◎').all(axis=1)]
            all_circle = subset[(subset == '○').all(axis=1)]
            all_triangle = subset[(subset == '△').all(axis=1)]

            st.subheader("🌟 全員が◎（二重丸）の日")
            st.write(all_double_circle.index.tolist() or "該当なし")

            st.subheader("✅ 全員が○（丸）の日")
            st.write(all_circle.index.tolist() or "該当なし")

            st.subheader("⚠ 全員が△（三角）の日")
            st.write(all_triangle.index.tolist() or "該当なし")

            all_candidates = all_double_circle.index.tolist() + all_circle.index.tolist() + all_triangle.index.tolist()
            if all_candidates:
                selected_day = st.selectbox("✅ 日付を選んでください", all_candidates)
                if st.button("この日に決定"):
                    result_text = f"{selected_day}、メンバー「{', '.join(selected_members)}」"
                    st.success(result_text)
                    st.markdown("### 📋 コピー用メンバー一覧")
                    st.code(', '.join(selected_members), language=None)

    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
