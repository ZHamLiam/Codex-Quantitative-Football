
# 量化足球系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建数据驱动的足球分析与投注决策辅助系统，覆盖世界杯+五大联赛+欧冠。

**Architecture:** FastAPI 后端 + SQLite 数据库 + 单页 HTML/JS 前端。Engine 层六步管线（数据→分析→模拟→总结→风险→策略），LLM 做定性辅助，因子配置可前端编辑持久化。

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite / NumPy / SciPy / OpenAI SDK / Vanilla HTML+JS 前端

---

## Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config.py`
- Create: `main.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.25
httpx>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
numpy>=1.26.0
scipy>=1.12.0
matplotlib>=3.8.0
openai>=1.30.0
feedparser>=6.0.0
```

- [ ] **Step 2: 创建 .env.example**

```
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
FOOTBALL_DATA_API_KEY=xxx
APP_HOST=127.0.0.1
APP_PORT=8000
```

- [ ] **Step 3: 创建 .gitignore**

```
.env
__pycache__/
*.pyc
db/sqlite.db
.superpowers/
*.egg-info/
dist/
```

- [ ] **Step 4: 创建 config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    football_data_api_key: str = ""
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///db/sqlite.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

- [ ] **Step 5: 创建 main.py（最小入口）**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings

app = FastAPI(title="量化足球系统")

@app.get("/api/health")
def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="web", html=True), name="web")
```

- [ ] **Step 6: 验证启动**

Run: `uvicorn main:app --host 127.0.0.1 --port 8000`
Expected: "Uvicorn running on http://127.0.0.1:8000"
Then: `curl http://127.0.0.1:8000/api/health` → `{"status":"ok"}`

- [ ] **Step 7: 安装创建各目录结构**

Run:
```
mkdir engines\data\sources
mkdir engines\data\squad
mkdir engines\data\news
mkdir engines\analysis
mkdir engines\simulation
mkdir engines\strategy
mkdir llm
mkdir db
mkdir api
mkdir web\css
mkdir web\js
mkdir tests
```

每个目录下创建空 `__init__.py`。

- [ ] **Step 8: Commit**

```
git add -A
git commit -m "chore: project scaffold with FastAPI entry point and config"
```

---

## Task 2: 数据库层

**Files:**
- Create: `db/database.py`
- Create: `db/models.py`

- [ ] **Step 1: 创建 db/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: 创建 db/models.py（完整模型）**

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(10))
    country = Column(String(50))
    league = Column(String(50))
    elo_rating = Column(Float, default=1500)
    external_id = Column(Integer, unique=True)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    match_date = Column(DateTime, nullable=False)
    league = Column(String(50))
    stage = Column(String(30), default="league")  # league / group_md1 / r16 / qf / sf / final
    status = Column(String(20), default="scheduled")  # scheduled / completed
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    external_id = Column(Integer, unique=True)
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

class FactorConfig(Base):
    __tablename__ = "factor_configs"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(10), nullable=False)  # L1-L5
    description = Column(String(500))
    is_custom = Column(Boolean, default=False)
    default_weight = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

class FactorProfile(Base):
    __tablename__ = "factor_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("FactorProfileItem", back_populates="profile", cascade="all, delete-orphan")

class FactorProfileItem(Base):
    __tablename__ = "factor_profile_items"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("factor_profiles.id"), nullable=False)
    factor_config_id = Column(Integer, ForeignKey("factor_configs.id"), nullable=False)
    weight = Column(Integer, default=5)  # 0-100
    enabled = Column(Boolean, default=True)
    profile = relationship("FactorProfile", back_populates="items")
    factor = relationship("FactorConfig")

class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("factor_profiles.id"), nullable=False)
    home_win_pct = Column(Float)
    draw_pct = Column(Float)
    away_win_pct = Column(Float)
    expected_goals = Column(Float)
    score_distribution = Column(JSON)  # {"2-1": 0.15, "1-1": 0.12, ...}
    lambda_home = Column(Float)
    lambda_away = Column(Float)
    variance = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class StartingXI(Base):
    __tablename__ = "starting_xi"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_name = Column(String(100), nullable=False)
    position = Column(String(10))  # GK/DEF/MID/FWD
    predicted_role = Column(String(10), default="bench")  # starter/bench/out
    confidence = Column(Integer, default=50)
    formation = Column(String(10))
    reasoning = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class NewsItem(Base):
    __tablename__ = "news_items"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    source = Column(String(200))
    source_tier = Column(Integer, default=3)  # 1-5
    player_mentioned = Column(String(100))
    topic = Column(String(30))  # injury/lineup/tactics/morale/other
    claim = Column(Text)
    sentiment = Column(String(10))  # positive/negative/neutral
    consensus_score = Column(Integer)  # 0-100
    verdict = Column(String(20))  # confirmed/disputed/unconfirmed/smoke
    url = Column(String(500))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: 验证数据库创建**

Run: `python -c "from db.database import init_db; init_db(); print('DB created')"`
Expected: `DB created`，`db/sqlite.db` 文件生成

- [ ] **Step 4: Commit**

```
git add db/ -A
git commit -m "feat: database models for teams, matches, factors, simulation"
```

---

## Task 3: 种子数据（默认因子 & 方案）

**Files:**
- Create: `db/seed.py`

- [ ] **Step 1: 创建 db/seed.py**

```python
from db.database import SessionLocal, init_db
from db.models import FactorConfig, FactorProfile, FactorProfileItem

DEFAULT_FACTORS = [
    # L1 基本面
    ("近期战绩", "L1", "近5/10场胜率、进球、失球", 20),
    ("主客场分离", "L1", "主场vs客场表现差异", 10),
    ("阵容完整度", "L1", "伤病/停赛对比理论最强11人", 12),
    ("射手状态", "L1", "主力射手近期进球效率", 8),
    ("配合默契度", "L1", "预测首发球员国家队同场次数", 5),
    ("教练稳定性", "L1", "教练在任时长、体系成熟度", 3),
    # L2 战术
    ("控球率倾向", "L2", "控球型vs放弃控球型", 5),
    ("进攻方式", "L2", "边路传中/中路渗透/快攻反击", 6),
    ("防守风格", "L2", "高位压迫/中位拦截/低位大巴", 6),
    ("风格克制", "L2", "高位防线vs快马,大巴vs远射", 8),
    # L3 环境
    ("天气", "L3", "雨战/大风/高温对战术的影响", 3),
    ("裁判风格", "L3", "出牌率/判罚尺度vs球队风格", 7),
    ("旅途疲劳", "L3", "飞行距离/休息天数", 3),
    ("赛程密度", "L3", "一周双赛/三赛的轮换影响", 4),
    # L4 心理
    ("战意", "L4", "杯赛/保级/争冠动力", 8),
    ("历史交锋", "L4", "H2H心理优势", 4),
    ("近期士气", "L4", "连胜势头vs连败低迷", 5),
    ("大赛经验", "L4", "世界杯/欧冠决赛圈经验", 4),
    # L5 市场
    ("赔率变化", "L5", "初盘到即时盘走势", 5),
]

def seed():
    init_db()
    db = SessionLocal()
    existing = db.query(FactorConfig).count()
    if existing > 0:
        print("Seed data already exists, skipping.")
        db.close()
        return

    factor_map = {}
    for name, category, desc, weight in DEFAULT_FACTORS:
        f = FactorConfig(name=name, category=category, description=desc, default_weight=weight, is_custom=False)
        db.add(f)
        db.flush()
        factor_map[name] = f.id

    profile = FactorProfile(name="默认联赛模式", is_default=True, description="系统内置通用模式，适用于联赛和杯赛")
    db.add(profile)
    db.flush()

    for name, _, _, weight in DEFAULT_FACTORS:
        item = FactorProfileItem(
            profile_id=profile.id,
            factor_config_id=factor_map[name],
            weight=weight,
            enabled=True
        )
        db.add(item)

    db.commit()
    db.close()
    print(f"Seed: {len(DEFAULT_FACTORS)} factors + 1 default profile created.")

if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: 运行种子脚本**

Run: `python db/seed.py`
Expected: `Seed: 19 factors + 1 default profile created.`

- [ ] **Step 3: 验证数据**

Run: `python -c "from db.database import SessionLocal; from db.models import FactorConfig, FactorProfile; db=SessionLocal(); print('Factors:', db.query(FactorConfig).count()); print('Profiles:', db.query(FactorProfile).count()); db.close()"`
Expected: `Factors: 19` / `Profiles: 1`

- [ ] **Step 4: Commit**

```
git add db/seed.py
git commit -m "feat: seed data with 19 default factors and default profile"
```

---

## Task 4: 数据引擎 — football-data.org 适配器

**Files:**
- Create: `engines/data/sources/__init__.py`
- Create: `engines/data/sources/football_data.py`
- Create: `engines/data/fetcher.py`

- [ ] **Step 1: 创建 football_data.py 适配器**

```python
import httpx
from config import settings

