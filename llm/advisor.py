import json
from llm.client import chat

SYSTEM_PROMPT = """你是一位量化足球因子专家。根据比赛上下文，建议哪些因子应该调高权重。
返回 JSON 格式: {"suggestions": [{"factor": "因子名", "current_weight": 5, "suggested_weight": 10, "reason": "原因"}]}
只能建议 0-3 个因子调整，没有好的建议就返回空数组。"""

def get_factor_advice(match_info: dict, current_weights: dict) -> list:
    user_msg = f"""比赛: {match_info.get('home_team', '')} vs {match_info.get('away_team', '')}
赛事: {match_info.get('league', '')} · 阶段: {match_info.get('stage', '')}
当前权重: {json.dumps(current_weights, ensure_ascii=False)}
"""
    resp = chat(SYSTEM_PROMPT, user_msg, temperature=0.2)
    try:
        return json.loads(resp).get("suggestions", [])
    except json.JSONDecodeError:
        return []
