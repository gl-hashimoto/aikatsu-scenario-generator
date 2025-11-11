"""
記事分析＆ネタ展開ページ
"""
import streamlit as st
from anthropic import Anthropic
import os
from utils.prompt_library import PromptLibrary


def render_article_analysis_page(api_key):
    """記事分析＆ネタ展開ページを表示"""

    st.header("🔬 記事分析＆ネタ展開")
    st.write("ヒット記事を分析して、新しいテーマのアイデアを生み出します。")

    # プロンプトライブラリの初期化
    prompts = PromptLibrary()

    st.markdown("---")
    st.subheader("ステップ1️⃣ ヒット記事を入力")

    # 記事入力フォーム
    article_title = st.text_input(
        "記事タイトル（任意）",
        placeholder="例: 【衝撃】月収20万で義母に50万要求された",
        help="タイトルがあれば入力してください"
    )

    article_content = st.text_area(
        "記事の内容・あらすじ ✳︎",
        placeholder="""例:
主人公は30代主婦。夫の月収は20万円。
ある日、義母が突然訪問してきて「新築祝いに50万円ちょうだい」と言ってきた。
主人公が「そんな余裕はありません」と断ると、義母は「息子夫婦なのに冷たい」と激怒。
主人公は義母の非常識さに我慢の限界を迎え...

（5-10行程度でOK）""",
        height=200,
        help="記事の要約やあらすじを入力してください。詳細でなくても大丈夫です。"
    )

    st.markdown("---")

    # 分析実行
    col1, col2 = st.columns([3, 1])

    with col1:
        analyze_button = st.button("🔍 この記事を分析", use_container_width=True, type="primary")

    with col2:
        st.caption("所要時間: 約30秒")

    # 分析実行
    if analyze_button:
        if not article_content.strip():
            st.error("記事の内容を入力してください")
        elif not api_key:
            st.error("⚠️ API Keyが設定されていません。「⚙️ 設定」から設定してください。")
        else:
            # 基本分析
            with st.spinner("📊 基本分析中..."):
                try:
                    client = Anthropic(api_key=api_key)

                    # プロンプト作成
                    prompt = prompts.format(
                        "analysis",
                        "basic_analysis",
                        article_title=article_title or "（タイトルなし）",
                        article_content=article_content
                    )

                    # API呼び出し
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    basic_analysis = message.content[0].text

                    # セッション状態に保存
                    st.session_state.basic_analysis = basic_analysis
                    st.session_state.article_content = article_content
                    st.session_state.article_title = article_title

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    return

            # 深堀り分析
            with st.spinner("🔬 深堀り分析中（3段階）..."):
                try:
                    # プロンプト作成
                    prompt = prompts.format(
                        "analysis",
                        "deep_analysis",
                        article_content=article_content,
                        basic_analysis=basic_analysis
                    )

                    # API呼び出し
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=3000,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    deep_analysis = message.content[0].text

                    # セッション状態に保存
                    st.session_state.deep_analysis = deep_analysis

                    st.success("✅ 分析が完了しました！")

                except Exception as e:
                    st.error(f"深堀り分析でエラーが発生しました: {e}")
                    return

    # 分析結果の表示
    if 'basic_analysis' in st.session_state and 'deep_analysis' in st.session_state:
        st.markdown("---")
        st.subheader("ステップ2️⃣ 分析結果")

        # タブで表示
        tab1, tab2 = st.tabs(["📊 基本分析", "🔬 深堀り分析"])

        with tab1:
            st.markdown(st.session_state.basic_analysis)

        with tab2:
            st.markdown(st.session_state.deep_analysis)

        st.markdown("---")
        st.subheader("ステップ3️⃣ 新テーマ提案")

        col1, col2 = st.columns([2, 1])

        with col1:
            num_themes = st.slider("提案数", min_value=5, max_value=20, value=10, step=1)

        with col2:
            generate_button = st.button("🚀 新テーマを生成", use_container_width=True, type="primary")

        if generate_button:
            with st.spinner(f"💡 {num_themes}個のテーマを生成中..."):
                try:
                    client = Anthropic(api_key=api_key)

                    # 分析結果を統合
                    analysis_result = f"""
【基本分析】
{st.session_state.basic_analysis}

【深堀り分析】
{st.session_state.deep_analysis}
"""

                    # プロンプト作成
                    prompt = prompts.format(
                        "theme_generation",
                        "generate_themes",
                        analysis_result=analysis_result,
                        num_themes=num_themes
                    )

                    # API呼び出し
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=4000,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    themes = message.content[0].text

                    # セッション状態に保存
                    st.session_state.generated_themes = themes

                    st.success(f"✅ {num_themes}個のテーマを生成しました！")

                except Exception as e:
                    st.error(f"テーマ生成でエラーが発生しました: {e}")

        # 生成されたテーマを表示
        if 'generated_themes' in st.session_state:
            st.markdown("---")
            st.subheader("💡 生成されたテーマ")
            st.markdown(st.session_state.generated_themes)

            # ダウンロードボタン
            st.download_button(
                label="📥 テーマをダウンロード",
                data=st.session_state.generated_themes,
                file_name=f"new_themes_{num_themes}.md",
                mime="text/markdown"
            )