BASE_URL = "https://api.football-data.org/v4"

class FootballDataClient:
    def __init__(self):
        self.headers = {"X-Auth-Token": settings.football_data_api_key}

    def _get(self, path: str, params: dict = None):
        url = f"{BASE_URL}{path}"
        resp = httpx.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_competitions(self):
        """获取可用联赛列表，筛选五大联赛+欧冠+世界杯"""
        target = {
            "PL": "英超", "PD": "西甲", "BL1": "德甲",
            "SA": "意甲", "FL1": "法甲", "CL": "欧冠", "WC": "世界杯"
        }
        data = self._get("/competitions")
        return [c for c in data.get("competitions", []) if c["code"] in target]

    def get_matches(self, competition_code: str, date_from: str, date_to: str):
        """获取指定联赛日期范围内的比赛"""
        return self._get(f"/competitions/{competition_code}/matches", {
            "dateFrom": date_from, "dateTo": date_to
        })

    def get_team(self, team_id: int):
        return self._get(f"/teams/{team_id}")

    def get_team_matches(self, team_id: int, limit: int = 10, status: str = "FINISHED"):
        """获取球队近期比赛"""
        return self._get(f"/teams/{team_id}/matches", {
            "limit": limit, "status": status
        })
```

- [ ] **Step 2: 创建 fetcher.py（调度器）**

```python
from engines.data.sources.football_data import FootballDataClient
from db.database import SessionLocal
from db.models import Team, Match
from datetime import datetime

LEAGUE_MAP = {
    "PL": "英超", "PD": "西甲", "BL1": "德甲",
    "SA": "意甲", "FL1": "法甲", "CL": "欧冠", "WC": "世界杯"
}

class DataFetcher:
    def __init__(self):
        self.client = FootballDataClient()
        self.db = SessionLocal()

    def sync_teams_for_competition(self, competition_code: str):
        """同步联赛中所有球队到本地数据库"""
        data = self.client.get_matches(competition_code, "2026-01-01", "2026-12-31")
        teams_seen = set()
        for match in data.get("matches", []):
            for side in ["homeTeam", "awayTeam"]:
                t = match[side]
                ext_id = t["id"]
                if ext_id not in teams_seen:
                    teams_seen.add(ext_id)
                    existing = self.db.query(Team).filter_by(external_id=ext_id).first()
                    if not existing:
                        team = Team(name=t["name"], short_name=t.get("shortName", ""), external_id=ext_id, league=LEAGUE_MAP.get(competition_code, ""))
                        self.db.add(team)
        self.db.commit()

    def sync_matches(self, competition_code: str, date_from: str, date_to: str):
        """同步比赛数据"""
        data = self.client.get_matches(competition_code, date_from, date_to)
        for m in data.get("matches", []):
            ext_id = m["id"]
            existing = self.db.query(Match).filter_by(external_id=ext_id).first()
            if existing:
                continue
            home = self.db.query(Team).filter_by(external_id=m["homeTeam"]["id"]).first()
            away = self.db.query(Team).filter_by(external_id=m["awayTeam"]["id"]).first()
            if not home or not away:
                continue
            match = Match(
                home_team_id=home.id, away_team_id=away.id,
                match_date=datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                league=LEAGUE_MAP.get(competition_code, ""),
                stage="league", status="scheduled",
                external_id=ext_id
            )
            self.db.add(match)
        self.db.commit()
        print(f"Synced {len(data.get('matches', []))} matches for {competition_code}")

    def close(self):
        self.db.close()
```

- [ ] **Step 3: 验证接口可用性**

Run: `python -c "from engines.data.sources.football_data import FootballDataClient; c=FootballDataClient(); comps=c.get_competitions(); print([c['code'] for c in comps])"`
Expected: 列出有权限访问的联赛代码（免费 tier 可能有限，至少应有 WC 相关）

- [ ] **Step 4: Commit**

```
git add engines/data/ -A
git commit -m "feat: football-data.org adapter and data fetcher"
```

---

## Task 5: 分析引擎 — 因子计算模块

**Files:**
- Create: `engines/analysis/__init__.py`
- Create: `engines/analysis/form.py`
- Create: `engines/analysis/tactics.py`
- Create: `engines/analysis/h2h.py`
- Create: `engines/analysis/squad_factor.py`
- Create: `engines/analysis/environment.py`
- Create: `engines/analysis/psychology.py`
- Create: `engines/analysis/market.py`
- Create: `engines/analysis/factors.py`

- [ ] **Step 1: 创建 form.py（近期状态 & 主客场 & 射手状态）**

```python
def calc_recent_form(team_matches: list[dict], n: int = 5) -> float:
    """计算近N场战绩得分 0-100"""
    if not team_matches:
        return 50.0
    recent = team_matches[-n:]
    wins = sum(1 for m in recent if _is_win(m))
    draws = sum(1 for m in recent if _is_draw(m))
    score = (wins * 100 + draws * 50) / len(recent)
    return score

def calc_home_away_split(team_matches: list[dict], is_home: bool) -> float:
    """主客场分离：主场/客场近期胜率，返回 0-100"""
    filtered = [m for m in team_matches if m.get("is_home") == is_home]
    if not filtered:
        return 50.0
    wins = sum(1 for m in filtered if _is_win(m))
    draws = sum(1 for m in filtered if _is_draw(m))
    return (wins * 100 + draws * 50) / len(filtered)

def calc_striker_form(team_matches: list[dict], striker_goals: float = 0) -> float:
    """射手状态：近5场进球效率 0-100。默认使用球队场均进球"""
    if not team_matches:
        return 50.0
    if striker_goals > 0:
        goals = striker_goals
    else:
        goals = sum(m.get("goals_for", 0) for m in team_matches[-5:]) / min(len(team_matches), 5)
    return min(goals * 25, 100.0)  # 场均4球=100分

