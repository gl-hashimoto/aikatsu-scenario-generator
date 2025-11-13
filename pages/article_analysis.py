"""
記事分析＆ネタ展開ページ
"""
import streamlit as st
from anthropic import Anthropic
import os
import json
import datetime
import time
from utils.prompt_library import PromptLibrary
from utils import job_manager


# 分析履歴のファイルパス
ANALYSIS_HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analysis_history.json')


def load_analysis_history():
    """分析履歴を読み込む"""
    try:
        with open(ANALYSIS_HISTORY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"version": "1.0.0", "last_updated": datetime.datetime.now().strftime("%Y-%m-%d"), "analyses": []}


def save_analysis_history(data):
    """分析履歴を保存する"""
    data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(ANALYSIS_HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_analysis(title, content, basic_analysis, deep_analysis, themes=None):
    """分析結果を保存する"""
    history = load_analysis_history()

    # 新しい分析IDを生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_id = f"ana_{timestamp}"

    # 要約を生成（記事内容の最初の100文字）
    summary = content[:100] + "..." if len(content) > 100 else content

    # 新しい分析データを作成
    new_analysis = {
        "id": analysis_id,
        "title": title or "（タイトルなし）",
        "content": content,
        "summary": summary,
        "basic_analysis": basic_analysis,
        "deep_analysis": deep_analysis,
        "themes": themes,
        "created_at": datetime.datetime.now().isoformat(),
    }

    # 履歴に追加（最新が先頭）
    history['analyses'].insert(0, new_analysis)

    # 保存
    save_analysis_history(history)

    return analysis_id


def delete_analysis(analysis_id):
    """指定されたIDの分析を削除する"""
    history = load_analysis_history()
    history['analyses'] = [a for a in history['analyses'] if a['id'] != analysis_id]
    save_analysis_history(history)


def render_article_analysis_page(api_key):
    """記事分析＆ネタ展開ページを表示"""

    st.header("🔬 記事分析＆ネタ展開")
    st.write("ヒット記事を分析して、新しいテーマのアイデアを生み出します。")

    # APIキーのトリム処理（余分な空白や改行を削除）
    if api_key:
        api_key = api_key.strip()

    # プロンプトライブラリの初期化
    prompts = PromptLibrary()

    # ========== 実行中のジョブを表示 ==========
    running_jobs = job_manager.get_running_jobs()
    running_analysis_jobs = [j for j in running_jobs if j['type'] == 'analysis']

    if running_analysis_jobs:
        st.info(f"🔄 {len(running_analysis_jobs)}件の分析が実行中です")

        with st.expander("実行中のジョブを表示", expanded=True):
            for job in running_analysis_jobs:
                col1, col2, col3 = st.columns([6, 3, 1])

                with col1:
                    st.markdown(f"**{job['title']}**")
                    st.progress(job['progress'] / 100)

                with col2:
                    status_text = {
                        'pending': '⏳ 待機中',
                        'running': '🔄 実行中',
                    }.get(job['status'], job['status'])
                    st.caption(f"{status_text} ({job['progress']}%)")

                with col3:
                    if st.button("🗑️", key=f"cancel_{job['id']}", help="キャンセル"):
                        job_manager.delete_job(job['id'])
                        st.rerun()

                st.markdown("---")

            # 自動更新（5秒ごと）
            if st.button("🔄 状態を更新"):
                st.rerun()

            st.caption("💡 ページを離れても処理は継続されます。完了すると自動的に「完了したジョブ」に表示されます。")

    # 完了したジョブを表示
    completed_jobs = job_manager.get_completed_jobs()
    completed_analysis_jobs = [j for j in completed_jobs if j['type'] == 'analysis']

    if completed_analysis_jobs:
        with st.expander(f"✅ 完了したジョブ ({len(completed_analysis_jobs)}件)", expanded=False):
            for job in completed_analysis_jobs:
                col1, col2, col3 = st.columns([6, 3, 1])

                with col1:
                    st.markdown(f"**{job['title']}**")
                    st.caption(f"完了: {datetime.datetime.fromisoformat(job['completed_at']).strftime('%Y/%m/%d %H:%M')}")

                with col2:
                    if st.button("📥 履歴に保存", key=f"save_{job['id']}"):
                        # 結果を履歴に保存
                        result = job['result']
                        save_analysis(
                            title=result['article_title'],
                            content=result['article_content'],
                            basic_analysis=result['basic_analysis'],
                            deep_analysis=result['deep_analysis'],
                            themes=result.get('themes')
                        )
                        # ジョブを削除
                        job_manager.delete_job(job['id'])
                        st.success("✅ 履歴に保存しました")
                        st.rerun()

                with col3:
                    if st.button("🗑️", key=f"delete_completed_{job['id']}", help="削除"):
                        job_manager.delete_job(job['id'])
                        st.rerun()

                st.markdown("---")

    st.markdown("---")

    # タブで「新規分析」と「分析履歴」を切り替え
    tab1, tab2 = st.tabs(["📝 新規分析", "📚 分析履歴"])

    # ========== タブ1: 新規分析 ==========
    with tab1:
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
                try:
                    # ジョブを作成
                    job_title = article_title or f"記事分析 {datetime.datetime.now().strftime('%m/%d %H:%M')}"
                    job_id = job_manager.create_job(
                        job_type="analysis",
                        title=job_title,
                        params={
                            "article_title": article_title,
                            "article_content": article_content
                        }
                    )

                    # バックグラウンドで分析を開始
                    job_manager.start_article_analysis_job(
                        job_id=job_id,
                        api_key=api_key,
                        article_title=article_title,
                        article_content=article_content,
                        prompts=prompts
                    )

                    st.success(f"✅ 分析をバックグラウンドで開始しました！（ジョブID: {job_id}）")
                    st.info("💡 ページを離れても処理は継続されます。上部の「実行中のジョブ」で進捗を確認できます。")

                    # ページをリロードして状態を更新
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"ジョブの作成中にエラーが発生しました: {e}")

        # 分析結果の表示
        if 'basic_analysis' in st.session_state and 'deep_analysis' in st.session_state:
            st.markdown("---")
            st.subheader("ステップ2️⃣ 分析結果")

            # タブで表示
            analysis_tab1, analysis_tab2 = st.tabs(["📊 基本分析", "🔬 深堀り分析"])

            with analysis_tab1:
                st.markdown(st.session_state.basic_analysis)

            with analysis_tab2:
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

                        # API呼び出し（テーマ数に応じてmax_tokensを調整）
                        # 1テーマあたり約600トークン必要と想定
                        estimated_tokens = min(num_themes * 600 + 1000, 8000)

                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=estimated_tokens,
                            messages=[{"role": "user", "content": prompt}]
                        )

                        themes = message.content[0].text

                        # セッション状態に保存
                        st.session_state.generated_themes = themes

                        # トークン上限に達したかチェック
                        if message.stop_reason == "max_tokens":
                            st.warning(f"⚠️ 生成が途中で終了しました。テーマ数を減らすか、複数回に分けて生成することをお勧めします。")

                        st.success(f"✅ {num_themes}個のテーマを生成しました！")

                    except Exception as e:
                        st.error(f"テーマ生成でエラーが発生しました: {e}")

            # 生成されたテーマを表示
            if 'generated_themes' in st.session_state:
                st.markdown("---")
                st.subheader("💡 生成されたテーマ")
                st.markdown(st.session_state.generated_themes)

                # ダウンロードボタンと保存ボタン
                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        label="📥 テーマをダウンロード",
                        data=st.session_state.generated_themes,
                        file_name=f"new_themes_{num_themes}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

                with col2:
                    if st.button("💾 分析結果を保存", use_container_width=True, type="secondary"):
                        try:
                            analysis_id = save_analysis(
                                title=st.session_state.get('article_title', ''),
                                content=st.session_state.get('article_content', ''),
                                basic_analysis=st.session_state.get('basic_analysis', ''),
                                deep_analysis=st.session_state.get('deep_analysis', ''),
                                themes=st.session_state.get('generated_themes')
                            )
                            st.success(f"✅ 分析結果を保存しました！（ID: {analysis_id}）")
                            st.info("💡 「📚 分析履歴」タブで確認できます")
                        except Exception as e:
                            st.error(f"保存中にエラーが発生しました: {e}")

    # ========== タブ2: 分析履歴 ==========
    with tab2:
        st.markdown("---")
        st.subheader("📚 保存済みの分析")

        # 履歴を読み込み
        history = load_analysis_history()
        analyses = history.get('analyses', [])

        if not analyses:
            st.info("保存された分析はまだありません。「📝 新規分析」タブで分析を実行して保存してください。")
        else:
            st.write(f"**保存数: {len(analyses)}件**")

            # セッション状態で選択中の分析を管理
            if 'selected_analysis_id' not in st.session_state:
                st.session_state.selected_analysis_id = None

            # 一覧表示
            st.markdown("### 📋 分析一覧")

            for analysis in analyses:
                # カード風の表示
                with st.container():
                    col1, col2, col3 = st.columns([6, 2, 1])

                    with col1:
                        # タイトルをボタンとして表示（クリックで詳細表示）
                        if st.button(
                            f"📄 {analysis['title']}",
                            key=f"select_{analysis['id']}",
                            use_container_width=True
                        ):
                            st.session_state.selected_analysis_id = analysis['id']
                            st.rerun()

                        # 要約を表示
                        st.caption(f"💬 {analysis['summary']}")

                    with col2:
                        # 作成日時を表示
                        created_at = datetime.datetime.fromisoformat(analysis['created_at'])
                        st.caption(f"📅 {created_at.strftime('%Y/%m/%d %H:%M')}")

                    with col3:
                        # 削除ボタン
                        if st.button("🗑️", key=f"delete_{analysis['id']}", help="削除"):
                            try:
                                delete_analysis(analysis['id'])
                                st.success("削除しました")
                                if st.session_state.selected_analysis_id == analysis['id']:
                                    st.session_state.selected_analysis_id = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"削除中にエラーが発生しました: {e}")

                    st.markdown("---")

            # 選択された分析の詳細表示
            if st.session_state.selected_analysis_id:
                selected_analysis = next(
                    (a for a in analyses if a['id'] == st.session_state.selected_analysis_id),
                    None
                )

                if selected_analysis:
                    st.markdown("---")
                    st.markdown(f"## 📖 詳細: {selected_analysis['title']}")

                    # 閉じるボタン
                    if st.button("✖️ 閉じる"):
                        st.session_state.selected_analysis_id = None
                        st.rerun()

                    st.markdown(f"**作成日時:** {datetime.datetime.fromisoformat(selected_analysis['created_at']).strftime('%Y年%m月%d日 %H:%M')}")

                    # 記事内容
                    with st.expander("📝 記事内容", expanded=True):
                        st.markdown(selected_analysis['content'])

                    # 分析結果をタブで表示
                    detail_tab1, detail_tab2, detail_tab3 = st.tabs(["📊 基本分析", "🔬 深堀り分析", "💡 生成テーマ"])

                    with detail_tab1:
                        st.markdown(selected_analysis['basic_analysis'])

                    with detail_tab2:
                        st.markdown(selected_analysis['deep_analysis'])

                    with detail_tab3:
                        if selected_analysis.get('themes'):
                            st.markdown(selected_analysis['themes'])
                        else:
                            st.info("テーマは生成されていません")

                    # ダウンロードボタン
                    st.markdown("---")
                    download_content = f"""# {selected_analysis['title']}

作成日時: {datetime.datetime.fromisoformat(selected_analysis['created_at']).strftime('%Y年%m月%d日 %H:%M')}

## 記事内容

{selected_analysis['content']}

---

## 基本分析

{selected_analysis['basic_analysis']}

---

## 深堀り分析

{selected_analysis['deep_analysis']}

---

## 生成されたテーマ

{selected_analysis.get('themes', 'テーマは生成されていません')}
"""

                    st.download_button(
                        label="📥 この分析をダウンロード",
                        data=download_content,
                        file_name=f"analysis_{selected_analysis['id']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
