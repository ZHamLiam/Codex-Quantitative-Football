from llm.client import chat

SYSTEM_PROMPT = """你是一位资深足球分析师。根据提供的数据，输出一份结构化的赛前分析报告。
格式要求：
1. 球队状态对比（2-3句）
2. 关键对位分析（2个关键对位）
3. 潜在风险点（1-2个）
4. 综合预判（1句）
使用中文，简洁专业，不超过300字。"""

def generate_scout_report(match_info: dict, factor_scores: dict) -> str:
    lines = []
    for k, v in factor_scores.items():
        lines.append(f"- {k}: {v}")
    user_msg = f"""比赛: {match_info.get('home_team', '主队')} vs {match_info.get('away_team', '客队')}
赛事: {match_info.get('league', '')} · {match_info.get('stage', '联赛')}

因子评分:
{chr(10).join(lines)}
"""
    return chat(SYSTEM_PROMPT, user_msg)