def _is_win(m: dict) -> bool:
    return m.get("goals_for", 0) > m.get("goals_against", 0)

def _is_draw(m: dict) -> bool:
    return m.get("goals_for", 0) == m.get("goals_against", 0)
```

- [ ] **Step 2: 创建 tactics.py（战术风格 & 克制）**

```python
def calc_possession_style(possession_pct: float) -> float:
    """控球率倾向：偏高进攻型，偏低防守型。返回中性评分（后续在克制中体现）"""
    if possession_pct is None:
        return 50.0
    return min(possession_pct, 100.0)

def calc_attack_style(fast_break_ratio: float = 0.3, cross_ratio: float = 0.3, through_ratio: float = 0.4) -> dict:
    """返回进攻风格向量"""
    total = fast_break_ratio + cross_ratio + through_ratio
    return {"fast_break": fast_break_ratio/total, "cross": cross_ratio/total, "through": through_ratio/total}

def calc_defense_style(ppda: float = 10) -> str:
    """PPDA越低=压迫越高。返回: high_press / mid_block / low_block"""
    if ppda <= 8:
        return "high_press"
    elif ppda <= 14:
        return "mid_block"
    return "low_block"

def calc_style_matchup(home_style: dict, away_style: dict) -> float:
    """风格克制评分 0-100。高=主队有利"""
    score = 50.0
    # 高位防守 vs 快攻型
    if home_style.get("defense") == "high_press" and away_style.get("attack", {}).get("fast_break", 0) > 0.4:
        score -= 15
    elif away_style.get("defense") == "high_press" and home_style.get("attack", {}).get("fast_break", 0) > 0.4:
        score += 15
    # 低位防守 vs 渗透型
    if home_style.get("defense") == "low_block" and away_style.get("attack", {}).get("through", 0) > 0.4:
        score -= 10
    elif away_style.get("defense") == "low_block" and home_style.get("attack", {}).get("through", 0) > 0.4:
        score += 10
    return max(0, min(100, score))
```

- [ ] **Step 3: 创建 h2h.py（历史交锋）**

```python
def calc_h2h_advantage(h2h_matches: list[dict], team_a_id: int, team_b_id: int) -> float:
    """H2H心理优势 0-100。a有利=高分"""
    if not h2h_matches:
        return 50.0
    a_wins = sum(1 for m in h2h_matches if m.get("winner_id") == team_a_id)
    b_wins = sum(1 for m in h2h_matches if m.get("winner_id") == team_b_id)
    draws = len(h2h_matches) - a_wins - b_wins
    score = (a_wins * 100 + draws * 50) / len(h2h_matches)
    return max(0, min(100, score))
```

- [ ] **Step 4: 创建 squad_factor.py（阵容完整度 & 默契度）**

```python
def calc_squad_integrity(available_starters: int, ideal_starters: int = 11) -> float:
    """阵容完整度：可用主力人数/理论最强11人"""
    return (available_starters / ideal_starters) * 100

def calc_chemistry(players: list[str], co_appearances: dict[tuple[str, str], int]) -> float:
    """配合默契度：首发球员国家队同场平均次数"""
    if len(players) < 2:
        return 50.0
    total = 0
    count = 0
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            key = (players[i], players[j])
            total += co_appearances.get(key, 0)
            count += 1
    avg = total / count if count > 0 else 0
    return min(avg * 10, 100.0)  # 10场同场=100分
```

- [ ] **Step 5: 创建 environment.py（天气/裁判/旅途/赛程）**

```python
def calc_weather_impact(weather: str, home_possession: float) -> float:
    """天气影响: 雨战不利传控队=高分(不利于主队)"""
    impact = 0.0
    weather_map = {"rain": -0.08, "wind": -0.05, "hot": -0.05, "clear": 0.0}
    base = weather_map.get(weather, 0)
    if weather in ("rain", "wind") and home_possession > 55:
        base *= 1.5  # 传控队受天气影响更大
    return 50 + base * 100  # 归一化0-100

def calc_referee_impact(ref_avg_cards: float, team_fouls_per_game: float) -> float:
    """裁判风格: 出牌率 vs 球队犯规数"""
    if ref_avg_cards is None or team_fouls_per_game is None:
        return 50.0
    # 凶悍球队遇严格裁判 = 不利
    ratio = ref_avg_cards * team_fouls_per_game / 20
    return max(0, min(100, 50 - (ratio - 2) * 10))

def calc_travel_fatigue(distance_km: float, rest_days: int) -> float:
    """旅途疲劳: 飞行距离+休息天数"""
    if distance_km is None or rest_days is None:
        return 50.0
    fatigue = distance_km / 1000 - rest_days * 5
    return max(0, min(100, 50 + fatigue))

def calc_fixture_congestion(matches_7d: int) -> float:
    """赛程密度: 近7天比赛数"""
    if matches_7d <= 1:
        return 100.0
    if matches_7d == 2:
        return 70.0
    return 40.0
```

- [ ] **Step 6: 创建 psychology.py 和 market.py**

`psychology.py`:
```python
def calc_motivation(match_type: str, context: dict) -> float:
    """战意评分 0-100"""
    base = 60
    if match_type == "derby":
        base += 20
    if context.get("is_knockout"):
        base += 25
    if context.get("can_win_league"):
        base += 20
    if context.get("relegation_battle"):
        base += 15
    return min(100, base)

def calc_morale(recent_results: list[str]) -> float:
    """近期士气: result列表 W/D/L"""
    if not recent_results:
        return 50.0
    pts = {"W": 100, "D": 50, "L": 0}
    return sum(pts.get(r, 50) for r in recent_results[-5:]) / min(len(recent_results), 5)

def calc_experience(tournament_matches: int) -> float:
    """大赛经验: 决赛圈场次"""
    if tournament_matches >= 20:
        return 100.0
    return tournament_matches * 5
```

`market.py`:
```python
def calc_odds_movement(initial: float, current: float) -> float:
    """赔率变化: 初盘到即时盘走势。主胜赔率下降=有利"""
    if initial is None or current is None:
        return 50.0
    change_pct = (initial - current) / initial
    return max(0, min(100, 50 + change_pct * 200))
```

- [ ] **Step 7: 创建 factors.py（因子汇总加权引擎）**

```python
from db.database import SessionLocal
from db.models import FactorConfig, FactorProfile, FactorProfileItem, Match
from engines.analysis import form, tactics, h2h, squad_factor, environment, psychology, market

STAGE_CONFIDENCE = {
    "league": 1.0, "group_md1": 0.6, "group_md2": 0.8,
    "group_md3": 0.9, "r16": 0.9, "qf": 0.95, "sf": 1.0, "final": 1.0
}

