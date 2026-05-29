# ⚽ 量化足球分析系统

基于蒙特卡洛模拟 + 大模型（LLM）+ 多因子模型的足球比赛量化分析系统。

## 功能概述

- **真实数据获取**：接入 football-data.org、ClubElo、The Odds API 等免费/低成本数据源
- **多因子分析**：涵盖基本面、战术风格、环境因素、心理/战意、市场信号五大类因子，支持权重配置
- **蒙特卡洛模拟**：10000 次随机模拟，输出胜平负概率、比分分布、期望进球
- **LLM 智能分析**：接入 DeepSeek / OpenAI，自动分析爆冷风险、大比分可能性、买入建议
- **可视化面板**：单页 Web 界面，比赛索引、搜索、因子调整、分析结果展示

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 / FastAPI / SQLAlchemy / SQLite |
| 前端 | 原生 HTML/CSS/JS（单页应用） |
| 数据分析 | NumPy / SciPy（蒙特卡洛、泊松分布） |
| AI | OpenAI SDK（兼容 DeepSeek / GPT） |
| 数据源 | football-data.org、ClubElo、The Odds API、RSS 新闻 |

## 项目结构

```
├── main.py                  # FastAPI 入口
├── config.py                # 环境变量配置
├── api/                     # API 路由（matches, analysis, profiles, llm）
├── db/                      # 数据库模型 & 种子数据
├── engines/
│   ├── simulation/          # 蒙特卡洛模拟引擎
│   ├── analysis/            # 多因子分析引擎
│   ├── strategy/            # 买入策略 & 风险评估
│   └── data/                # 数据获取 & 同步
│       ├── sources/         # football-data, ClubElo, Odds API
│       ├── news/            # RSS 新闻聚合 & 验证
│       └── squad/           # 首发预测
├── llm/                     # LLM 客户端 & 解释器
├── web/                     # 前端页面 (index.html + CSS + JS)
└── docs/                    # 设计文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 API Key
```

| 变量 | 说明 | 获取地址 |
|---|---|---|
| `OPENAI_API_KEY` | LLM API Key | [DeepSeek](https://platform.deepseek.com/) 或 [OpenAI](https://platform.openai.com/) |
| `OPENAI_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` 或 `gpt-4o-mini` |
| `FOOTBALL_DATA_API_KEY` | 比赛数据 | [football-data.org](https://www.football-data.org/) |
| `ODDS_API_KEY` | 赔率数据 | [the-odds-api.com](https://the-odds-api.com/) |

### 3. 初始化数据

```bash
$env:PYTHONPATH = "."
python db/seed.py
```

### 4. 启动服务

```bash
$env:PYTHONPATH = "."
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:8000/`

## 因子体系

系统内置 19 个分析因子，分为五大类：

| 类别 | 因子 | 数据来源 |
|---|---|---|
| 基本面 | 近期战绩、主客场分离、阵容完整度、射手状态 | ClubElo、football-data |
| 战术风格 | 配合默契度、教练稳定性、控球率倾向、进攻方式、防守风格、风格克制 | ClubElo、LLM 分析 |
| 环境因素 | 天气、裁判风格、旅途疲劳、赛程密度 | RSS 新闻 + LLM |
| 心理/战意 | 战意、近期士气、大赛经验 | 联赛/杯赛阶段推断 |
| 市场信号 | 赔率变化 | The Odds API |

因子权重可通过前端面板实时调整并持久化保存。

## 分析流程

```
选择比赛 → 数据获取 → 多因子计算 → 蒙特卡洛模拟(10000次) → LLM 总结 → 结果展示
```

1. **数据获取**：比赛信息、ELO 评分、赔率数据、相关新闻
2. **因子计算**：根据因子权重和实际数据计算 λ（进球期望值）
3. **蒙特卡洛模拟**：基于泊松分布模拟 10000 场比赛
4. **LLM 分析**：将模拟结果交给大模型进行爆冷/大比分/策略分析
5. **结果展示**：胜平负概率、比分分布、买入建议、风险提示

## 联赛覆盖

- 英超 / 西甲 / 德甲 / 意甲 / 法甲
- 欧冠
- 世界杯

## License

MIT
