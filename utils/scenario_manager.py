"""
シナリオ管理ユーティリティ
"""
import json
import os
import datetime


# シナリオ履歴のファイルパス
SCENARIO_HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'scenario_history.json')


def load_scenario_history():
    """シナリオ履歴を読み込む"""
    try:
        with open(SCENARIO_HISTORY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"version": "1.0.0", "last_updated": datetime.datetime.now().strftime("%Y-%m-%d"), "scenarios": []}


def save_scenario_history(data):
    """シナリオ履歴を保存する"""
    data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(SCENARIO_HISTORY_PATH), exist_ok=True)
    with open(SCENARIO_HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_scenario(scenario_params, scenario_content):
    """シナリオを保存する"""
    history = load_scenario_history()

    # 新しいシナリオIDを生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario_id = f"scn_{timestamp}"

    # タイトルを抽出（シナリオ本文の最初の行または最初の100文字）
    lines = scenario_content.split('\n')
    title = "無題のシナリオ"
    for line in lines:
        if line.strip() and not line.startswith('#'):
            title = line.strip()[:100]
            break
        elif line.startswith('# '):
            title = line.replace('# ', '').strip()[:100]
            break

    # 要約を生成（シナリオ内容の最初の150文字）
    summary = scenario_content[:150] + "..." if len(scenario_content) > 150 else scenario_content

    # 新しいシナリオデータを作成
    new_scenario = {
        "id": scenario_id,
        "title": title,
        "summary": summary,
        "content": scenario_content,
        "parameters": scenario_params,
        "created_at": datetime.datetime.now().isoformat(),
    }

    # 履歴に追加（最新が先頭）
    history['scenarios'].insert(0, new_scenario)

    # 保存
    save_scenario_history(history)

    return scenario_id


def delete_scenario(scenario_id):
    """指定されたIDのシナリオを削除する"""
    history = load_scenario_history()
    history['scenarios'] = [s for s in history['scenarios'] if s['id'] != scenario_id]
    save_scenario_history(history)