class FactorEngine:
    def __init__(self, profile_id: int = None):
        self.db = SessionLocal()
        self.profile = self._load_profile(profile_id)

    def _load_profile(self, profile_id: int = None):
        if profile_id:
            return self.db.query(FactorProfile).filter_by(id=profile_id).first()
        return self.db.query(FactorProfile).filter_by(is_default=True).first()

    def get_weights(self) -> dict[str, dict]:
        """返回 {factor_name: {weight, enabled}}"""
        items = self.db.query(FactorProfileItem).filter_by(profile_id=self.profile.id).all()
        result = {}
        for item in items:
            name = item.factor.name
            result[name] = {"weight": item.weight, "enabled": item.enabled}
        return result

    def compute_lambda(self, match: Match, factor_inputs: dict) -> tuple[float, float, float]:
        """计算主客队进球期望和不确定系数"""
        weights = self.get_weights()
        stage_conf = STAGE_CONFIDENCE.get(match.stage, 1.0)

        home_score = 0.0
        away_score = 0.0
        uncertainty = 0.0
        total_weight = 0

        for name, config in weights.items():
            if not config["enabled"]:
                continue
            w = config["weight"]
            total_weight += w
            val = factor_inputs.get(name, 50.0)  # 默认中性50
            confidence = factor_inputs.get(f"{name}_confidence", 1.0) * stage_conf
            normalized = (val - 50) / 50  # -1 到 +1
            home_score += w * normalized
            away_score -= w * normalized
            uncertainty += w * (1 - confidence)

        if total_weight > 0:
            home_score /= total_weight
            away_score /= total_weight
            uncertainty /= total_weight

        # λ = baseline * exp(score)
        lambda_home = 1.4 * (2.718 ** home_score)
        lambda_away = 1.2 * (2.718 ** away_score)

        return lambda_home, lambda_away, uncertainty

    def close(self):
        self.db.close()
```

- [ ] **Step 8: 运行单元验证**

Run: `python -c "from engines.analysis.factors import FactorEngine; e=FactorEngine(); w=e.get_weights(); print(f'{len(w)} factors loaded'); e.close()"`
Expected: `19 factors loaded`

- [ ] **Step 9: Commit**

```
git add engines/analysis/ -A
git commit -m "feat: analysis engine with 19 factors and aggregation"
```

---

## Task 6: 模拟引擎 & 策略引擎

**Files:**
- Create: `engines/simulation/__init__.py`
- Create: `engines/simulation/model.py`
- Create: `engines/simulation/runner.py`
- Create: `engines/strategy/__init__.py`
- Create: `engines/strategy/risk.py`
- Create: `engines/strategy/bet.py`

- [ ] **Step 1: 创建 simulation/model.py（泊松分布模型）**

```python
import numpy as np

def simulate_one_match(lambda_home: float, lambda_away: float, uncertainty: float = 0.0) -> tuple[int, int]:
    """模拟一场比赛，返回 (主队进球, 客队进球)"""
    # 考虑不确定性：方差大于均值
    var_factor = 1 + uncertainty * 3
    lam_h = max(0.05, np.random.normal(lambda_home, np.sqrt(lambda_home * var_factor)))
    lam_a = max(0.05, np.random.normal(lambda_away, np.sqrt(lambda_away * var_factor)))
    home_goals = np.random.poisson(lam_h)
    away_goals = np.random.poisson(lam_a)
    return home_goals, away_goals

def monte_carlo_simulate(lambda_home: float, lambda_away: float, uncertainty: float = 0.0, n: int = 10000) -> dict:
    """蒙特卡洛模拟 n 次，返回统计结果"""
    results = {"home_wins": 0, "draws": 0, "away_wins": 0, "score_dist": {}, "total_goals": 0}

    for _ in range(n):
        h, a = simulate_one_match(lambda_home, lambda_away, uncertainty)
        results["total_goals"] += h + a
        key = f"{h}-{a}"
        results["score_dist"][key] = results["score_dist"].get(key, 0) + 1
        if h > a:
            results["home_wins"] += 1
        elif h == a:
            results["draws"] += 1
        else:
            results["away_wins"] += 1

    # 计算百分比
    pct = {
        "home_win_pct": round(results["home_wins"] / n * 100, 2),
        "draw_pct": round(results["draws"] / n * 100, 2),
        "away_win_pct": round(results["away_wins"] / n * 100, 2),
        "expected_goals": round(results["total_goals"] / n, 2),
        "lambda_home": round(lambda_home, 4),
        "lambda_away": round(lambda_away, 4),
        "variance": round(1 + uncertainty * 3, 2),
        "simulations": n,
    }

    # Top 5 比分分布
    sorted_scores = sorted(results["score_dist"].items(), key=lambda x: x[1], reverse=True)[:5]
    pct["score_distribution"] = {k: round(v / n * 100, 2) for k, v in sorted_scores}

    return pct
```

- [ ] **Step 2: 创建 simulation/runner.py**

```python
from engines.simulation.model import monte_carlo_simulate
from engines.analysis.factors import FactorEngine
from db.database import SessionLocal
from db.models import Match, SimulationResult

def run_simulation(match_id: int, profile_id: int = None, n: int = 10000) -> dict:
    db = SessionLocal()
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        db.close()
        raise ValueError(f"Match {match_id} not found")

    engine = FactorEngine(profile_id)
    # 获取因子输入（阶段性实现先全用默认值50）
    factor_inputs = {
        "近期战绩": 60, "主客场分离": 65, "阵容完整度": 80,
        "射手状态": 55, "配合默契度": 50, "教练稳定性": 60,
        "控球率倾向": 50, "进攻方式": 50, "防守风格": 50,
        "风格克制": 50, "天气": 50, "裁判风格": 50,
        "旅途疲劳": 50, "赛程密度": 70, "战意": 60,
        "历史交锋": 50, "近期士气": 55, "大赛经验": 50,
        "赔率变化": 50,
    }
    lam_h, lam_a, uncertainty = engine.compute_lambda(match, factor_inputs)
    result = monte_carlo_simulate(lam_h, lam_a, uncertainty, n)

    # 保存到数据库
    sim = SimulationResult(
        match_id=match_id,
        profile_id=engine.profile.id,
        home_win_pct=result["home_win_pct"],
        draw_pct=result["draw_pct"],
        away_win_pct=result["away_win_pct"],
        expected_goals=result["expected_goals"],
        score_distribution=result["score_distribution"],
        lambda_home=lam_h, lambda_away=lam_a,
        variance=result["variance"],
    )
    db.add(sim)
    db.commit()
    db.close()
    engine.close()
    return result
```

- [ ] **Step 3: 创建 strategy/risk.py**

```python
def calc_expected_value(sim_prob: float, odds: float) -> float:
    """期望值 = 模拟概率 x 赔率 - 1"""
    implied_prob = 1 / odds
    edge = (sim_prob / 100) * odds - 1
    return round(edge, 4)

def calc_risk_level(variance: float, edge: float) -> str:
    """风险等级"""
    if variance > 3 or edge < 0:
        return "high"
    if variance > 2 or edge < 0.05:
        return "medium"
    return "low"
```

- [ ] **Step 4: 创建 strategy/bet.py**

```python
def kelly_criterion(sim_prob: float, odds: float, fraction: float = 0.25) -> float:
    """凯利公式：b = odds-1, p = sim_prob, q = 1-p
    f = (b*p - q) / b * fraction"""
    b = odds - 1
    p = sim_prob / 100
    q = 1 - p
    raw_kelly = max(0, (b * p - q) / b) if b > 0 else 0
    return round(raw_kelly * fraction * 100, 2)  # 返回百分比

