from llm.client import chat

SYSTEM_PROMPT = """你是一位量化足球结果解读专家。根据模拟数据和策略建议，输出一段自然语言总结。
用中文，2-4句，简洁有力。提到：胜率、关键因子、风险提示。"""

def interpret_results(sim_result: dict, advice: dict, match_info: dict) -> str:
    user_msg = f"""{sim_result.get('home_win_pct', '?')}% | 平 {sim_result.get('draw_pct', '?')}% | 客胜 {sim_result.get('away_win_pct', '?')}%
期望值: {advice.get('expected_value', '?')}
建议: {advice.get('suggestion', '?')}
波动系数: {sim_result.get('variance', '?')}
"""
    return chat(SYSTEM_PROMPT, user_msg)
