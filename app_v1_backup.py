import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# ページ設定
st.set_page_config(
    page_title="漫画シナリオ生成AI",
    page_icon="📖",
    layout="wide"
)

# タイトル
st.title("📖 漫画シナリオ生成AI - データ分析ダッシュボード")
st.markdown("---")

# サイドバー
with st.sidebar:
    st.header("メニュー")
    page = st.radio(
        "選択してください",
        ["📊 データ分析", "🤖 シナリオ生成", "⚙️ 設定"]
    )

# データ分析ページ
if page == "📊 データ分析":
    st.header("過去記事データ分析")

    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "CSV/Excelファイルをアップロード",
        type=['csv', 'xlsx', 'xls'],
        help="過去の記事データ（PV、CTR、タイトル等）をアップロードしてください"
    )

    if uploaded_file is not None:
        # データ読み込み
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"✅ データ読み込み完了: {len(df)}件の記事")

            # データプレビュー
            with st.expander("📋 データプレビュー"):
                st.dataframe(df.head(10))
                st.write(f"カラム: {list(df.columns)}")

            # カラム選択
            st.subheader("分析設定")
            col1, col2, col3 = st.columns(3)

            with col1:
                title_col = st.selectbox(
                    "タイトルカラム",
                    options=df.columns.tolist(),
                    help="記事タイトルが入っているカラムを選択"
                )

            with col2:
                pv_col = st.selectbox(
                    "PVカラム",
                    options=[col for col in df.columns if col.lower() in ['pv', 'pageview', 'views']],
                    help="PV（ページビュー）が入っているカラムを選択"
                )

            with col3:
                ctr_col = st.selectbox(
                    "CTRカラム（任意）",
                    options=['なし'] + [col for col in df.columns if col.lower() in ['ctr', 'click_through_rate']],
                    help="CTRが入っているカラムを選択（任意）"
                )

            st.markdown("---")

            # 基本統計
            st.subheader("📈 基本統計")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("総記事数", f"{len(df):,}件")

            with col2:
                if pv_col:
                    avg_pv = df[pv_col].mean()
                    st.metric("平均PV", f"{avg_pv:,.0f}")

            with col3:
                if pv_col:
                    total_pv = df[pv_col].sum()
                    st.metric("総PV", f"{total_pv:,.0f}")

            with col4:
                if pv_col:
                    median_pv = df[pv_col].median()
                    st.metric("中央値PV", f"{median_pv:,.0f}")

            # PV分布
            if pv_col:
                st.subheader("📊 PV分布")

                col1, col2 = st.columns(2)

                with col1:
                    # ヒストグラム
                    fig_hist = px.histogram(
                        df,
                        x=pv_col,
                        nbins=50,
                        title="PV分布ヒストグラム",
                        labels={pv_col: 'PV', 'count': '記事数'}
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

                with col2:
                    # ボックスプロット
                    fig_box = px.box(
                        df,
                        y=pv_col,
                        title="PVボックスプロット",
                        labels={pv_col: 'PV'}
                    )
                    st.plotly_chart(fig_box, use_container_width=True)

            # ヒット記事分析
            st.subheader("🔥 ヒット記事分析")

            if pv_col:
                top_n = st.slider("上位何件を分析しますか？", 10, 100, 20)

                # 上位記事抽出
                top_articles = df.nlargest(top_n, pv_col)

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"### Top {top_n} 記事")
                    display_df = top_articles[[title_col, pv_col]].copy()
                    display_df['順位'] = range(1, len(top_articles) + 1)
                    display_df = display_df[['順位', title_col, pv_col]]
                    st.dataframe(display_df, use_container_width=True)

                with col2:
                    st.write("### ヒット記事の特徴")

                    # タイトル文字数分析
                    if title_col:
                        top_articles['title_length'] = top_articles[title_col].astype(str).str.len()
                        avg_length = top_articles['title_length'].mean()
                        st.metric("平均タイトル文字数", f"{avg_length:.1f}文字")

                        # 頻出ワード分析
                        st.write("#### 頻出キーワード（Top 10）")
                        all_titles = ' '.join(top_articles[title_col].astype(str))

                        # 日本語の単語抽出（簡易版）
                        words = re.findall(r'[ぁ-んァ-ヶー一-龥]+', all_titles)
                        word_counts = Counter([w for w in words if len(w) > 1])

                        for word, count in word_counts.most_common(10):
                            st.write(f"- {word}: {count}回")

            # タイトル長さと PV の相関
            if pv_col and title_col:
                st.subheader("📏 タイトル文字数 vs PV")

                df['title_length'] = df[title_col].astype(str).str.len()

                fig_scatter = px.scatter(
                    df,
                    x='title_length',
                    y=pv_col,
                    title="タイトル文字数とPVの関係",
                    labels={'title_length': 'タイトル文字数', pv_col: 'PV'},
                    trendline="lowess"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                # 相関係数
                corr = df['title_length'].corr(df[pv_col])
                st.info(f"相関係数: {corr:.3f}")

        except Exception as e:
            st.error(f"エラー: {e}")

    else:
        st.info("👆 CSVまたはExcelファイルをアップロードしてください")

        # サンプルデータフォーマット
        with st.expander("📝 データフォーマット例"):
            st.write("以下のようなカラムを含むCSV/Excelファイルをアップロードしてください：")
            sample_data = pd.DataFrame({
                'タイトル': ['【漫画】彼氏が突然プロポーズしてきた話', '【実話】職場の先輩に恋をした結果...'],
                'PV': [50000, 30000],
                'CTR': [0.05, 0.03],
                'PV単価': [0.5, 0.4]
            })
            st.dataframe(sample_data)

# シナリオ生成ページ
elif page == "🤖 シナリオ生成":
    st.header("AI漫画シナリオ生成")
    st.info("この機能は次のステップで実装します")

    # プレースホルダー
    st.write("### 準備中...")
    st.write("- ヒット記事パターンの学習")
    st.write("- Claude API統合")
    st.write("- プロンプトエンジニアリング")

# 設定ページ
elif page == "⚙️ 設定":
    st.header("設定")

    st.subheader("API設定")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help=".envファイルまたはここで設定してください"
    )

    if api_key:
        st.success("✅ APIキーが設定されました")
    else:
        st.warning("⚠️ APIキーを設定してください")
