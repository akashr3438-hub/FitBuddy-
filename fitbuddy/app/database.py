"""SQLite persistence via SQLAlchemy."""
import os
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fitbuddy.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    intensity = Column(String, nullable=False)
    plan = relationship("Plan", uselist=False, back_populates="user", cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text)
    nutrition_tip = Column(Text)
    user = relationship("User", back_populates="plan")


def init_db():
    Base.metadata.create_all(bind=engine)


def save_user(data: dict) -> None:
    """Insert the user, or refresh their details if the user_id already exists."""
    with SessionLocal() as db:
        user = db.get(User, data["user_id"])
        if user:
            for k, v in data.items():
                setattr(user, k, v)
        else:
            db.add(User(**data))
        db.commit()


def save_plan(user_id: str, plan: str, tip: str) -> None:
    """Store a freshly generated plan; resets any earlier update."""
    with SessionLocal() as db:
        row = db.query(Plan).filter_by(user_id=user_id).first()
        if row:
            row.original_plan, row.nutrition_tip, row.updated_plan = plan, tip, None
        else:
            db.add(Plan(user_id=user_id, original_plan=plan, nutrition_tip=tip))
        db.commit()


def update_plan(user_id: str, updated: str) -> None:
    with SessionLocal() as db:
        row = db.query(Plan).filter_by(user_id=user_id).first()
        if row:
            row.updated_plan = updated
            db.commit()


def get_user(user_id: str):
    with SessionLocal() as db:
        u = db.get(User, user_id)
        return None if not u else {c.name: getattr(u, c.name) for c in User.__table__.columns}


def get_original_plan(user_id: str):
    with SessionLocal() as db:
        row = db.query(Plan).filter_by(user_id=user_id).first()
        return row.original_plan if row else None


def get_current_plan(user_id: str):
    """The latest version: updated plan if there is one, else the original."""
    with SessionLocal() as db:
        row = db.query(Plan).filter_by(user_id=user_id).first()
        return None if not row else (row.updated_plan or row.original_plan)


def get_tip(user_id: str):
    with SessionLocal() as db:
        row = db.query(Plan).filter_by(user_id=user_id).first()
        return row.nutrition_tip if row else None


def get_all_users():
    with SessionLocal() as db:
        return [{c.name: getattr(u, c.name) for c in User.__table__.columns} for u in db.query(User).all()]


def get_all_plans():
    with SessionLocal() as db:
        return {p.user_id: {"original": p.original_plan, "updated": p.updated_plan, "tip": p.nutrition_tip}
                for p in db.query(Plan).all()}


def delete_user(user_id: str) -> None:
    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()
