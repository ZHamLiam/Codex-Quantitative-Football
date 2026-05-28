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
    stage = Column(String(30), default="league")
    status = Column(String(20), default="scheduled")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    external_id = Column(Integer, unique=True)
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

class FactorConfig(Base):
    __tablename__ = "factor_configs"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(10), nullable=False)
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
    weight = Column(Integer, default=5)
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
    score_distribution = Column(JSON)
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
    position = Column(String(10))
    predicted_role = Column(String(10), default="bench")
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
    source_tier = Column(Integer, default=3)
    player_mentioned = Column(String(100))
    topic = Column(String(30))
    claim = Column(Text)
    sentiment = Column(String(10))
    consensus_score = Column(Integer)
    verdict = Column(String(20))
    url = Column(String(500))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
