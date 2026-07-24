from __future__ import annotations

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class RecipeModel(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("recipe_sources.id"), nullable=False)
    title = Column(String, nullable=False)
    ingredients = Column(JSON, nullable=False, default=list)
    preparation_steps = Column(JSON, nullable=False, default=list)
    portions = Column(Integer, nullable=False, default=1)
    restrictions = Column(JSON, nullable=False, default=list)
    version = Column(String, nullable=False, default="1")
    previous_version_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    source = relationship("RecipeSourceModel", back_populates="recipes")


class RecipeSourceModel(Base):
    __tablename__ = "recipe_sources"

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    collected_at = Column(DateTime, server_default=func.now(), nullable=False)
    content_version = Column(String, nullable=False, default="1")

    recipes = relationship("RecipeModel", back_populates="source", cascade="all, delete-orphan")


class IngredientModel(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True)
    canonical_name = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    aliases = Column(JSON, nullable=False, default=list)
    restrictions = Column(JSON, nullable=False, default=list)


class InventoryItemModel(Base):
    __tablename__ = "inventory_items"

    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), nullable=False)
    canonical_name = Column(String, nullable=False)
    original_input = Column(String, nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)


def create_session(db_url: str = "sqlite:///data/recipes.db"):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
