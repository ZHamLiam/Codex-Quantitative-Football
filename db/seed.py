from db.database import SessionLocal, init_db
from db.models import FactorConfig, FactorProfile, FactorProfileItem

DEFAULT_FACTORS = [
    ("近期战绩", "L1", "近5/10场胜率、进球、失球", 20),
    ("主客场分离", "L1", "主场vs客场表现差异", 10),
    ("阵容完整度", "L1", "伤病/停赛对比理论最强11人", 12),
    ("射手状态", "L1", "主力射手近期进球效率", 8),
    ("配合默契度", "L1", "预测首发球员国家队同场次数", 5),
    ("教练稳定性", "L1", "教练在任时长、体系成熟度", 3),
    ("控球率倾向", "L2", "控球型vs放弃控球型", 5),
    ("进攻方式", "L2", "边路传中/中路渗透/快攻反击", 6),
    ("防守风格", "L2", "高位压迫/中位拦截/低位大巴", 6),
    ("风格克制", "L2", "高位防线vs快马,大巴vs远射", 8),
    ("天气", "L3", "雨战/大风/高温对战术的影响", 3),
    ("裁判风格", "L3", "出牌率/判罚尺度vs球队风格", 7),
    ("旅途疲劳", "L3", "飞行距离/休息天数", 3),
    ("赛程密度", "L3", "一周双赛/三赛的轮换影响", 4),
    ("战意", "L4", "杯赛/保级/争冠动力", 8),
    ("历史交锋", "L4", "H2H心理优势", 4),
    ("近期士气", "L4", "连胜势头vs连败低迷", 5),
    ("大赛经验", "L4", "世界杯/欧冠决赛圈经验", 4),
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
