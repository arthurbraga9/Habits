# db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, default="")
    strava_token = Column(String, nullable=True)
    garmin_token = Column(String, nullable=True)
    apple_token = Column(String, nullable=True)
    goals = relationship("Goal", back_populates="user", cascade="all, delete")
    logs = relationship("Log", back_populates="user", cascade="all, delete")
    followers = relationship("Follow", back_populates="followed", foreign_keys='Follow.followed_id')
    following = relationship("Follow", back_populates="follower", foreign_keys='Follow.follower_id')

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    activity = Column(String)
    target = Column(Float)
    user = relationship("User", back_populates="goals")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    activity = Column(String)
    value = Column(Float)
    distance = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    proof_url = Column(String, nullable=True)
    cheers = Column(Integer, default=0)
    user = relationship("User", back_populates="logs")

class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    followed_id = Column(Integer, ForeignKey('users.id'))
    follower = relationship("User", back_populates="following", foreign_keys=[follower_id])
    followed = relationship("User", back_populates="followers", foreign_keys=[followed_id])

engine = create_engine(config.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Utility functions

def get_user_by_email(db_session, email: str):
    return db_session.query(User).filter(User.email == email).first()

def create_user(db_session, email: str, name: str = ""):
    user = User(email=email, name=name)
    db_session.add(user)
    for act, goal in config.DEFAULT_GOALS.items():
        user.goals.append(Goal(activity=act, target=goal))
    db_session.commit()
    return user

def add_log(db_session, user: User, activity: str, value: float, timestamp: datetime, proof_path: str = None, distance: float = None):
    log = Log(
        user_id=user.id,
        activity=activity,
        value=value,
        distance=distance,
        timestamp=timestamp,
        proof_url=proof_path,
    )
    db_session.add(log)
    db_session.commit()
    return log

def get_followed_user_ids(db_session, user: User):
    return [f.followed_id for f in user.following]


def update_user_token(db_session, user: User, service: str, token: str):
    if service == "strava":
        user.strava_token = token
    elif service == "garmin":
        user.garmin_token = token
    elif service == "apple":
        user.apple_token = token
    db_session.commit()


def get_user_token(user: User, service: str):
    if service == "strava":
        return user.strava_token
    if service == "garmin":
        return user.garmin_token
    if service == "apple":
        return user.apple_token
    return None
