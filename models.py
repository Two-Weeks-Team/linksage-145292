import os
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    func,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Resolve DATABASE_URL with auto‑fix logic
_db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "sqlite:///./app.db"
if _db_url.startswith("postgresql+asyncpg://"):
    _db_url = _db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+psycopg://")

# Add SSL mode for non‑local PostgreSQL connections
if _db_url.startswith("postgresql+psycopg://"):
    if "localhost" not in _db_url and "127.0.0.1" not in _db_url:
        engine = create_engine(_db_url, connect_args={"sslmode": "require"})
    else:
        engine = create_engine(_db_url)
else:
    engine = create_engine(_db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Table name prefix – avoids collisions in shared DB
_PREFIX = "ls_"

# Association table for many‑to‑many Bookmark ↔ Tag
bookmark_tag = Table(
    f"{_PREFIX}bookmark_tag",
    Base.metadata,
    Column("bookmark_id", Integer, ForeignKey(f"{_PREFIX}bookmark.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey(f"{_PREFIX}tag.id"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now()),
)

class User(Base):
    __tablename__ = f"{_PREFIX}user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    bookmarks = relationship("Bookmark", back_populates="owner")
    favorites = relationship("Favorite", back_populates="owner")

class Bookmark(Base):
    __tablename__ = f"{_PREFIX}bookmark"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f"{_PREFIX}user.id"), nullable=False)
    url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    summary = Column(Text, nullable=True)
    favorite = Column(Boolean, default=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="bookmarks")
    tags = relationship("Tag", secondary=bookmark_tag, back_populates="bookmarks")
    favorites = relationship("Favorite", back_populates="bookmark")

class Tag(Base):
    __tablename__ = f"{_PREFIX}tag"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    bookmarks = relationship("Bookmark", secondary=bookmark_tag, back_populates="tags")

class Favorite(Base):
    __tablename__ = f"{_PREFIX}favorite"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f"{_PREFIX}user.id"), nullable=False)
    bookmark_id = Column(Integer, ForeignKey(f"{_PREFIX}bookmark.id"), nullable=False)
    favorited_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="favorites")
    bookmark = relationship("Bookmark", back_populates="favorites")