def generate_advice(sim_result: dict, odds_home: float = 2.0, odds_draw: float = 3.5, odds_away: float = 3.5) -> dict:
    """生成买入建议"""
    outcomes = {
        "home": {"prob": sim_result["home_win_pct"], "odds": odds_home},
        "draw": {"prob": sim_result["draw_pct"], "odds": odds_draw},
        "away": {"prob": sim_result["away_win_pct"], "odds": odds_away},
    }

    best = None
    best_edge = -999
    for key, val in outcomes.items():
        ev = calc_expected_value(val["prob"], val["odds"])
        if ev > best_edge:
            best_edge = ev
            best = key

    risk = calc_risk_level(sim_result["variance"], best_edge)

    advice = {
        "expected_value": best_edge,
        "best_pick": best,
        "risk_level": risk,
        "suggestion": "avoid",
    }

    if best_edge > 0.05:
        advice["suggestion"] = "buy"
        advice["kelly_stake"] = kelly_criterion(outcomes[best]["prob"], outcomes[best]["odds"])
    elif best_edge > 0:
        advice["suggestion"] = "watch"
    else:
        advice["suggestion"] = "avoid"

    return advice
```

- [ ] **Step 5: 验证模拟运行**

Run: `python -c "from engines.simulation.model import monte_carlo_simulate; r=monte_carlo_simulate(1.5, 1.2, 0.2, 1000); print(f'Home: {r[\"home_win_pct\"]}%, Draw: {r[\"draw_pct\"]}%, Away: {r[\"away_win_pct\"]}%')"`
Expected: 合理概率分布，如 Home: ~48%, Draw: ~25%, Away: ~27%

- [ ] **Step 6: Commit**

```
git add engines/simulation/ engines/strategy/ -A
git commit -m "feat: Monte Carlo simulation engine and Kelly strategy engine"
```

---

## Task 7: API 层 — 因子配置 CRUD + 比赛分析接口

**Files:**
- Create: `api/__init__.py`
- Create: `api/factors.py`
- Create: `api/profiles.py`
- Create: `api/matches.py`
- Create: `api/analysis.py`
- Create: `api/strategy.py`

- [ ] **Step 1: 创建 api/factors.py（因子 CRUD）**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import FactorConfig

router = APIRouter(prefix="/api/factors", tags=["factors"])

class FactorCreate(BaseModel):
    name: str
    category: str
    description: str = ""
    default_weight: int = 5

class FactorUpdate(BaseModel):
    name: str = None
    description: str = None
    default_weight: int = None

@router.get("")
def list_factors(db: Session = Depends(get_db)):
    return db.query(FactorConfig).all()

@router.post("")
def create_factor(data: FactorCreate, db: Session = Depends(get_db)):
    f = FactorConfig(name=data.name, category=data.category, description=data.description, default_weight=data.default_weight, is_custom=True)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f

@router.put("/{factor_id}")
def update_factor(factor_id: int, data: FactorUpdate, db: Session = Depends(get_db)):
    f = db.query(FactorConfig).filter_by(id=factor_id).first()
    if not f:
        raise HTTPException(404, "Factor not found")
    if data.name is not None: f.name = data.name
    if data.description is not None: f.description = data.description
    if data.default_weight is not None: f.default_weight = data.default_weight
    db.commit()
    return f

@router.delete("/{factor_id}")
def delete_factor(factor_id: int, db: Session = Depends(get_db)):
    f = db.query(FactorConfig).filter_by(id=factor_id).first()
    if not f:
        raise HTTPException(404, "Factor not found")
    db.delete(f)
    db.commit()
    return {"status": "deleted"}
```

- [ ] **Step 2: 创建 api/profiles.py（方案管理 CRUD）**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import FactorProfile, FactorProfileItem, FactorConfig

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

class ProfileCreate(BaseModel):
    name: str
    description: str = ""

class ProfileItemUpdate(BaseModel):
    factor_config_id: int
    weight: int
    enabled: bool = True

@router.get("")
def list_profiles(db: Session = Depends(get_db)):
    return db.query(FactorProfile).all()

@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not p:
        raise HTTPException(404, "Profile not found")
    items = db.query(FactorProfileItem).filter_by(profile_id=profile_id).all()
    return {"profile": p, "items": items}

@router.post("")
def create_profile(data: ProfileCreate, base_profile_id: int = None, db: Session = Depends(get_db)):
    profile = FactorProfile(name=data.name, description=data.description)
    db.add(profile)
    db.flush()

    base = None
    if base_profile_id:
        base = db.query(FactorProfile).filter_by(id=base_profile_id).first()
    else:
        base = db.query(FactorProfile).filter_by(is_default=True).first()

    if base:
        for item in db.query(FactorProfileItem).filter_by(profile_id=base.id).all():
            new_item = FactorProfileItem(profile_id=profile.id, factor_config_id=item.factor_config_id, weight=item.weight, enabled=item.enabled)
            db.add(new_item)

    db.commit()
    db.refresh(profile)
    return profile

@router.put("/{profile_id}/items")
def update_profile_items(profile_id: int, items: list[ProfileItemUpdate], db: Session = Depends(get_db)):
    profile = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    for item_data in items:
        existing = db.query(FactorProfileItem).filter_by(profile_id=profile_id, factor_config_id=item_data.factor_config_id).first()
        if existing:
            existing.weight = item_data.weight
            existing.enabled = item_data.enabled
    db.commit()
    return {"status": "updated"}

@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not p:
        raise HTTPException(404, "Profile not found")
    if p.is_default:
        raise HTTPException(400, "Cannot delete default profile")
    db.delete(p)
    db.commit()
    return {"status": "deleted"}
```

- [ ] **Step 3: 创建 api/matches.py（比赛列表 & 详情）**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Match

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.get("")
def list_matches(league: str = None, date_from: str = None, date_to: str = None, db: Session = Depends(get_db)):
    q = db.query(Match)
    if league:
        q = q.filter(Match.league == league)
    if date_from:
        q = q.filter(Match.match_date >= date_from)
    if date_to:
        q = q.filter(Match.match_date <= date_to)
    return q.order_by(Match.match_date).all()

@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(404, "Match not found")
    return {
        "id": m.id, "match_date": m.match_date.isoformat(),
        "league": m.league, "stage": m.stage, "status": m.status,
        "home_team": {"id": m.home_team.id, "name": m.home_team.name} if m.home_team else None,
        "away_team": {"id": m.away_team.id, "name": m.away_team.name} if m.away_team else None,
        "home_score": m.home_score, "away_score": m.away_score,
    }
```

- [ ] **Step 4: 创建 api/analysis.py（分析触发接口）**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import SimulationResult, Match
from engines.simulation.runner import run_simulation
from engines.strategy.bet import generate_advice

router = APIRouter(prefix="/api/matches", tags=["analysis"])

