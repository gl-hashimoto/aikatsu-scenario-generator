"""
バックグラウンドジョブ管理システム
"""
import json
import os
import datetime
import threading
from typing import Optional, Dict, Any, Callable
from anthropic import Anthropic


# ジョブ状態ファイルのパス
JOBS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'jobs.json')
ANALYSIS_HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analysis_history.json')

# ロック（スレッドセーフな操作のため）
_jobs_lock = threading.Lock()
_history_lock = threading.Lock()


def load_jobs():
    """ジョブ一覧を読み込む"""
    try:
        with _jobs_lock:
            with open(JOBS_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except FileNotFoundError:
        return {"version": "1.0.0", "jobs": []}


def save_jobs(data):
    """ジョブ一覧を保存する"""
    with _jobs_lock:
        os.makedirs(os.path.dirname(JOBS_FILE_PATH), exist_ok=True)
        with open(JOBS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def create_job(job_type: str, title: str, params: Dict[str, Any]) -> str:
    """新しいジョブを作成"""
    jobs_data = load_jobs()

    # ジョブIDを生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"job_{timestamp}"

    # 新しいジョブを作成
    new_job = {
        "id": job_id,
        "type": job_type,
        "status": "pending",
        "title": title,
        "params": params,
        "result": None,
        "error": None,
        "created_at": datetime.datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0
    }

    # ジョブリストに追加
    jobs_data['jobs'].insert(0, new_job)

    # 保存
    save_jobs(jobs_data)

    return job_id


def update_job_status(job_id: str, status: str, progress: int = None, result: Any = None, error: str = None):
    """ジョブの状態を更新"""
    jobs_data = load_jobs()

    for job in jobs_data['jobs']:
        if job['id'] == job_id:
            job['status'] = status

            if progress is not None:
                job['progress'] = progress

            if status == "running" and job['started_at'] is None:
                job['started_at'] = datetime.datetime.now().isoformat()

            if status in ["completed", "failed"]:
                job['completed_at'] = datetime.datetime.now().isoformat()

            if result is not None:
                job['result'] = result

            if error is not None:
                job['error'] = error

            break

    save_jobs(jobs_data)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """ジョブ情報を取得"""
    jobs_data = load_jobs()

    for job in jobs_data['jobs']:
        if job['id'] == job_id:
            return job

    return None


def delete_job(job_id: str):
    """ジョブを削除"""
    jobs_data = load_jobs()
    jobs_data['jobs'] = [job for job in jobs_data['jobs'] if job['id'] != job_id]
    save_jobs(jobs_data)


def get_running_jobs():
    """実行中のジョブを取得"""
    jobs_data = load_jobs()
    return [job for job in jobs_data['jobs'] if job['status'] in ['pending', 'running']]


def get_completed_jobs():
    """完了したジョブを取得"""
    jobs_data = load_jobs()
    return [job for job in jobs_data['jobs'] if job['status'] == 'completed']


def cleanup_old_jobs(days: int = 7):
    """古い完了済みジョブを削除"""
    jobs_data = load_jobs()
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

    jobs_data['jobs'] = [
        job for job in jobs_data['jobs']
        if job['status'] not in ['completed', 'failed'] or
        datetime.datetime.fromisoformat(job['created_at']) > cutoff_date
    ]

    save_jobs(jobs_data)


# =====================================================
# 分析履歴への自動保存
# =====================================================

def save_analysis_to_history(title: str, content: str, basic_analysis: str, deep_analysis: str, themes: str = None):
    """分析結果を履歴に保存する"""
    try:
        with _history_lock:
            # 履歴を読み込み
            try:
                with open(ANALYSIS_HISTORY_PATH, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = {"version": "1.0.0", "last_updated": datetime.datetime.now().strftime("%Y-%m-%d"), "analyses": []}

            # 新しい分析IDを生成
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_id = f"ana_{timestamp}"

            # タイトルが空の場合、記事内容の最初の50文字を使用
            if not title or title.strip() == "":
                # 改行やタブを除去して最初の50文字を取得
                clean_content = content.replace('\n', ' ').replace('\t', ' ').strip()
                title = clean_content[:50] + "..." if len(clean_content) > 50 else clean_content

            # 要約を生成（記事内容の最初の100文字）
            summary = content[:100] + "..." if len(content) > 100 else content

            # 新しい分析データを作成
            new_analysis = {
                "id": analysis_id,
                "title": title,
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
            history['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")
            os.makedirs(os.path.dirname(ANALYSIS_HISTORY_PATH), exist_ok=True)
            with open(ANALYSIS_HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            return analysis_id
    except Exception as e:
        print(f"履歴保存エラー: {e}")
        return None


# =====================================================
# 記事分析用のバックグラウンドタスク
# =====================================================

def run_article_analysis_job(job_id: str, api_key: str, article_title: str, article_content: str, prompts, auto_generate_themes: bool = True, num_themes: int = 6):
    """記事分析をバックグラウンドで実行し、自動的にテーマ生成も行う"""
    try:
        update_job_status(job_id, "running", progress=10)

        client = Anthropic(api_key=api_key)

        # 基本分析
        update_job_status(job_id, "running", progress=20)
        prompt = prompts.format(
            "analysis",
            "basic_analysis",
            article_title=article_title or "（タイトルなし）",
            article_content=article_content
        )

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        basic_analysis = message.content[0].text
        update_job_status(job_id, "running", progress=40)

        # 深堀り分析
        prompt = prompts.format(
            "analysis",
            "deep_analysis",
            article_content=article_content,
            basic_analysis=basic_analysis
        )

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        deep_analysis = message.content[0].text
        update_job_status(job_id, "running", progress=60)

        # 自動的にテーマ生成を実行
        themes = None
        if auto_generate_themes:
            # 分析結果を統合
            analysis_result = f"""
【基本分析】
{basic_analysis}

【深堀り分析】
{deep_analysis}
"""

            update_job_status(job_id, "running", progress=70)

            # story_tips を読み込み（キャッシュを使わない）
            story_tips = prompts.load("theme_generation", "story_tips", use_cache=False)

            # テーマ生成プロンプト作成
            prompt = prompts.format(
                "theme_generation",
                "generate_themes",
                analysis_result=analysis_result,
                num_themes=num_themes,
                story_tips=story_tips
            )

            # テーマ生成API呼び出し
            estimated_tokens = min(num_themes * 600 + 1000, 8000)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=estimated_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            themes = message.content[0].text
            update_job_status(job_id, "running", progress=90)

        # 結果を保存
        result = {
            "article_title": article_title,
            "article_content": article_content,
            "basic_analysis": basic_analysis,
            "deep_analysis": deep_analysis,
            "themes": themes,
            "num_themes": num_themes
        }

        update_job_status(job_id, "completed", progress=100, result=result)

        # 自動的に履歴に保存
        save_analysis_to_history(
            title=article_title,
            content=article_content,
            basic_analysis=basic_analysis,
            deep_analysis=deep_analysis,
            themes=themes
        )

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))


def start_article_analysis_job(job_id: str, api_key: str, article_title: str, article_content: str, prompts, auto_generate_themes: bool = True, num_themes: int = 6):
    """記事分析ジョブをバックグラウンドで開始"""
    thread = threading.Thread(
        target=run_article_analysis_job,
        args=(job_id, api_key, article_title, article_content, prompts, auto_generate_themes, num_themes),
        daemon=True
    )
    thread.start()


# =====================================================
# テーマ生成用のバックグラウンドタスク
# =====================================================

def run_theme_generation_job(job_id: str, api_key: str, analysis_result: str, num_themes: int, prompts):
    """テーマ生成をバックグラウンドで実行"""
    try:
        update_job_status(job_id, "running", progress=20)

        client = Anthropic(api_key=api_key)

        # story_tips を読み込み（キャッシュを使わない）
        story_tips = prompts.load("theme_generation", "story_tips", use_cache=False)

        # プロンプト作成
        prompt = prompts.format(
            "theme_generation",
            "generate_themes",
            analysis_result=analysis_result,
            num_themes=num_themes,
            story_tips=story_tips
        )

        update_job_status(job_id, "running", progress=40)

        # API呼び出し
        estimated_tokens = min(num_themes * 600 + 1000, 8000)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=estimated_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        themes = message.content[0].text

        update_job_status(job_id, "running", progress=80)

        # 結果を保存
        result = {
            "themes": themes,
            "num_themes": num_themes
        }

        update_job_status(job_id, "completed", progress=100, result=result)

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))


def start_theme_generation_job(job_id: str, api_key: str, analysis_result: str, num_themes: int, prompts):
    """テーマ生成ジョブをバックグラウンドで開始"""
    thread = threading.Thread(
        target=run_theme_generation_job,
        args=(job_id, api_key, analysis_result, num_themes, prompts),
        daemon=True
    )
    thread.start()
