import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import os
import json
import random
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
import traceback

# デバッグ: インポートエラーをキャッチ
try:
    # ユーティリティのインポート
    sys.path.append(os.path.dirname(__file__))
    from utils.prompt_library import PromptLibrary
    from utils.scenario_manager import load_scenario_history, save_scenario, delete_scenario
    from pages.article_analysis import render_article_analysis_page
    st.success("✅ All modules imported successfully")
except Exception as e:
    st.error(f"❌ Import Error: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# バージョン情報
VERSION = "3.3.0"
VERSION_DATE = "2025-11-17"

# 環境変数読み込み（明示的にパスを指定）
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# ページ設定
st.set_page_config(
    page_title=f"記事ネタ提案ツール v{VERSION}",
    page_icon="💡",
    layout="wide"
)

# セッション状態の初期化
if 'df' not in st.session_state:
    st.session_state.df = None
if 'df_numeric' not in st.session_state:
    st.session_state.df_numeric = None
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = None

# タイトル
st.title(f"💡 記事ネタ提案ツール `v{VERSION}`")
st.caption(f"最終更新: {VERSION_DATE}")
st.markdown("---")

# サイドバー
with st.sidebar:
    # プロジェクト識別情報（大きく表示）
    st.markdown("""
    <div style="background-color: #FFE5E5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #FF6B6B;">
        <h3 style="color: #FF0000; margin: 0; text-align: center;">⚠️ プロジェクト識別</h3>
        <p style="color: #333; margin: 0.5rem 0; text-align: center; font-weight: bold; font-size: 1.1rem;">
            📝 記事ネタ提案ツール<br>
            🔌 ポート: <span style="color: #FF0000; font-size: 1.3rem;">8502</span>
        </p>
        <p style="color: #666; margin: 0; text-align: center; font-size: 0.85rem;">
            ディレクトリ: 8502_記事ネタ提案ツール
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("メニュー")
    page = st.radio(
        "選択してください",
        ["💡 記事ネタ提案", "⚙️ 設定"]
    )

    # データ読み込み状況を表示
    if st.session_state.df is not None:
        st.success(f"✅ データ読み込み済み: {len(st.session_state.df)}件")
        if st.button("データをクリア"):
            st.session_state.df = None
            st.session_state.df_numeric = None
            st.session_state.selected_sheet = None
            st.rerun()

    # バージョン情報（サイドバー下部）
    st.markdown("---")
    st.caption(f"Version {VERSION}")
    st.caption(f"Updated: {VERSION_DATE}")

# 記事ネタ提案ページ
if page == "💡 記事ネタ提案":
    # APIキーを取得（Streamlit Cloud対応）
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.getenv('ANTHROPIC_API_KEY') or st.session_state.get('api_key')
    render_article_analysis_page(api_key)

# データ分析ページ（削除予定 - 後方互換性のため残す）
elif page == "📊 データ分析":
    st.header("LINE配信データ分析")

    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "愛カツLINE配信シートをアップロード",
        type=['xlsx', 'xls'],
        help="LINE配信シートのExcelファイルをアップロードしてください",
        key="file_uploader"
    )

    if uploaded_file is not None:
        try:
            # Excelファイルのシート一覧を取得
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names

            # シート選択
            default_index = sheet_names.index("LINE配信シート") if "LINE配信シート" in sheet_names else 0
            selected_sheet = st.selectbox(
                "分析するシートを選択",
                sheet_names,
                index=default_index
            )

            # シートが変更された、または初回読み込みの場合
            if st.session_state.selected_sheet != selected_sheet or st.session_state.df is None:
                # データ読み込み
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                st.session_state.selected_sheet = selected_sheet

                # カラムの正規化（改行を削除）
                df.columns = [col.replace('\n', '') if isinstance(col, str) else col for col in df.columns]

                # データの前処理：数値カラムを変換
                if 'LINEアクセス' in df.columns:
                    df['LINEアクセス_num'] = pd.to_numeric(df['LINEアクセス'], errors='coerce')

                if 'LINECTR' in df.columns:
                    df['LINECTR_num'] = pd.to_numeric(df['LINECTR'], errors='coerce')

                if 'LINES' in df.columns:
                    df['LINES_num'] = pd.to_numeric(df['LINES'], errors='coerce')

                # 数値データのみのDataFrameを作成
                if 'LINEアクセス_num' in df.columns:
                    df_numeric = df[df['LINEアクセス_num'].notna()].copy()
                else:
                    df_numeric = df.copy()

                # セッション状態に保存
                st.session_state.df = df
                st.session_state.df_numeric = df_numeric

                st.success(f"✅ データ読み込み完了: {len(df)}件の記事")

            # セッション状態からデータを取得
            df = st.session_state.df
            df_numeric = st.session_state.df_numeric

            # データプレビュー
            with st.expander("📋 データプレビュー（最初の10行）"):
                st.dataframe(df.head(10))

            # 基本統計
            st.subheader("📈 基本統計")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("総記事数", f"{len(df):,}件")

            with col2:
                if 'LINEアクセス_num' in df.columns:
                    avg_access = df['LINEアクセス_num'].mean()
                    st.metric("平均アクセス", f"{avg_access:,.0f}")

            with col3:
                if 'LINEアクセス_num' in df.columns:
                    total_access = df['LINEアクセス_num'].sum()
                    st.metric("総アクセス", f"{total_access:,.0f}")

            with col4:
                if 'LINECTR_num' in df.columns:
                    avg_ctr = df['LINECTR_num'].mean()
                    st.metric("平均CTR", f"{avg_ctr:.4f}")

            # アクセス分布
            if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
                st.subheader("📊 アクセス分布")

                col1, col2 = st.columns(2)

                with col1:
                    # ヒストグラム
                    fig_hist = px.histogram(
                        df_numeric,
                        x='LINEアクセス_num',
                        nbins=50,
                        title="アクセス数分布",
                        labels={'LINEアクセス_num': 'LINEアクセス数', 'count': '記事数'}
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

                with col2:
                    # ボックスプロット
                    fig_box = px.box(
                        df_numeric,
                        y='LINEアクセス_num',
                        title="アクセス数ボックスプロット",
                        labels={'LINEアクセス_num': 'LINEアクセス数'}
                    )
                    st.plotly_chart(fig_box, use_container_width=True)

            # ジャンル別分析
            if 'ジャンル①' in df.columns:
                st.subheader("🏷️ ジャンル別分析")

                col1, col2 = st.columns(2)

                with col1:
                    # ジャンル別記事数
                    genre_counts = df['ジャンル①'].value_counts()
                    fig_genre = px.pie(
                        values=genre_counts.values,
                        names=genre_counts.index,
                        title="ジャンル別記事数"
                    )
                    st.plotly_chart(fig_genre, use_container_width=True)

                with col2:
                    # ジャンル別平均アクセス
                    if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
                        genre_access = df_numeric.groupby('ジャンル①')['LINEアクセス_num'].mean().sort_values(ascending=False)
                        fig_genre_access = px.bar(
                            x=genre_access.index,
                            y=genre_access.values,
                            title="ジャンル別平均アクセス",
                            labels={'x': 'ジャンル', 'y': '平均アクセス'}
                        )
                        st.plotly_chart(fig_genre_access, use_container_width=True)

            # 記事種別分析
            if '記事種別' in df.columns:
                st.subheader("📝 記事種別分析")

                col1, col2 = st.columns(2)

                with col1:
                    # 記事種別ごとの記事数
                    type_counts = df['記事種別'].value_counts()
                    fig_type = px.bar(
                        x=type_counts.index,
                        y=type_counts.values,
                        title="記事種別ごとの記事数",
                        labels={'x': '記事種別', 'y': '記事数'}
                    )
                    st.plotly_chart(fig_type, use_container_width=True)

                with col2:
                    # 記事種別ごとの平均アクセス
                    if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
                        type_access = df_numeric.groupby('記事種別')['LINEアクセス_num'].mean().sort_values(ascending=False)
                        fig_type_access = px.bar(
                            x=type_access.index,
                            y=type_access.values,
                            title="記事種別ごとの平均アクセス",
                            labels={'x': '記事種別', 'y': '平均アクセス'}
                        )
                        st.plotly_chart(fig_type_access, use_container_width=True)

            # ヒット記事分析
            st.subheader("🔥 ヒット記事 Top 20")

            if 'LINEアクセス_num' in df_numeric.columns and 'タイトル' in df_numeric.columns and len(df_numeric) > 0:
                # 上位20記事
                top_20 = df_numeric.nlargest(20, 'LINEアクセス_num')

                display_cols = ['タイトル', 'LINEアクセス_num']
                if 'ジャンル①' in top_20.columns:
                    display_cols.append('ジャンル①')
                if '記事種別' in top_20.columns:
                    display_cols.append('記事種別')
                if 'LINECTR_num' in top_20.columns:
                    display_cols.append('LINECTR_num')

                display_df = top_20[display_cols].copy()
                display_df['順位'] = range(1, len(top_20) + 1)

                # カラム名を見やすく変更
                display_df = display_df.rename(columns={
                    'LINEアクセス_num': 'LINEアクセス',
                    'LINECTR_num': 'LINE CTR'
                })

                # 順位を最初に
                cols = ['順位'] + [col for col in display_df.columns if col != '順位']
                display_df = display_df[cols]

                st.dataframe(display_df, use_container_width=True)

                # タイトル分析
                st.write("### タイトルの特徴分析")

                col1, col2 = st.columns(2)

                with col1:
                    # 平均文字数
                    top_20['title_length'] = top_20['タイトル'].astype(str).str.len()
                    avg_length = top_20['title_length'].mean()
                    median_length = top_20['title_length'].median()
                    st.metric("平均タイトル文字数", f"{avg_length:.1f}文字")
                    st.metric("中央値タイトル文字数", f"{median_length:.1f}文字")

                with col2:
                    # 頻出キーワード
                    st.write("#### 頻出キーワード（Top 15）")
                    all_titles = ' '.join(top_20['タイトル'].astype(str))

                    # 特殊記号と数字を除外
                    words = re.findall(r'[ぁ-んァ-ヶー一-龥]+', all_titles)
                    # 2文字以上のワードのみ
                    word_counts = Counter([w for w in words if len(w) >= 2])

                    for word, count in word_counts.most_common(15):
                        st.write(f"- **{word}**: {count}回")

        except Exception as e:
            st.error(f"エラー: {e}")
            import traceback
            st.code(traceback.format_exc())

    # ファイルアップロードがない場合でもセッション状態にデータがあれば表示
    if st.session_state.df is not None and uploaded_file is None:
        st.info("💡 保存済みのデータを表示しています。新しいデータをアップロードする場合は上のアップローダーを使用してください。")

        # セッション状態からデータを取得
        df = st.session_state.df
        df_numeric = st.session_state.df_numeric

        # データプレビュー
        with st.expander("📋 データプレビュー（最初の10行）"):
            st.dataframe(df.head(10))

        # 以下、分析表示（uploaded_file is not Noneの場合と同じ）
        # 基本統計
        st.subheader("📈 基本統計")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総記事数", f"{len(df):,}件")

        with col2:
            if 'LINEアクセス_num' in df.columns:
                avg_access = df['LINEアクセス_num'].mean()
                st.metric("平均アクセス", f"{avg_access:,.0f}")

        with col3:
            if 'LINEアクセス_num' in df.columns:
                total_access = df['LINEアクセス_num'].sum()
                st.metric("総アクセス", f"{total_access:,.0f}")

        with col4:
            if 'LINECTR_num' in df.columns:
                avg_ctr = df['LINECTR_num'].mean()
                st.metric("平均CTR", f"{avg_ctr:.4f}")

        # アクセス分布
        if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
            st.subheader("📊 アクセス分布")

            col1, col2 = st.columns(2)

            with col1:
                # ヒストグラム
                fig_hist = px.histogram(
                    df_numeric,
                    x='LINEアクセス_num',
                    nbins=50,
                    title="アクセス数分布",
                    labels={'LINEアクセス_num': 'LINEアクセス数', 'count': '記事数'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                # ボックスプロット
                fig_box = px.box(
                    df_numeric,
                    y='LINEアクセス_num',
                    title="アクセス数ボックスプロット",
                    labels={'LINEアクセス_num': 'LINEアクセス数'}
                )
                st.plotly_chart(fig_box, use_container_width=True)

        # ジャンル別分析
        if 'ジャンル①' in df.columns:
            st.subheader("🏷️ ジャンル別分析")

            col1, col2 = st.columns(2)

            with col1:
                # ジャンル別記事数
                genre_counts = df['ジャンル①'].value_counts()
                fig_genre = px.pie(
                    values=genre_counts.values,
                    names=genre_counts.index,
                    title="ジャンル別記事数"
                )
                st.plotly_chart(fig_genre, use_container_width=True)

            with col2:
                # ジャンル別平均アクセス
                if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
                    genre_access = df_numeric.groupby('ジャンル①')['LINEアクセス_num'].mean().sort_values(ascending=False)
                    fig_genre_access = px.bar(
                        x=genre_access.index,
                        y=genre_access.values,
                        title="ジャンル別平均アクセス",
                        labels={'x': 'ジャンル', 'y': '平均アクセス'}
                    )
                    st.plotly_chart(fig_genre_access, use_container_width=True)

        # 記事種別分析
        if '記事種別' in df.columns:
            st.subheader("📝 記事種別分析")

            col1, col2 = st.columns(2)

            with col1:
                # 記事種別ごとの記事数
                type_counts = df['記事種別'].value_counts()
                fig_type = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="記事種別ごとの記事数",
                    labels={'x': '記事種別', 'y': '記事数'}
                )
                st.plotly_chart(fig_type, use_container_width=True)

            with col2:
                # 記事種別ごとの平均アクセス
                if 'LINEアクセス_num' in df_numeric.columns and len(df_numeric) > 0:
                    type_access = df_numeric.groupby('記事種別')['LINEアクセス_num'].mean().sort_values(ascending=False)
                    fig_type_access = px.bar(
                        x=type_access.index,
                        y=type_access.values,
                        title="記事種別ごとの平均アクセス",
                        labels={'x': '記事種別', 'y': '平均アクセス'}
                    )
                    st.plotly_chart(fig_type_access, use_container_width=True)

        # ヒット記事分析
        st.subheader("🔥 ヒット記事 Top 20")

        if 'LINEアクセス_num' in df_numeric.columns and 'タイトル' in df_numeric.columns and len(df_numeric) > 0:
            # 上位20記事
            top_20 = df_numeric.nlargest(20, 'LINEアクセス_num')

            display_cols = ['タイトル', 'LINEアクセス_num']
            if 'ジャンル①' in top_20.columns:
                display_cols.append('ジャンル①')
            if '記事種別' in top_20.columns:
                display_cols.append('記事種別')
            if 'LINECTR_num' in top_20.columns:
                display_cols.append('LINECTR_num')

            display_df = top_20[display_cols].copy()
            display_df['順位'] = range(1, len(top_20) + 1)

            # カラム名を見やすく変更
            display_df = display_df.rename(columns={
                'LINEアクセス_num': 'LINEアクセス',
                'LINECTR_num': 'LINE CTR'
            })

            # 順位を最初に
            cols = ['順位'] + [col for col in display_df.columns if col != '順位']
            display_df = display_df[cols]

            st.dataframe(display_df, use_container_width=True)

            # タイトル分析
            st.write("### タイトルの特徴分析")

            col1, col2 = st.columns(2)

            with col1:
                # 平均文字数
                top_20['title_length'] = top_20['タイトル'].astype(str).str.len()
                avg_length = top_20['title_length'].mean()
                median_length = top_20['title_length'].median()
                st.metric("平均タイトル文字数", f"{avg_length:.1f}文字")
                st.metric("中央値タイトル文字数", f"{median_length:.1f}文字")

            with col2:
                # 頻出キーワード
                st.write("#### 頻出キーワード（Top 15）")
                all_titles = ' '.join(top_20['タイトル'].astype(str))

                # 特殊記号と数字を除外
                words = re.findall(r'[ぁ-んァ-ヶー一-龥]+', all_titles)
                # 2文字以上のワードのみ
                word_counts = Counter([w for w in words if len(w) >= 2])

                for word, count in word_counts.most_common(15):
                    st.write(f"- **{word}**: {count}回")

    elif uploaded_file is None:
        st.info("👆 愛カツLINE配信シートをアップロードしてください")

# ヒットパターン分析ページ
elif page == "🔍 ヒットパターン分析":
    st.header("ヒットパターン分析")

    if st.session_state.df is not None and st.session_state.df_numeric is not None:
        df = st.session_state.df
        df_numeric = st.session_state.df_numeric

        st.success(f"✅ データ使用中: {len(df)}件の記事")

        # ヒットパターン分析の実装
        st.subheader("🔥 ヒット記事のパターン分析")

        if 'LINEアクセス_num' in df_numeric.columns and 'タイトル' in df_numeric.columns:
            # 上位10%の記事を抽出
            threshold = df_numeric['LINEアクセス_num'].quantile(0.9)
            hit_articles = df_numeric[df_numeric['LINEアクセス_num'] >= threshold]

            st.write(f"### 上位10%の記事（{len(hit_articles)}件）")

            # タイトルパターン分析
            col1, col2 = st.columns(2)

            with col1:
                st.write("#### タイトルの特徴")
                hit_articles['title_length'] = hit_articles['タイトル'].astype(str).str.len()
                avg_length = hit_articles['title_length'].mean()
                st.metric("平均文字数", f"{avg_length:.1f}文字")

                # 記号の使用率
                hit_articles['has_brackets'] = hit_articles['タイトル'].astype(str).str.contains('【|】')
                brackets_rate = hit_articles['has_brackets'].mean()
                st.metric("【】使用率", f"{brackets_rate*100:.1f}%")

                hit_articles['has_emoji'] = hit_articles['タイトル'].astype(str).str.contains('💔|❤️|😭|😱')
                emoji_rate = hit_articles['has_emoji'].mean()
                st.metric("絵文字使用率", f"{emoji_rate*100:.1f}%")

            with col2:
                st.write("#### 頻出キーワード（Top 20）")
                all_titles = ' '.join(hit_articles['タイトル'].astype(str))
                words = re.findall(r'[ぁ-んァ-ヶー一-龥]+', all_titles)
                word_counts = Counter([w for w in words if len(w) >= 2])

                for word, count in word_counts.most_common(20):
                    st.write(f"- **{word}**: {count}回")

    else:
        st.info("📊 先にデータ分析ページでデータをアップロードしてください")

# 新テーマ提案ページ
elif page == "💡 新テーマ提案":
    st.header("新テーマ提案 - ヒットパターンから広がる可能性")

    # API key確認
    api_key = st.secrets.get('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or st.session_state.get('api_key')

    if not api_key:
        st.warning("⚠️ Anthropic API Keyが設定されていません。「⚙️ 設定」から設定してください。")
    elif st.session_state.df is None:
        st.info("📊 先にデータ分析ページでデータをアップロードしてください")
    else:
        df = st.session_state.df
        df_numeric = st.session_state.df_numeric

        st.write("過去のヒットデータを分析して、新しいテーマの可能性を提案します。")
        st.write("**「隣地」** = 既存ヒットテーマに近い安全な拡張 | **「飛び地」** = 少し冒険的な新領域")

        # ヒットデータの分析
        st.subheader("📊 現在のヒットパターン")

        col1, col2, col3 = st.columns(3)

        with col1:
            if 'ジャンル①' in df_numeric.columns and 'LINEアクセス_num' in df_numeric.columns:
                genre_performance = df_numeric.groupby('ジャンル①')['LINEアクセス_num'].agg(['mean', 'count']).sort_values('mean', ascending=False)
                st.write("**ジャンル別パフォーマンス**")
                for genre, row in genre_performance.head(5).iterrows():
                    st.write(f"- **{genre}**: 平均{row['mean']:,.0f} ({row['count']}件)")

        with col2:
            if 'ジャンル②' in df_numeric.columns:
                theme_performance = df_numeric.groupby('ジャンル②')['LINEアクセス_num'].agg(['mean', 'count']).sort_values('mean', ascending=False)
                st.write("**テーマ別パフォーマンス**")
                for theme, row in theme_performance.head(5).iterrows():
                    st.write(f"- **{theme}**: 平均{row['mean']:,.0f} ({row['count']}件)")

        with col3:
            if '記事種別' in df_numeric.columns:
                type_performance = df_numeric.groupby('記事種別')['LINEアクセス_num'].agg(['mean', 'count']).sort_values('mean', ascending=False)
                st.write("**記事種別パフォーマンス**")
                for article_type, row in type_performance.head(5).iterrows():
                    st.write(f"- **{article_type}**: 平均{row['mean']:,.0f} ({row['count']}件)")

        st.markdown("---")

        # 新テーマ提案生成
        st.subheader("💡 AIによる新テーマ提案")

        expansion_type = st.radio(
            "提案タイプを選択",
            ["🎯 隣地拡張（安全な方向）", "🚀 飛び地挑戦（冒険的な方向）", "🎨 両方提案"]
        )

        num_suggestions = st.slider("提案数", 3, 10, 5)

        if st.button("新テーマを提案"):
            with st.spinner("AIが新しいテーマを考案中..."):
                try:
                    client = Anthropic(api_key=api_key)

                    # ヒットデータのサマリー作成
                    genre_summary = ""
                    if 'ジャンル①' in df_numeric.columns:
                        top_genres = df_numeric.groupby('ジャンル①')['LINEアクセス_num'].mean().sort_values(ascending=False).head(5)
                        genre_summary = ", ".join([f"{g}({v:,.0f}PV)" for g, v in top_genres.items()])

                    theme_summary = ""
                    if 'ジャンル②' in df_numeric.columns:
                        top_themes = df_numeric.groupby('ジャンル②')['LINEアクセス_num'].mean().sort_values(ascending=False).head(5)
                        theme_summary = ", ".join([f"{t}({v:,.0f}PV)" for t, v in top_themes.items()])

                    # 上位記事のタイトルサンプル
                    top_titles = df_numeric.nlargest(10, 'LINEアクセス_num')['タイトル'].tolist()
                    title_examples = "\n".join([f"- {t}" for t in top_titles[:5]])

                    # 展開方向の指示
                    if expansion_type == "🎯 隣地拡張（安全な方向）":
                        direction = """
**隣地拡張**: 既存のヒットテーマに近い、安全で確実性の高い拡張を提案してください。
- 既存ジャンル×新しいシチュエーション
- 既存テーマの別の切り口
- 人気記事の続編・派生パターン
"""
                    elif expansion_type == "🚀 飛び地挑戦（冒険的な方向）":
                        direction = """
**飛び地挑戦**: 既存のヒットから少し離れた、新しい可能性を提案してください。
- まだ扱っていない新ジャンル
- 意外な組み合わせ
- トレンドを先取りするテーマ
"""
                    else:
                        direction = """
**両方の提案**:
1. 隣地拡張（3-4個）: 既存のヒットに近い安全な拡張
2. 飛び地挑戦（2-3個）: 少し冒険的な新領域
"""

                    prompt = f"""あなたは愛カツの編集長です。過去のヒットデータを分析して、新しい記事テーマを提案してください。

【現在のヒットパターン】
◆ 人気ジャンル: {genre_summary}
◆ 人気テーマ: {theme_summary}

◆ ヒット記事タイトル例:
{title_examples}

{direction}

【提案形式】
{num_suggestions}個の新テーマを以下の形式で提案してください：

## [提案タイプ: 隣地 or 飛び地]

### 1. [テーマタイトル]
**ジャンル**: [ジャンル名]
**テーマ**: [テーマ名]
**なぜヒットしそうか**: [2-3行で理由を説明]
**記事タイトル例**: [実際の記事タイトル風の例を1つ]

---

【重要】
- 愛カツの読者（20-40代女性）が共感できるテーマ
- スカッと、感動、ハラハラなど感情を動かす要素
- 実体験風のリアリティ
- SNSでシェアしたくなる要素"""

                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=4000,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )

                    suggestions = message.content[0].text

                    # 結果表示
                    st.success("✅ 新テーマ提案が完成しました！")
                    st.markdown("---")
                    st.markdown(suggestions)

                    # ダウンロードボタン
                    st.download_button(
                        label="📥 提案をダウンロード",
                        data=suggestions,
                        file_name=f"theme_suggestions_{expansion_type}.md",
                        mime="text/markdown"
                    )

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# シナリオ生成ページ
elif page == "🤖 シナリオ生成":
    st.header("AI漫画シナリオ生成")

    # データがある場合は情報を表示
    if st.session_state.df is not None:
        df = st.session_state.df
        df_numeric = st.session_state.df_numeric

        with st.expander("📊 データに基づく推奨設定"):
            if 'ジャンル①' in df.columns:
                top_genres = df['ジャンル①'].value_counts().head(3)
                st.write("**人気ジャンル Top 3:**")
                for genre, count in top_genres.items():
                    st.write(f"- {genre}: {count}件")

            if 'ジャンル②' in df.columns:
                top_themes = df['ジャンル②'].value_counts().head(3)
                st.write("\n**人気テーマ Top 3:**")
                for theme, count in top_themes.items():
                    st.write(f"- {theme}: {count}件")

    # API key確認（Streamlit Cloud対応）
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.getenv('ANTHROPIC_API_KEY') or st.session_state.get('api_key')

    if not api_key:
        st.warning("⚠️ Anthropic API Keyが設定されていません。「⚙️ 設定」から設定してください。")
    else:
        st.success("✅ API Key設定済み")

        # ネタ要素JSONファイルを読み込み
        neta_file_path = os.path.join(os.path.dirname(__file__), 'data', 'neta_elements.json')

        try:
            with open(neta_file_path, 'r', encoding='utf-8') as f:
                neta_data = json.load(f)
        except FileNotFoundError:
            neta_data = None

        # シナリオ生成フォーム
        with st.form("scenario_form"):
            st.subheader("🎬 シナリオ生成設定")

            if neta_data:
                st.info(f"💡 ネタ管理から {sum(len(cat['elements']) for cat in neta_data['categories'].values())} 個の要素を活用できます")

            st.markdown("---")
            st.markdown("### 📝 基本設定（ネタ管理と連動）")

            # トーン/雰囲気（ネタ管理から）
            col1, col2 = st.columns(2)

            with col1:
                if neta_data and 'tones' in neta_data['categories']:
                    tone_elements = neta_data['categories']['tones']['elements']
                    tone_options = [f"{elem.get('name', elem.get('id'))} {elem.get('mood', '')}" for elem in tone_elements]
                    tone_options.append("🎲 AIにおまかせ")

                    selected_tone = st.selectbox(
                        "😊 雰囲気・トーン",
                        tone_options,
                        help="記事全体の雰囲気を選択"
                    )
                else:
                    selected_tone = st.selectbox(
                        "😊 雰囲気・トーン",
                        ["スカッと", "感動", "ハラハラ", "ほのぼの", "🎲 AIにおまかせ"]
                    )

            with col2:
                # ページ構成
                page_structure = st.selectbox(
                    "📄 ページ数・展開",
                    ["4ページ（超高速展開）", "6ページ（標準）", "8ページ（じっくり）"],
                    index=1,
                    help="漫画のボリュームとテンポ"
                )

            # シチュエーション（ネタ管理から）
            if neta_data and 'situations' in neta_data['categories']:
                situation_elements = neta_data['categories']['situations']['elements']
                situation_options = [elem.get('name', elem.get('id')) for elem in situation_elements]
                situation_options.extend(["🎲 AIにおまかせ", "✏️ カスタム入力..."])

                selected_situation = st.selectbox(
                    "🏠 場面設定・シチュエーション",
                    situation_options,
                    help="ストーリーの舞台となる場面"
                )

                # カスタム入力の場合
                custom_situation = ""
                if selected_situation == "✏️ カスタム入力...":
                    custom_situation = st.text_input(
                        "場面を入力",
                        placeholder="例: 義実家での法事中にトラブル発生"
                    )
            else:
                selected_situation = st.text_input(
                    "🏠 場面設定・シチュエーション",
                    placeholder="例: 義実家での同居開始"
                )
                custom_situation = selected_situation

            # キャラクター（ネタ管理から）
            col3, col4 = st.columns(2)

            with col3:
                if neta_data and 'character_archetypes' in neta_data['categories']:
                    char_elements = neta_data['categories']['character_archetypes']['elements']
                    protagonist_options = [elem.get('name', elem.get('id')) for elem in char_elements if elem.get('type') == 'protagonist']
                    protagonist_options.extend(["🎲 AIにおまかせ", "✏️ カスタム入力..."])

                    selected_protagonist = st.selectbox(
                        "👤 主人公タイプ",
                        protagonist_options,
                        help="主人公のキャラクター性"
                    )

                    custom_protagonist = ""
                    if selected_protagonist == "✏️ カスタム入力...":
                        custom_protagonist = st.text_input(
                            "主人公を入力",
                            placeholder="例: 30代主婦、我慢強い性格"
                        )
                else:
                    selected_protagonist = st.text_input(
                        "👤 主人公タイプ",
                        placeholder="例: 我慢強い主婦"
                    )
                    custom_protagonist = selected_protagonist

            with col4:
                if neta_data and 'character_archetypes' in neta_data['categories']:
                    antagonist_options = [elem.get('name', elem.get('id')) for elem in char_elements if elem.get('type') == 'antagonist']
                    antagonist_options.extend(["🎲 AIにおまかせ", "✏️ カスタム入力..."])

                    selected_antagonist = st.selectbox(
                        "👿 敵対者タイプ",
                        antagonist_options,
                        help="対立する人物のキャラクター性"
                    )

                    custom_antagonist = ""
                    if selected_antagonist == "✏️ カスタム入力...":
                        custom_antagonist = st.text_input(
                            "敵対者を入力",
                            placeholder="例: マウント取る義姉"
                        )
                else:
                    selected_antagonist = st.text_input(
                        "👿 敵対者タイプ",
                        placeholder="例: 無神経な義母"
                    )
                    custom_antagonist = selected_antagonist

            # オチ/結末（ネタ管理から）
            if neta_data and 'ending_types' in neta_data['categories']:
                ending_elements = neta_data['categories']['ending_types']['elements']
                ending_options = [elem.get('name', elem.get('id')) for elem in ending_elements]
                ending_options.append("🎲 AIにおまかせ")

                selected_ending = st.selectbox(
                    "🎬 オチ・結末のパターン",
                    ending_options,
                    help="ストーリーの締めくくり方"
                )
            else:
                selected_ending = st.selectbox(
                    "🎬 オチ・結末のパターン",
                    ["スカッと復讐", "感動の和解", "因果応報", "逆転勝利", "🎲 AIにおまかせ"]
                )

            # 詳細設定（折りたたみ可能）
            with st.expander("⚙️ 詳細設定（オプション）"):
                st.markdown("#### ターゲット設定")
                col5, col6 = st.columns(2)

                with col5:
                    target_audience = st.selectbox(
                        "読者層",
                        ["20代女性", "30代主婦", "40代女性", "全年代"],
                        index=1
                    )

                with col6:
                    article_goal = st.selectbox(
                        "記事の目的",
                        ["PV最大化（バズ狙い）", "エンゲージメント（共感）", "シェア獲得（話題性）"]
                    )

                st.markdown("#### 展開の調整")
                col7, col8 = st.columns(2)

                with col7:
                    surprise_level = st.slider(
                        "意外性レベル",
                        min_value=1, max_value=5, value=3,
                        help="1=安全な展開、5=超意外な展開"
                    )

                with col8:
                    reality_level = st.slider(
                        "リアリティレベル",
                        min_value=1, max_value=5, value=3,
                        help="1=ありえる話、5=極端な設定"
                    )

            # 追加の指示
            additional_notes = st.text_area(
                "💬 追加の指示・要望（任意）",
                placeholder="例: 主人公は結婚3年目、子供なし。最後は夫が覚醒して主人公の味方になる展開で",
                height=100
            )

            st.markdown("---")
            submitted = st.form_submit_button("🚀 シナリオ生成", use_container_width=True)

            if submitted:
                with st.spinner("シナリオを生成中..."):
                    try:
                        # 選択された要素を整理
                        # トーン
                        final_tone = selected_tone if "AIにおまかせ" not in selected_tone else None

                        # シチュエーション
                        if selected_situation == "✏️ カスタム入力...":
                            final_situation = custom_situation
                        elif selected_situation == "🎲 AIにおまかせ":
                            final_situation = None
                        else:
                            final_situation = selected_situation

                        # 主人公
                        if selected_protagonist == "✏️ カスタム入力...":
                            final_protagonist = custom_protagonist
                        elif selected_protagonist == "🎲 AIにおまかせ":
                            final_protagonist = None
                        else:
                            final_protagonist = selected_protagonist

                        # 敵対者
                        if selected_antagonist == "✏️ カスタム入力...":
                            final_antagonist = custom_antagonist
                        elif selected_antagonist == "🎲 AIにおまかせ":
                            final_antagonist = None
                        else:
                            final_antagonist = selected_antagonist

                        # オチ
                        final_ending = selected_ending if "AIにおまかせ" not in selected_ending else None

                        # ネタ要素DBから追加情報を取得
                        neta_elements_text = ""
                        hit_data_text = ""

                        if neta_data:
                            # ネタ要素を構築
                            neta_parts = []

                            # セリフパターン（ランダムに2-3個選択）
                            dialogues = neta_data['categories']['dialogue_patterns']['elements']
                            if dialogues:
                                selected_dialogues = random.sample(dialogues, min(2, len(dialogues)))
                                neta_parts.append("**セリフ参考例:**")
                                for dlg in selected_dialogues:
                                    if 'examples' in dlg:
                                        for ex in dlg['examples'][:2]:
                                            neta_parts.append(f"  - 「{ex}」")

                            # タイトル要素（ランダム選択）
                            if neta_data['categories']['title_elements']['elements']:
                                title_hook = random.choice(neta_data['categories']['title_elements']['elements'])
                                if 'examples' in title_hook:
                                    neta_parts.append(f"**タイトル要素:** {', '.join(title_hook['examples'][:3])}")

                            # 展開テンポ（ページ数に応じて）
                            if neta_data['categories']['pacing_patterns']['elements']:
                                pacing = random.choice(neta_data['categories']['pacing_patterns']['elements'])
                                neta_parts.append(f"**構成:** {pacing.get('structure', '')} ({pacing.get('name', '')})")

                            neta_elements_text = "\n".join(neta_parts)

                        # ヒットデータの情報（データがある場合）
                        if st.session_state.df is not None:
                            df = st.session_state.df
                            hit_parts = []

                            # ヒット記事のタイトル例（Top 5）
                            if 'タイトル' in df.columns and 'LINEアクセス_num' in df.columns:
                                top_titles = df.nlargest(5, 'LINEアクセス_num')['タイトル'].tolist()
                                hit_parts.append("**ヒット記事タイトル例:**")
                                for title in top_titles[:3]:
                                    hit_parts.append(f"  - {title}")

                            if hit_parts:
                                hit_data_text = "\n".join(hit_parts)

                        # Claude APIでシナリオ生成
                        client = Anthropic(api_key=api_key)

                        # ページ数抽出
                        page_num = page_structure.split("ページ")[0]

                        # 意外性・リアリティの説明
                        surprise_desc = ["安全な展開", "やや意外", "普通の意外性", "かなり意外", "超意外な展開"][surprise_level-1]
                        reality_desc = ["完全にありえる話", "少し盛る", "程よく盛る", "かなり盛る", "極端な設定"][reality_level-1]

                        # プロンプト構築
                        prompt_parts = [
                            "あなたはWEBメディア「愛カツ」の漫画記事ライターです。",
                            "以下の条件で漫画記事のシナリオを生成してください。",
                            "",
                            "【基本設定】"
                        ]

                        # 選択された要素を追加
                        if final_tone:
                            prompt_parts.append(f"- 雰囲気・トーン: {final_tone}")
                        if final_situation:
                            prompt_parts.append(f"- 場面設定: {final_situation}")
                        if final_protagonist:
                            prompt_parts.append(f"- 主人公: {final_protagonist}")
                        if final_antagonist:
                            prompt_parts.append(f"- 敵対者: {final_antagonist}")
                        if final_ending:
                            prompt_parts.append(f"- オチ/結末: {final_ending}")

                        prompt_parts.extend([
                            f"- ページ数: {page_structure}",
                            "",
                            "【戦略設定】",
                            f"- ターゲット読者: {target_audience}",
                            f"- 記事の目的: {article_goal}",
                            f"- 意外性レベル: {surprise_desc}",
                            f"- リアリティレベル: {reality_desc}"
                        ])

                        if additional_notes:
                            prompt_parts.append(f"- 追加要望: {additional_notes}")

                        if neta_elements_text:
                            prompt_parts.extend([
                                "",
                                "【参考にするネタ要素】",
                                neta_elements_text
                            ])

                        if hit_data_text:
                            prompt_parts.extend([
                                "",
                                "【過去のヒット記事（参考）】",
                                hit_data_text
                            ])

                        prompt_parts.extend([
                            "",
                            "【出力形式】",
                            "1. 記事タイトル",
                            "   - LINEで配信する際のキャッチーなタイトル（60-80文字程度）",
                            "   - 【】や💔などの記号を効果的に使用",
                            "   - 具体的な数字や状況を含める",
                            "",
                            "2. 起承転結の4部構成",
                            "   各部について以下を記載：",
                            "   - 場面説明（具体的に）",
                            "   - 主要な展開",
                            "   - キャラクターのセリフ（3-5個、リアルで印象的なもの）",
                            "   - 心理描写",
                            "",
                            "3. オチ・結末",
                            "   - 読者に響くメッセージ",
                            "   - スカッとするまたは感動的な結末",
                            "",
                            "【愛カツの特徴とヒットの法則】",
                            "- 女性読者がメインターゲット（20-40代）",
                            "- スカッとする展開や共感できるストーリーが人気",
                            "- 実体験風のリアリティが重要（具体的な年齢・金額・状況を含める）",
                            "- 起承転結がはっきりしている",
                            "",
                            "【戦略設定に基づく執筆方針】",
                            f"- **ターゲット（{target_audience}）**に刺さる言葉選びと設定",
                            f"- **目的（{article_goal}）**を達成するための展開とトーン",
                            f"- **{page_num}ページ構成**で完結する適切な情報量",
                            f"- **意外性レベル（{surprise_desc}）**に合わせた展開の予測可能性",
                            f"- **リアリティレベル（{reality_desc}）**に合わせた設定の極端さ",
                            "",
                            "上記すべてを踏まえて、戦略設定に沿った魅力的なシナリオを生成してください。"
                        ])

                        prompt = "\n".join(prompt_parts)

                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4000,
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )

                        scenario = message.content[0].text

                        # セッション状態に保存
                        st.session_state.generated_scenario = scenario

                        # ファイル名用の識別子を生成
                        filename_parts = []
                        if final_tone:
                            filename_parts.append(final_tone.split()[0])  # 最初の単語だけ
                        if final_situation:
                            filename_parts.append(final_situation[:10])  # 最初の10文字
                        filename_str = "_".join(filename_parts) if filename_parts else "scenario"

                        st.session_state.scenario_filename = f"scenario_{filename_str}.md"
                        st.session_state.scenario_params = {
                            'tone': final_tone or 'AIおまかせ',
                            'situation': final_situation or 'AIおまかせ',
                            'protagonist': final_protagonist or 'AIおまかせ',
                            'antagonist': final_antagonist or 'AIおまかせ',
                            'ending': final_ending or 'AIおまかせ',
                            'target_audience': target_audience,
                            'article_goal': article_goal,
                            'page_structure': page_structure,
                            'surprise_level': surprise_level,
                            'reality_level': reality_level
                        }

                        # 使用したネタ要素を保存
                        if neta_elements_text:
                            st.session_state.used_neta_elements = neta_elements_text
                        else:
                            st.session_state.used_neta_elements = None

                        # ヒットデータを保存
                        if hit_data_text:
                            st.session_state.used_hit_data = hit_data_text
                        else:
                            st.session_state.used_hit_data = None

                        # 結果表示
                        st.success("✅ シナリオ生成完了！")

                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        # フォームの外でシナリオ表示とダウンロードボタン
        if 'generated_scenario' in st.session_state:
            st.markdown("---")
            st.subheader("生成されたシナリオ")

            # 生成条件表示
            if 'scenario_params' in st.session_state:
                params = st.session_state.scenario_params

                # 基本設定
                st.markdown("**📋 生成設定**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**雰囲気・トーン:** {params.get('tone', 'N/A')}")
                    st.markdown(f"**場面設定:** {params.get('situation', 'N/A')}")
                    st.markdown(f"**主人公:** {params.get('protagonist', 'N/A')}")
                with col2:
                    st.markdown(f"**敵対者:** {params.get('antagonist', 'N/A')}")
                    st.markdown(f"**オチ:** {params.get('ending', 'N/A')}")
                    st.markdown(f"**ページ数:** {params.get('page_structure', 'N/A')}")

                # 戦略設定
                st.markdown("**⚙️ ターゲット設定**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**読者層:** {params.get('target_audience', 'N/A')}")
                with col2:
                    st.markdown(f"**目的:** {params.get('article_goal', 'N/A')}")
                with col3:
                    st.markdown(f"**意外性Lv.{params.get('surprise_level', 'N/A')} / リアリティLv.{params.get('reality_level', 'N/A')}**")

            # 使用したネタ要素を表示
            col1, col2 = st.columns(2)

            with col1:
                if st.session_state.get('used_neta_elements'):
                    with st.expander("📝 使用したネタ要素", expanded=False):
                        st.markdown(st.session_state.used_neta_elements)

            with col2:
                if st.session_state.get('used_hit_data'):
                    with st.expander("📊 参考にしたヒットデータ", expanded=False):
                        st.markdown(st.session_state.used_hit_data)

            # シナリオ表示
            st.markdown("### シナリオ本文")
            st.markdown(st.session_state.generated_scenario)

            # ダウンロードボタンと保存ボタン
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="📥 シナリオをダウンロード",
                    data=st.session_state.generated_scenario,
                    file_name=st.session_state.scenario_filename,
                    mime="text/markdown",
                    use_container_width=True
                )

            with col2:
                if st.button("💾 シナリオを保存", use_container_width=True, type="secondary"):
                    try:
                        scenario_id = save_scenario(
                            scenario_params=st.session_state.get('scenario_params', {}),
                            scenario_content=st.session_state.get('generated_scenario', '')
                        )
                        st.success(f"✅ シナリオを保存しました！（ID: {scenario_id}）")
                        st.info("💡 下の「📚 保存済みシナリオ」セクションで確認できます")
                    except Exception as e:
                        st.error(f"保存中にエラーが発生しました: {e}")

        # 保存済みシナリオの履歴表示
        st.markdown("---")
        st.subheader("📚 保存済みシナリオ")

        history = load_scenario_history()
        scenarios = history.get('scenarios', [])

        if not scenarios:
            st.info("保存されたシナリオはまだありません。シナリオを生成して「💾 シナリオを保存」ボタンで保存してください。")
        else:
            st.write(f"**保存数: {len(scenarios)}件**")

            # セッション状態で選択中のシナリオを管理
            if 'selected_scenario_id' not in st.session_state:
                st.session_state.selected_scenario_id = None

            # 一覧表示
            for scenario in scenarios:
                with st.container():
                    col1, col2, col3 = st.columns([6, 2, 1])

                    with col1:
                        # タイトルをボタンとして表示（クリックで詳細表示）
                        if st.button(
                            f"📄 {scenario['title']}",
                            key=f"select_scn_{scenario['id']}",
                            use_container_width=True
                        ):
                            st.session_state.selected_scenario_id = scenario['id']
                            st.rerun()

                        # 要約を表示
                        st.caption(f"💬 {scenario['summary']}")

                    with col2:
                        # 作成日時を表示
                        created_at = datetime.datetime.fromisoformat(scenario['created_at'])
                        st.caption(f"📅 {created_at.strftime('%Y/%m/%d %H:%M')}")

                    with col3:
                        # 削除ボタン
                        if st.button("🗑️", key=f"delete_scn_{scenario['id']}", help="削除"):
                            try:
                                delete_scenario(scenario['id'])
                                st.success("削除しました")
                                if st.session_state.selected_scenario_id == scenario['id']:
                                    st.session_state.selected_scenario_id = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"削除中にエラーが発生しました: {e}")

                    st.markdown("---")

            # 選択されたシナリオの詳細表示
            if st.session_state.selected_scenario_id:
                selected_scenario = next(
                    (s for s in scenarios if s['id'] == st.session_state.selected_scenario_id),
                    None
                )

                if selected_scenario:
                    st.markdown("---")
                    st.markdown(f"## 📖 詳細: {selected_scenario['title']}")

                    # 閉じるボタン
                    if st.button("✖️ 閉じる", key="close_scenario"):
                        st.session_state.selected_scenario_id = None
                        st.rerun()

                    st.markdown(f"**作成日時:** {datetime.datetime.fromisoformat(selected_scenario['created_at']).strftime('%Y年%m月%d日 %H:%M')}")

                    # パラメータを表示
                    if selected_scenario.get('parameters'):
                        with st.expander("📋 生成設定", expanded=True):
                            params = selected_scenario['parameters']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**雰囲気:** {params.get('tone', 'N/A')}")
                                st.markdown(f"**場面:** {params.get('situation', 'N/A')}")
                                st.markdown(f"**主人公:** {params.get('protagonist', 'N/A')}")
                            with col2:
                                st.markdown(f"**敵対者:** {params.get('antagonist', 'N/A')}")
                                st.markdown(f"**オチ:** {params.get('ending', 'N/A')}")
                                st.markdown(f"**ページ数:** {params.get('page_structure', 'N/A')}")

                    # シナリオ本文
                    st.markdown("### シナリオ本文")
                    st.markdown(selected_scenario['content'])

                    # ダウンロードボタン
                    st.markdown("---")
                    st.download_button(
                        label="📥 このシナリオをダウンロード",
                        data=selected_scenario['content'],
                        file_name=f"scenario_{selected_scenario['id']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

# ネタ管理ページ
elif page == "📝 ネタ管理":
    st.header("ネタ要素管理")
    st.write("シナリオ生成に使用するネタ要素を管理します。")

    # ネタ要素JSONファイルのパス
    neta_file_path = os.path.join(os.path.dirname(__file__), 'data', 'neta_elements.json')

    # JSONファイルの読み込み
    def load_neta_elements():
        try:
            with open(neta_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            st.error("ネタ要素ファイルが見つかりません")
            return None

    # JSONファイルの保存
    def save_neta_elements(data):
        with open(neta_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    neta_data = load_neta_elements()

    if neta_data:
        # カテゴリ名と日本語名のマッピング
        category_mapping = {
            cat_id: neta_data['categories'][cat_id]['name']
            for cat_id in neta_data['categories']
        }

        # タブで機能を分割
        tab1, tab2, tab3, tab4 = st.tabs(["💡 クイック追加", "📚 使い方ガイド", "📋 要素一覧", "🤖 AI整理"])

        with tab1:
            st.subheader("💡 クイック追加 - 思いついたらすぐメモ！")
            st.info("**カテゴリを気にせず、思いついたネタを自由に書き留めましょう。後でAIが自動で整理してくれます！**")

            # 未整理メモ用のJSONファイルパス
            quick_notes_path = os.path.join(os.path.dirname(__file__), 'data', 'neta_quick_notes.json')

            # 未整理メモの読み込み
            def load_quick_notes():
                try:
                    with open(quick_notes_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except FileNotFoundError:
                    return {"version": "1.0.0", "last_updated": "2025-11-10", "notes": []}

            # 未整理メモの保存
            def save_quick_notes(data):
                os.makedirs(os.path.dirname(quick_notes_path), exist_ok=True)
                with open(quick_notes_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            quick_notes_data = load_quick_notes()

            st.markdown("---")
            st.subheader("✍️ 新しいネタをメモ")

            with st.form("quick_add_form"):
                st.markdown("""
                **例：こんな風に自由に書いてOK！**
                - 読者コメントで見つけた：「義母が出産直後に『もう次の子作らないの？』って言ってきた」
                - 編集会議のアイデア：夫が家族に相談なく転職してた
                - SNSで見たネタ：月収20万で義母に50万要求された
                - ヒット記事のタイトル：【衝撃】3年間の我慢が限界に
                """)

                quick_note = st.text_area(
                    "思いついたネタを自由に入力",
                    placeholder="例：義母が「あなたの稼ぎじゃ生活できない」って言ってきた。これ使えそう！",
                    height=150
                )

                source = st.selectbox(
                    "どこで見つけた？（任意）",
                    ["その他", "読者コメント", "編集会議", "SNS", "ヒット記事", "自分の体験"]
                )

                tags = st.text_input(
                    "タグ（任意・カンマ区切り）",
                    placeholder="例: 義母, モラハラ, セリフ"
                )

                submitted = st.form_submit_button("📝 メモを保存")

                if submitted and quick_note:
                    import datetime

                    # 新しいメモを作成
                    new_note = {
                        "id": f"qn{len(quick_notes_data['notes']) + 1:04d}",
                        "content": quick_note,
                        "source": source,
                        "tags": [t.strip() for t in tags.split(',') if t.strip()] if tags else [],
                        "created_at": datetime.datetime.now().isoformat(),
                        "status": "unprocessed"
                    }

                    # メモを追加
                    quick_notes_data['notes'].append(new_note)
                    quick_notes_data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")

                    # 保存
                    save_quick_notes(quick_notes_data)

                    st.success("✅ メモを保存しました！「🤖 AI整理」タブで自動整理できます。")
                    st.balloons()
                elif submitted:
                    st.warning("ネタを入力してください")

            # 未整理メモ一覧
            st.markdown("---")
            st.subheader("📋 保存済みの未整理メモ")

            unprocessed_notes = [note for note in quick_notes_data['notes'] if note.get('status') == 'unprocessed']

            if unprocessed_notes:
                st.write(f"**未整理: {len(unprocessed_notes)}件**")

                for idx, note in enumerate(unprocessed_notes):
                    with st.expander(f"📝 {note['id']} - {note['content'][:50]}..."):
                        st.write(f"**内容:** {note['content']}")
                        st.write(f"**出典:** {note.get('source', 'その他')}")
                        if note.get('tags'):
                            st.write(f"**タグ:** {', '.join(note['tags'])}")
                        st.write(f"**作成日:** {note.get('created_at', 'N/A')[:10]}")

                        # 削除ボタン
                        if st.button(f"🗑️ 削除", key=f"del_quick_{note['id']}"):
                            quick_notes_data['notes'].remove(note)
                            save_quick_notes(quick_notes_data)
                            st.success("削除しました")
                            st.rerun()
            else:
                st.info("未整理のメモはありません。上のフォームから追加してください！")

        with tab2:
            st.subheader("ネタ管理とは？")
            st.info("**あなたのアイデア・実体験・ヒット記事の要素を蓄積して、AIがそれを使って面白いシナリオを自動生成します！**")

            st.markdown("---")

            st.subheader("💡 何ができるの？")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                **1. アイデアをストック**
                - 編集会議で出たネタ
                - 読者コメントから拾ったリアルな話
                - SNSで見つけた面白いネタ

                **2. ヒット要素を再利用**
                - 過去にウケたパターンを保存
                - 何度でも使える
                - マンネリ防止にも
                """)

            with col2:
                st.markdown("""
                **3. 組み合わせで無限バリエーション**
                - 15カテゴリ × 複数要素
                - AIが自動で組み合わせ
                - 毎回違う、でもウケる記事に

                **4. 使うほど賢くなる**
                - 使用回数を自動カウント
                - ヒット要素を優先使用
                - データが蓄積 → 品質向上
                """)

            st.markdown("---")

            st.subheader("🎯 よく使う5つのカテゴリ（まずはここから！）")

            with st.expander("**1. シチュエーション 🏠 - こんな場面の話を作りたい**", expanded=True):
                st.markdown("""
                **例：**
                - 義実家で法事中にトラブル
                - 夫の浮気相手が義姉だった
                - 妊娠報告したら義母が激怒
                - 同居を突然言い渡された
                """)

            with st.expander("**2. セリフパターン 💬 - このセリフ、使えそう！**"):
                st.markdown("""
                **例：**
                - 「あなたの稼ぎじゃ生活できない」
                - 「私が体調悪いって言ってるのに」
                - 「孫の顔を見せるのが嫁の義務」
                - 「うちの息子に何してくれてんの」
                """)

            with st.expander("**3. キャラクター原型 👥 - こんな人物が登場**"):
                st.markdown("""
                **例：**
                - マウント取る義姉
                - 無関心な夫
                - 口出しばかりする義父
                - 理解ある友人
                """)

            with st.expander("**4. オチ/結末 🎬 - こういう終わり方**"):
                st.markdown("""
                **例：**
                - 義母が周囲から非難される
                - 夫が覚醒して主人公の味方に
                - 証拠を突きつけて勝利
                - 関係修復して和解
                """)

            with st.expander("**5. タイトル要素 📰 - クリックされるフレーズ**"):
                st.markdown("""
                **例：**
                - 【修羅場】【スカッと】
                - 「月収20万なのに50万要求された」
                - 「これって私が悪いの？」
                - 絵文字 💔😭🔥
                """)

            st.markdown("---")

            st.subheader("🔰 迷ったときの選び方")
            st.markdown("""
            | 登録したい内容 | 選ぶカテゴリ | 例 |
            |---|---|---|
            | 場面・状況 | **シチュエーション** | 「義実家で法事中」 |
            | セリフ | **セリフパターン** | 「稼ぎが少ないくせに」 |
            | 登場人物 | **キャラクター原型** | 「マウント義姉」 |
            | 終わり方 | **オチ/結末** | 「因果応報」 |
            | タイトル用 | **タイトル要素** | 「【衝撃】」 |
            """)

            st.markdown("---")

            st.subheader("📝 具体例で理解")

            with st.expander("**例1：読者コメントで見つけたネタ**"):
                st.markdown("""
                **コメント：** 「義母が出産直後の私に『もう次の子作らないの？』って言ってきた」

                → **登録方法：**
                - カテゴリ：**セリフパターン**
                - カテゴリ区分：攻撃的
                - セリフ例：「もう次の子作らないの？」
                """)

            with st.expander("**例2：編集会議のアイデア**"):
                st.markdown("""
                **アイデア：** 「夫が転職を勝手に決めてた」

                → **登録方法：**
                - カテゴリ：**シチュエーション**
                - 要素名：「夫が家族に相談なく転職」
                - トリガー：「収入減、価値観の違い」
                """)

            with st.expander("**例3：ヒット記事のタイトル**"):
                st.markdown("""
                **ヒット記事：** 「【衝撃】月収20万で義母に50万要求された」

                → **登録方法：**
                - カテゴリ：**タイトル要素**
                - カテゴリ区分：数字
                - 例：「月収20万で50万要求された」
                """)

            st.success("💡 まずは「💡 クイック追加」タブで、思いついたネタを気軽に登録してみましょう！")

        with tab3:
            st.subheader("既存のネタ要素")

            # カテゴリ選択
            selected_category = st.selectbox(
                "カテゴリを選択",
                options=list(category_mapping.keys()),
                format_func=lambda x: category_mapping[x]
            )

            category_data = neta_data['categories'][selected_category]
            st.info(f"**説明:** {category_data['description']}")

            # 要素一覧を表示
            if category_data['elements']:
                st.write(f"**登録数:** {len(category_data['elements'])}件")

                for idx, element in enumerate(category_data['elements']):
                    with st.expander(f"🔹 {element.get('name', element.get('id', f'要素{idx+1}'))}"):
                        # 要素の詳細を表示
                        for key, value in element.items():
                            if key != 'id':
                                st.write(f"**{key}:** {value}")

                        # 削除ボタン
                        if st.button(f"🗑️ 削除", key=f"del_{selected_category}_{idx}"):
                            category_data['elements'].pop(idx)
                            save_neta_elements(neta_data)
                            st.success("削除しました")
                            st.rerun()
            else:
                st.warning("このカテゴリには要素が登録されていません")

        with tab4:
            st.subheader("🤖 AI自動整理 - 未整理メモをカテゴリ分類")
            st.info("**未整理のメモをAIが分析して、自動的に適切なカテゴリに振り分けます！**")

            # API key確認（Streamlit Cloud対応）
            try:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
            except (KeyError, FileNotFoundError):
                api_key = os.getenv('ANTHROPIC_API_KEY') or st.session_state.get('api_key')

            if not api_key:
                st.warning("⚠️ Anthropic API Keyが設定されていません。「⚙️ 設定」から設定してください。")
            else:
                # 未整理メモ用のJSONファイルパス
                quick_notes_path = os.path.join(os.path.dirname(__file__), 'data', 'neta_quick_notes.json')

                # 未整理メモの読み込み
                def load_quick_notes():
                    try:
                        with open(quick_notes_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except FileNotFoundError:
                        return {"version": "1.0.0", "last_updated": "2025-11-10", "notes": []}

                # 未整理メモの保存
                def save_quick_notes(data):
                    with open(quick_notes_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                quick_notes_data = load_quick_notes()
                unprocessed_notes = [note for note in quick_notes_data['notes'] if note.get('status') == 'unprocessed']

                if not unprocessed_notes:
                    st.info("未整理のメモはありません。「💡 クイック追加」タブからメモを追加してください。")
                else:
                    st.write(f"**未整理メモ: {len(unprocessed_notes)}件**")

                    # カテゴリ情報を取得
                    category_info_text = ""
                    if neta_data:
                        category_info = []
                        for cat_id, cat_data in neta_data['categories'].items():
                            category_info.append(f"- **{cat_id}** ({cat_data['name']}): {cat_data['description']}")
                        category_info_text = "\n".join(category_info)

                    # 整理するメモを選択
                    st.markdown("### 整理するメモを選択")
                    selected_notes = []

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        select_all = st.checkbox("全て選択", value=True)

                    if select_all:
                        selected_notes = unprocessed_notes
                    else:
                        for note in unprocessed_notes:
                            if st.checkbox(f"{note['content'][:80]}...", key=f"select_{note['id']}"):
                                selected_notes.append(note)

                    st.markdown("---")

                    if selected_notes:
                        st.write(f"**選択中: {len(selected_notes)}件**")

                        if st.button("🤖 AIで自動整理を実行"):
                            with st.spinner("AIが分析・整理中..."):
                                try:
                                    client = Anthropic(api_key=api_key)

                                    # 整理結果を格納
                                    organized_results = []

                                    for note in selected_notes:
                                        # AIにカテゴリ分類を依頼
                                        prompt = f"""以下のネタメモを分析して、適切なカテゴリに分類し、構造化してください。

【利用可能なカテゴリ】
{category_info_text}

【ネタメモ】
{note['content']}

【出力形式】（必ずJSON形式で返してください）
{{
  "category": "カテゴリID（上記から選択）",
  "element_name": "要素名（簡潔に）",
  "additional_fields": {{
    "description": "説明",
    "examples": ["例1", "例2"],  // dialogue_patternsの場合
    "tags": ["タグ1", "タグ2"],  // 該当する場合
    "trigger": "トリガー",  // situationsの場合
    "category": "サブカテゴリ"  // dialogue_patternsの場合
  }},
  "reasoning": "このカテゴリを選んだ理由"
}}

【重要】
- category は必ず上記のカテゴリIDから選択
- element_name は簡潔で分かりやすく
- additional_fields はカテゴリに応じて適切なフィールドを含める
- 必ずJSON形式で返答してください"""

                                        message = client.messages.create(
                                            model="claude-sonnet-4-20250514",
                                            max_tokens=1000,
                                            messages=[
                                                {"role": "user", "content": prompt}
                                            ]
                                        )

                                        # AIの応答を解析
                                        response_text = message.content[0].text

                                        # JSONを抽出（コードブロックの場合も対応）
                                        import re
                                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                                        if json_match:
                                            result = json.loads(json_match.group())
                                            result['original_note_id'] = note['id']
                                            organized_results.append(result)

                                    # 結果を表示
                                    st.success(f"✅ {len(organized_results)}件の整理が完了しました！")

                                    for result in organized_results:
                                        with st.expander(f"📝 {result['element_name']} → {result['category']}"):
                                            st.write(f"**カテゴリ:** {result['category']} ({neta_data['categories'][result['category']]['name']})")
                                            st.write(f"**要素名:** {result['element_name']}")
                                            st.write(f"**理由:** {result['reasoning']}")

                                            if result.get('additional_fields'):
                                                st.write("**追加情報:**")
                                                for key, value in result['additional_fields'].items():
                                                    st.write(f"- {key}: {value}")

                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.button("✅ 承認してマージ", key=f"approve_{result['original_note_id']}"):
                                                    # neta_elements.jsonにマージ
                                                    category_id = result['category']
                                                    existing_ids = [e.get('id', '') for e in neta_data['categories'][category_id]['elements']]
                                                    id_prefix = category_id[:2]
                                                    new_id_num = len(existing_ids) + 1
                                                    new_id = f"{id_prefix}{new_id_num:03d}"

                                                    new_element = {
                                                        'id': new_id,
                                                        'name': result['element_name'],
                                                        'weight': 1.0,
                                                        'usage_count': 0,
                                                        **result.get('additional_fields', {})
                                                    }

                                                    neta_data['categories'][category_id]['elements'].append(new_element)
                                                    save_neta_elements(neta_data)

                                                    # 未整理メモのステータスを更新
                                                    for note in quick_notes_data['notes']:
                                                        if note['id'] == result['original_note_id']:
                                                            note['status'] = 'processed'
                                                            break
                                                    save_quick_notes(quick_notes_data)

                                                    st.success("マージしました！")
                                                    st.rerun()

                                            with col2:
                                                if st.button("❌ スキップ", key=f"skip_{result['original_note_id']}"):
                                                    st.info("スキップしました")

                                except Exception as e:
                                    st.error(f"エラーが発生しました: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())

# 設定ページ
elif page == "⚙️ 設定":
    st.header("設定")

    st.subheader("API設定")

    # APIキーを取得（Streamlit Cloud対応）
    try:
        current_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        current_key = os.getenv('ANTHROPIC_API_KEY')

    if current_key:
        st.success("✅ APIキーが設定されています")
        st.write(f"APIキー: `{current_key[:8]}...{current_key[-4:]}`")

        # Streamlit Cloudの場合
        try:
            if st.secrets["ANTHROPIC_API_KEY"]:
                st.info("💡 Streamlit Cloud Secretsから読み込まれています")
        except (KeyError, FileNotFoundError):
            st.info("💡 ローカルの.envファイルから読み込まれています")

        st.markdown("---")
        st.subheader("🔌 接続テスト")

        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("🧪 API接続をテスト", use_container_width=True):
                with st.spinner("接続テスト中..."):
                    try:
                        # APIキーをトリム
                        test_key = current_key.strip()

                        # Anthropicクライアントを作成
                        client = Anthropic(api_key=test_key)

                        # テストリクエスト
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=50,
                            messages=[{"role": "user", "content": "Hello"}]
                        )

                        st.success("✅ API接続成功！正常に動作しています。")
                        st.info(f"レスポンス: {message.content[0].text[:100]}...")

                    except Exception as e:
                        st.error(f"❌ API接続失敗: {e}")
                        st.warning("APIキーが正しく設定されていない可能性があります。Streamlit Cloud Secretsを確認してください。")

        with col2:
            st.caption("所要時間: 約3秒")

        st.markdown("---")

        if st.button("APIキーを削除"):
            try:
                env_path = os.path.join(os.path.dirname(__file__), '.env')
                if os.path.exists(env_path):
                    # .envファイルを読み込み
                    with open(env_path, 'r') as f:
                        lines = f.readlines()

                    # ANTHROPIC_API_KEY以外の行を保持
                    new_lines = [line for line in lines if not line.startswith('ANTHROPIC_API_KEY=')]

                    # .envファイルを書き直し
                    with open(env_path, 'w') as f:
                        f.writelines(new_lines)

                    st.success("✅ APIキーを削除しました。ページをリロードしてください。")
                    st.info("💡 ページをリロード（F5）してください")
            except Exception as e:
                st.error(f"エラー: {e}")

    else:
        st.warning("⚠️ APIキーが設定されていません")

        # Streamlit Cloudでの設定方法を案内
        with st.expander("🌐 Streamlit Cloudをお使いの場合"):
            st.markdown("""
            **Streamlit Cloudでは、以下の手順でAPIキーを設定してください：**

            1. アプリのダッシュボードで「⚙️ Settings」をクリック
            2. 「Secrets」セクションを開く
            3. 以下の形式で入力：
               ```toml
               ANTHROPIC_API_KEY = "sk-ant-api03-..."
               ```
            4. 「Save」をクリック
            5. アプリが自動的に再起動します

            ⚠️ **注意:** Streamlit Cloudでは下記のフォームでの保存はできません。必ず上記の方法で設定してください。
            """)

        st.info("💻 **ローカル環境の場合:** 下記のフォームでAPIキーを入力して保存すると、.envファイルに保存され、次回以降も自動的に読み込まれます")

        with st.form("api_key_form"):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Claude APIを使用するためのキーを入力してください"
            )

            save_button = st.form_submit_button("保存")

            if save_button and api_key:
                try:
                    # .envファイルのパス
                    env_path = os.path.join(os.path.dirname(__file__), '.env')

                    # 既存の.envファイルを読み込み
                    existing_lines = []
                    if os.path.exists(env_path):
                        with open(env_path, 'r') as f:
                            existing_lines = f.readlines()

                    # ANTHROPIC_API_KEY以外の行を保持
                    new_lines = [line for line in existing_lines if not line.startswith('ANTHROPIC_API_KEY=')]

                    # 新しいAPIキーを追加
                    new_lines.append(f'ANTHROPIC_API_KEY={api_key}\n')

                    # .envファイルに書き込み
                    with open(env_path, 'w') as f:
                        f.writelines(new_lines)

                    st.success("✅ APIキーを保存しました！")
                    st.info("💡 ページをリロード（F5）すると設定が反映されます")

                    # セッション状態にも保存
                    st.session_state['api_key'] = api_key

                except Exception as e:
                    st.error(f"保存中にエラーが発生しました: {e}")
            elif save_button:
                st.warning("APIキーを入力してください")