@router.post("/{match_id}/analyze")
def analyze_match(match_id: int, profile_id: int = Query(None), db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(404, "Match not found")

    sim_result = run_simulation(match_id, profile_id, n=10000)
    advice = generate_advice(sim_result)

    return {"simulation": sim_result, "advice": advice}

@router.get("/{match_id}/history")
def match_history(match_id: int, db: Session = Depends(get_db)):
    sims = db.query(SimulationResult).filter_by(match_id=match_id).order_by(SimulationResult.created_at.desc()).limit(5).all()
    return sims
```

- [ ] **Step 5: 注册路由到 main.py**

修改 `main.py`，在 `app = FastAPI(...)` 之后添加：

```python
from api import factors, profiles, matches, analysis, strategy
app.include_router(factors.router)
app.include_router(profiles.router)
app.include_router(matches.router)
app.include_router(analysis.router)
```

- [ ] **Step 6: 验证 API**

Run: `uvicorn main:app &` then:
`curl http://127.0.0.1:8000/api/factors` → 返回 19 个因子的 JSON 数组
`curl http://127.0.0.1:8000/api/profiles` → 返回默认方案

- [ ] **Step 7: Commit**

```
git add api/ -A
git add main.py
git commit -m "feat: REST API for factors, profiles, matches, analysis"
```

---

## Task 8: 前端基础页面

**Files:**
- Create: `web/index.html`
- Create: `web/css/style.css`
- Create: `web/js/app.js`

- [ ] **Step 1: 创建 web/index.html（基础布局 + 左栏比赛列表）**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>量化足球系统</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header class="app-header">
        <h1>⚽ 量化足球系统</h1>
        <span id="current-profile">方案: 默认联赛模式</span>
    </header>

    <div class="app-layout">
        <!-- 左侧比赛列表 -->
        <aside class="sidebar">
            <div class="filter-bar">
                <select id="league-filter">
                    <option value="">全部联赛</option>
                    <option value="英超">英超</option>
                    <option value="西甲">西甲</option>
                    <option value="德甲">德甲</option>
                    <option value="意甲">意甲</option>
                    <option value="法甲">法甲</option>
                    <option value="欧冠">欧冠</option>
                    <option value="世界杯">世界杯</option>
                </select>
                <input type="date" id="date-filter">
            </div>
            <ul id="match-list" class="match-list"></ul>
        </aside>

        <!-- 右侧主面板 -->
        <main class="main-panel" id="main-panel">
            <div class="placeholder">选择一场比赛开始分析</div>
        </main>
    </div>

    <script src="/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 web/css/style.css**

```css
:root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --text-dim: #8b8fa3;
    --accent: #4f8ff7;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
}

.app-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 24px; background: var(--surface); border-bottom: 1px solid var(--border);
}

.app-header h1 { font-size: 18px; }
.app-header span { color: var(--text-dim); font-size: 13px; }

.app-layout { display: flex; height: calc(100vh - 50px); }

.sidebar {
    width: 280px; background: var(--surface); border-right: 1px solid var(--border);
    overflow-y: auto; padding: 12px;
}

.filter-bar { display: flex; gap: 8px; margin-bottom: 12px; }
.filter-bar select, .filter-bar input {
    flex: 1; padding: 6px 8px; background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 4px; font-size: 12px;
}

.match-list { list-style: none; }
.match-item {
    padding: 10px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px;
    border: 1px solid transparent; transition: all 0.15s;
}
.match-item:hover { background: #252836; }
.match-item.active { border-color: var(--accent); background: #1e2a3a; }
.match-item .teams { font-size: 14px; font-weight: 600; }
.match-item .meta { font-size: 11px; color: var(--text-dim); margin-top: 2px; }

.main-panel { flex: 1; overflow-y: auto; padding: 20px; }
.placeholder { color: var(--text-dim); text-align: center; margin-top: 100px; font-size: 16px; }

.card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px; margin-bottom: 16px;
}
.card h3 { font-size: 14px; margin-bottom: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }

.result-bar { display: flex; gap: 0; border-radius: 6px; overflow: hidden; height: 28px; margin-bottom: 12px; }
.result-bar .home { background: var(--accent); }
.result-bar .draw { background: #555; }
.result-bar .away { background: var(--red); }
.result-labels { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-dim); }

.factor-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #1f2230; }
.factor-row label { width: 110px; font-size: 13px; flex-shrink: 0; }
.factor-row input[type="range"] { flex: 1; accent-color: var(--accent); }
.factor-row .weight-val { width: 35px; text-align: right; font-size: 13px; color: var(--accent); }
.factor-row input[type="checkbox"] { accent-color: var(--accent); }

.advice-box { padding: 12px 16px; border-radius: 6px; font-size: 14px; }
.advice-box.buy { background: #0f2d1a; border: 1px solid var(--green); color: var(--green); }
.advice-box.watch { background: #2d2810; border: 1px solid var(--yellow); color: var(--yellow); }
.advice-box.avoid { background: #2d1010; border: 1px solid var(--red); color: var(--red); }

.profile-selector { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
.profile-selector select { padding: 6px 10px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 4px; }
.profile-selector button { padding: 6px 12px; background: var(--accent); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }

.score-dist { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.score-dist .score-item { text-align: center; padding: 8px; background: var(--bg); border-radius: 4px; }
.score-dist .score { font-size: 16px; font-weight: 700; }
.score-dist .pct { font-size: 11px; color: var(--accent); }
```

- [ ] **Step 3: 创建 web/js/app.js**

```javascript
const API = '/api';
let currentMatchId = null;
let currentProfileId = null;

// 加载比赛列表
async function loadMatches() {
    const league = document.getElementById('league-filter').value;
    const date = document.getElementById('date-filter').value;
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    if (date) params.set('date_from', date);

    const resp = await fetch(`${API}/matches?${params}`);
    const matches = await resp.json();
    const list = document.getElementById('match-list');
    list.innerHTML = matches.map(m => `
        <li class="match-item${m.id === currentMatchId ? ' active' : ''}" onclick="selectMatch(${m.id})">
            <div class="teams">${m.home_team?.name || '?'} vs ${m.away_team?.name || '?'}</div>
            <div class="meta">${m.league} · ${new Date(m.match_date).toLocaleDateString('zh-CN')} · ${m.stage}</div>
        </li>
    `).join('');
}

// 选择比赛
async function selectMatch(matchId) {
    currentMatchId = matchId;
    await loadMatches();
    const resp = await fetch(`${API}/matches/${matchId}`);
    const match = await resp.json();
    renderMatchDetail(match);
}

// 渲染比赛详情
function renderMatchDetail(match) {
    const panel = document.getElementById('main-panel');
    panel.innerHTML = `
        <div class="card">
            <h3>比赛信息</h3>
            <h2 style="text-align:center; margin: 10px 0;">
                ${match.home_team?.name || '?'} vs ${match.away_team?.name || '?'}
            </h2>
            <p style="text-align:center; color:var(--text-dim);">${match.league} · ${match.stage} · ${new Date(match.match_date).toLocaleString('zh-CN')}</p>
            <button onclick="runAnalysis()" style="display:block; margin:12px auto; padding:8px 24px; background:var(--accent); color:#fff; border:none; border-radius:4px; cursor:pointer;">
                开始分析
            </button>
        </div>
        <div id="result-area"></div>
        <div id="factor-area"></div>
    `;
    loadFactorPanel();
}

// 运行分析
async function runAnalysis() {
    if (!currentMatchId) return;
    const params = currentProfileId ? `?profile_id=${currentProfileId}` : '';
    const resp = await fetch(`${API}/matches/${currentMatchId}/analyze`, { method: 'POST' + (params ? `?profile_id=${currentProfileId}` : '') });
    const data = await resp.json();
    renderResults(data);
}

// 渲染结果
function renderResults(data) {
    const sim = data.simulation;
    const adv = data.advice;
    const area = document.getElementById('result-area');
    area.innerHTML = `
        <div class="card">
            <h3>模拟结果（${sim.simulations} 次）</h3>
            <div class="result-bar">
                <div class="home" style="width:${sim.home_win_pct}%"></div>
                <div class="draw" style="width:${sim.draw_pct}%"></div>
                <div class="away" style="width:${sim.away_win_pct}%"></div>
            </div>
            <div class="result-labels">
                <span>主胜 ${sim.home_win_pct}%</span>
                <span>平局 ${sim.draw_pct}%</span>
                <span>客胜 ${sim.away_win_pct}%</span>
            </div>
            <p style="margin-top:8px; font-size:13px; color:var(--text-dim);">
                期望总进球: ${sim.expected_goals} · 波动系数: ${sim.variance} · λ主: ${sim.lambda_home} / λ客: ${sim.lambda_away}
            </p>
        </div>
        <div class="card">
            <h3>比分分布 Top 5</h3>
            <div class="score-dist">
                ${Object.entries(sim.score_distribution).map(([score, pct]) => `
                    <div class="score-item"><div class="score">${score}</div><div class="pct">${pct}%</div></div>
                `).join('')}
            </div>
        </div>
        <div class="card">
            <h3>买入建议</h3>
            <div class="advice-box ${adv.suggestion}">
                ${adv.suggestion === 'buy' ? '✅ 建议买入' : adv.suggestion === 'watch' ? '⚠️ 观望' : '🚫 回避'} &nbsp;
                最佳选择: ${adv.best_pick === 'home' ? '主胜' : adv.best_pick === 'draw' ? '平局' : '客胜'} &nbsp;
                期望值: ${adv.expected_value > 0 ? '+' : ''}${adv.expected_value}
                ${adv.kelly_stake ? ` · 建议仓位: ${adv.kelly_stake}%` : ''}
            </div>
            <p style="margin-top:8px; font-size:12px; color:var(--text-dim);">风险等级: ${adv.risk_level}</p>
        </div>
    `;
}

// 加载因子面板
async function loadFactorPanel() {
    const area = document.getElementById('factor-area');
    const profilesResp = await fetch(`${API}/profiles`);
    const profiles = await profilesResp.json();
    const factorsResp = await fetch(`${API}/factors`);
    const factors = await factorsResp.json();

    const defaultProfile = profiles.find(p => p.is_default);
    const profileResp = await fetch(`${API}/profiles/${defaultProfile?.id || profiles[0]?.id}`);
    const profileData = await profileResp.json();

    currentProfileId = profileData.profile?.id;
    document.getElementById('current-profile').textContent = `方案: ${profileData.profile?.name || '默认'}`;

    const cats = { L1: '基本面', L2: '战术风格', L3: '环境因素', L4: '心理/战意', L5: '市场信号' };

    area.innerHTML = `
        <div class="card">
            <h3>因子配置</h3>
            <div class="profile-selector">
                <select onchange="switchProfile(this.value)">
                    ${profiles.map(p => `<option value="${p.id}" ${p.id === currentProfileId ? 'selected' : ''}>${p.name}</option>`).join('')}
                </select>
                <button onclick="saveProfile()">保存</button>
                <button onclick="createProfile()">新建方案</button>
            </div>
            ${Object.entries(cats).map(([key, label]) => `
                <div style="margin-bottom:10px;">
                    <div style="font-size:12px; color:var(--accent); margin-bottom:4px;">${label}</div>
                    ${profileData.items.filter(i => i.factor?.category === key).map(i => `
                        <div class="factor-row">
                            <input type="checkbox" ${i.enabled ? 'checked' : ''} onchange="toggleFactor(${i.id}, this.checked)">
                            <label>${i.factor?.name || '?'}</label>
                            <input type="range" min="0" max="30" value="${i.weight}" oninput="this.nextElementSibling.textContent=this.value+'%'; updateWeight(${i.id}, this.value)">
                            <span class="weight-val">${i.weight}%</span>
                        </div>
                    `).join('')}
                </div>
            `).join('')}
        </div>
    `;
}

function updateWeight(itemId, val) {
    // 临时前端更新，保存时批量提交
}

function toggleFactor(itemId, enabled) {
    // 临时前端更新，保存时批量提交
}

async function saveProfile() {
    // 收集所有因子行数据并提交
    const rows = document.querySelectorAll('.factor-row');
    const items = [];
    rows.forEach(row => {
        const checkbox = row.querySelector('input[type="checkbox"]');
        const range = row.querySelector('input[type="range"]');
        items.push({
            factor_config_id: parseInt(row.dataset?.itemId || 0),
            weight: parseInt(range.value),
            enabled: checkbox.checked
        });
    });
    await fetch(`${API}/profiles/${currentProfileId}/items`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items)
    });
    alert('方案已保存');
}

async function createProfile() {
    const name = prompt('新方案名称:');
    if (!name) return;
    const resp = await fetch(`${API}/profiles?base_profile_id=${currentProfileId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
    const data = await resp.json();
    currentProfileId = data.id;
    await loadFactorPanel();
}

async function switchProfile(id) {
    currentProfileId = parseInt(id);
    await loadFactorPanel();
}

// 初始化
loadMatches();
```

- [ ] **Step 4: 验证前端**

Run: `uvicorn main:app --host 127.0.0.1 --port 8000`
Open: `http://127.0.0.1:8000`
Expected: 左侧比赛列表 + 右侧空白主面板

- [ ] **Step 5: Commit**

```
git add web/ -A
git commit -m "feat: frontend - match list, factor panel, simulation results"
```

---

## Task 9: LLM 集成

**Files:**
- Create: `llm/__init__.py`
- Create: `llm/client.py`
- Create: `llm/scout.py`
- Create: `llm/advisor.py`
- Create: `llm/interpreter.py`

- [ ] **Step 1: 创建 llm/client.py（OpenAI 兼容封装）**

```python
from openai import OpenAI
from config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    return _client

def chat(system_prompt: str, user_message: str, model: str = None, temperature: float = 0.3) -> str:
    """发送 Chat Completion 请求，返回文本"""
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=model or settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=800,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[LLM 不可用] {e}"
```

- [ ] **Step 2: 创建 llm/scout.py（赛前情报分析）**

```python
from llm.client import chat

SYSTEM_PROMPT = """你是一位资深足球分析师。根据提供的数据，输出一份结构化的赛前分析报告。
格式要求：
1. 球队状态对比（2-3句）
2. 关键对位分析（2个关键对位）
3. 潜在风险点（1-2个）
4. 综合预判（1句）
使用中文，简洁专业，不超过300字。"""

def generate_scout_report(match_info: dict, factor_scores: dict) -> str:
    user_msg = f"""
比赛: {match_info.get('home_team', '主队')} vs {match_info.get('away_team', '客队')}
赛事: {match_info.get('league', '')} · {match_info.get('stage', '联赛')}

因子评分:
{chr(10).join(f'- {k}: {v}' for k, v in factor_scores.items())}
"""
    return chat(SYSTEM_PROMPT, user_msg)
```

- [ ] **Step 3: 创建 llm/advisor.py（因子建议）**

```python
from llm.client import chat

SYSTEM_PROMPT = """你是一位量化足球因子专家。根据比赛上下文，建议哪些因子应该调高权重。
返回 JSON 格式: {"suggestions": [{"factor": "因子名", "current_weight": 5, "suggested_weight": 10, "reason": "原因"}]}
只能建议 0-3 个因子调整，没有好的建议就返回空数组。"""

def get_factor_advice(match_info: dict, current_weights: dict) -> list[dict]:
    import json
    user_msg = f"""
比赛: {match_info.get('home_team', '')} vs {match_info.get('away_team', '')}
赛事: {match_info.get('league', '')} · 阶段: {match_info.get('stage', '')}
当前权重: {json.dumps(current_weights, ensure_ascii=False)}
"""
    resp = chat(SYSTEM_PROMPT, user_msg, temperature=0.2)
    try:
        return json.loads(resp).get("suggestions", [])
    except json.JSONDecodeError:
        return []
```

- [ ] **Step 4: 创建 llm/interpreter.py（结果解读）**

```python
from llm.client import chat

SYSTEM_PROMPT = """你是一位量化足球结果解读专家。根据模拟数据和策略建议，输出一段自然语言总结。
用中文，2-4句，简洁有力。提到：胜率、关键因子、风险提示。"""

def interpret_results(sim_result: dict, advice: dict, match_info: dict) -> str:
    user_msg = f"""
{sim_result.get('home_win_pct', '?')}% | 平 {sim_result.get('draw_pct', '?')}% | 客胜 {sim_result.get('away_win_pct', '?')}%
期望值: {advice.get('expected_value', '?')}
建议: {advice.get('suggestion', '?')}
波动系数: {sim_result.get('variance', '?')}
"""
    return chat(SYSTEM_PROMPT, user_msg)
```

- [ ] **Step 5: 创建 api/llm.py（LLM 接口）**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import Match
from llm.scout import generate_scout_report
from llm.interpreter import interpret_results
from engines.simulation.runner import run_simulation
from engines.strategy.bet import generate_advice

router = APIRouter(prefix="/api/llm", tags=["llm"])

class ScoutRequest(BaseModel):
    match_id: int
    profile_id: int = None

@router.post("/scout")
def scout(req: ScoutRequest, db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=req.match_id).first()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(404, "Match not found")
    info = {"home_team": m.home_team.name, "away_team": m.away_team.name, "league": m.league, "stage": m.stage}
    sim = run_simulation(req.match_id, req.profile_id, n=5000)
    advice = generate_advice(sim)
    report = generate_scout_report(info, sim.get("score_distribution", {}))
    interpretation = interpret_results(sim, advice, info)
    return {"scout_report": report, "interpretation": interpretation}
```

- [ ] **Step 6: 注册 LLM 路由到 main.py**

```python
from api import llm
app.include_router(llm.router)
```

- [ ] **Step 7: Commit**

```
git add llm/ api/llm.py main.py -A
git commit -m "feat: LLM integration - scout, advisor, interpreter"
```

---

## Task 10: 首发预测 & 新闻交叉验证（P2 收尾）

**Files:**
- Create: `engines/data/squad/__init__.py`
- Create: `engines/data/squad/predictor.py`
- Create: `engines/data/news/__init__.py`
- Create: `engines/data/news/aggregator.py`
- Create: `engines/data/news/verifier.py`

- [ ] **Step 1: 创建 predictor.py（首发预测引擎）**

```python
from db.database import SessionLocal
from db.models import StartingXI, Match

def predict_starting_xi(match_id: int, team_id: int, squad_list: list[dict], recent_lineups: list[list[str]], formation: str = "4-3-3") -> list[dict]:
    """从大名单预测首发11人。
    squad_list: [{"name": "球员名", "position": "GK", "is_injured": False, "is_suspended": False}]
    recent_lineups: [["球员A", "球员B", ...], ...] 近期首发阵容列表
    """
    available = [p for p in squad_list if not p["is_injured"] and not p["is_suspended"]]

    # 统计最近首发频率
    starter_freq = {}
    for lineup in recent_lineups[-5:]:
        for name in lineup:
            starter_freq[name] = starter_freq.get(name, 0) + 1

    # 分配位置模板
    position_slots = {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3}

    result = []
    for pos, count in position_slots.items():
        candidates = [p for p in available if p["position"] == pos]
        candidates.sort(key=lambda p: starter_freq.get(p["name"], 0), reverse=True)
        for p in candidates[:count]:
            confidence = min(100, starter_freq.get(p["name"], 0) * 20 + 40)
            result.append({
                "player_name": p["name"],
                "position": pos,
                "predicted_role": "starter",
                "confidence": confidence,
                "formation": formation,
            })

    # 剩余标记为替补
    starter_names = {r["player_name"] for r in result}
    for p in available:
        if p["name"] not in starter_names:
            result.append({
                "player_name": p["name"],
                "position": p["position"],
                "predicted_role": "bench",
                "confidence": 70,
                "formation": formation,
            })

    return result

def save_starting_xi(match_id: int, team_id: int, predictions: list[dict]):
    db = SessionLocal()
    # 删除旧预测
    db.query(StartingXI).filter_by(match_id=match_id, team_id=team_id).delete()
    for p in predictions:
        xi = StartingXI(match_id=match_id, team_id=team_id, **p)
        db.add(xi)
    db.commit()
    db.close()
```

- [ ] **Step 2: 创建 news/aggregator.py（新闻聚合器）**

```python
import feedparser

SOURCES = {
    "skysports": {"url": "https://www.skysports.com/football/rss", "tier": 2},
    "espn": {"url": "https://www.espn.com/espn/rss/soccer/news", "tier": 2},
    "bbc": {"url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "tier": 2},
}

def fetch_news(max_per_source: int = 10) -> list[dict]:
    """聚合多个 RSS 源的新闻"""
    items = []
    for name, config in SOURCES.items():
        try:
            feed = feedparser.parse(config["url"])
            for entry in feed.entries[:max_per_source]:
                items.append({
                    "source": name,
                    "source_tier": config["tier"],
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                })
        except Exception:
            continue
    return items
```

- [ ] **Step 3: 创建 news/verifier.py（交叉验证）**

```python
def cluster_news(news_items: list[dict]) -> dict[str, list[dict]]:
    """按球队+话题聚类"""
    clusters = {}
    for item in news_items:
        title = item.get("title", "")
        # 简单关键词匹配聚类（后续可升级 LLM 聚类）
        key = _extract_team_topic(title)
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(item)
    return clusters

def verify_claim(cluster: list[dict]) -> dict:
    """验证一个聚类中的说法"""
    if not cluster:
        return {"consensus_score": 0, "verdict": "unconfirmed"}

    tier_weights = {1: 1.0, 2: 0.75, 3: 0.6, 4: 0.35, 5: 0.15}
    total_weight = sum(tier_weights.get(item["source_tier"], 0.1) for item in cluster)
    high_tier = any(item.get("source_tier", 5) <= 2 for item in cluster)

    if total_weight >= 3 and high_tier:
        return {"consensus_score": 80, "verdict": "confirmed"}
    elif total_weight >= 1.5:
        return {"consensus_score": 50, "verdict": "disputed"}
    else:
        return {"consensus_score": 20, "verdict": "unconfirmed"}

def detect_smoke(cluster: list[dict]) -> bool:
    """烟雾弹识别"""
    tiers = [item.get("source_tier", 5) for item in cluster]
    # 仅有低等级来源
    if all(t >= 4 for t in tiers):
        return True
    # 来源单一
    if len(set(item.get("source", "") for item in cluster)) == 1:
        return True
    return False

def _extract_team_topic(title: str) -> str:
    keywords = ["受伤", "injury", "首发", "lineup", "转会", "transfer", "战术", "tactic", "轮休", "rest"]
    for kw in keywords:
        if kw.lower() in title.lower():
            return kw
    return "other"
```

- [ ] **Step 4: Commit**

```
git add engines/data/squad/ engines/data/news/ -A
git commit -m "feat: squad prediction engine and news cross-verification"
```
