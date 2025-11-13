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

# ロック（スレッドセーフな操作のため）
_jobs_lock = threading.Lock()


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
# 記事分析用のバックグラウンドタスク
# =====================================================

def run_article_analysis_job(job_id: str, api_key: str, article_title: str, article_content: str, prompts):
    """記事分析をバックグラウンドで実行"""
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
        update_job_status(job_id, "running", progress=50)

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
        update_job_status(job_id, "running", progress=80)

        # 結果を保存
        result = {
            "article_title": article_title,
            "article_content": article_content,
            "basic_analysis": basic_analysis,
            "deep_analysis": deep_analysis
        }

        update_job_status(job_id, "completed", progress=100, result=result)

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))


def start_article_analysis_job(job_id: str, api_key: str, article_title: str, article_content: str, prompts):
    """記事分析ジョブをバックグラウンドで開始"""
    thread = threading.Thread(
        target=run_article_analysis_job,
        args=(job_id, api_key, article_title, article_content, prompts),
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

        # プロンプト作成
        prompt = prompts.format(
            "theme_generation",
            "generate_themes",
            analysis_result=analysis_result,
            num_themes=num_themes
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
