from typing import TypedDict

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Photo(TypedDict):
    """строка фотографии."""

    photo_string: str


class IngredientResHint(TypedDict):
    """содержит сведения игредиента."""

    id: int
    name: str


class IngredientResult(TypedDict):
    """Хинт получаемого игредиента/напитка. при запросе поьзователя."""

    name: str
    description: str
    photos: list[Photo]

class DrinkResult(IngredientResult):
    """Хинт получаемого напитка с ингредиентами. при запросе поьзователя."""

    ingredients: IngredientResHint


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(200), nullable=True, comment="имя клиента из отзыва/предложения")
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    created_dt: Mapped[DateTime] = mapped_column(DateTime,
                                                 nullable=False,
                                                 server_default=func.timezone('Europe/Moscow', func.now()))
    tg_username: Mapped[str] = mapped_column(String(500), nullable=True, comment="ник пользователя.")
    first_name: Mapped[str] = mapped_column(String(200), nullable=True)
    full_name: Mapped[str] = mapped_column(String(400), nullable=True)
    last_name: Mapped[str] = mapped_column(String(200), nullable=True)
    update_dt: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    been_deleted: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="True удалил, False | None подписан.")
    feedback: Mapped[list["FeedBack"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class DrinkIngredientAssociation(Base):
    """ORM Модель для связи many-to-many с таблицами Drinks & Ingredient."""

    __tablename__ = "drink_ingredient_association"

    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    photos: Mapped[list["Photo"]] = relationship(back_populates="ingredient", cascade="all, delete-orphan")
    drinks: Mapped[list["Drink"]] = relationship(
        secondary=DrinkIngredientAssociation.__tablename__, back_populates="ingredients"
    )

    def ingredient_to_dict(self) -> IngredientResult:
        """Собираем словарь с вложенными объектами из других таблиц."""
        ingredient_dict = {
            "name": self.name,
            "description": self.description,
            "photos": [],
        }
        if self.photos:
            ingredient_dict["photos"] = [{"photo_string": photo.photo_string} for photo in self.photos]
        return ingredient_dict


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_string: Mapped[str] = mapped_column(String(2000), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=True)  # FK к таблице ingredients
    ingredient: Mapped[Ingredient] = relationship(back_populates="photos")  # Связь с Ingredient
    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), nullable=True)  # FK к таблице drinks
    drink: Mapped["Drink"] = relationship(back_populates="photos")  # Связь с Drink
    feedback_id: Mapped[int] = mapped_column(ForeignKey("feedback.id"), nullable=True)  # FK к таблице feedback
    feedback: Mapped["FeedBack"] = relationship(back_populates="photos")  # Связь с Drink


class FeedBack(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(None), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=True)
    created_dt: Mapped[DateTime] = mapped_column(DateTime,
                                                 nullable=False,
                                                 server_default=func.timezone('Europe/Moscow', func.now()))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Foreign key к таблице ingredients
    user: Mapped[User] = relationship(back_populates="feedback")  # Связь с Ingredient
    photos: Mapped[list["Photo"]] = relationship(back_populates="feedback", cascade="all, delete-orphan")
    # ALTER TABLE feedback ADD COLUMN created_dt
    # timestamp without time zone NOT NULL DEFAULT (NOW() AT TIME ZONE 'Europe/Moscow');


class Drink(Base):
    __tablename__ = "drinks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    created_dt: Mapped[DateTime] = mapped_column(DateTime,
                                                 nullable=False,
                                                 server_default=func.timezone('Europe/Moscow', func.now()))
    update_dt: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    ingredients: Mapped[list["Ingredient"]] = relationship(
        secondary=DrinkIngredientAssociation.__tablename__,
        back_populates="drinks",
    )
    photos: Mapped[list["Photo"]] = relationship(back_populates="drink", cascade="all, delete-orphan")

    def drink_to_dict(self) -> DrinkResult:
        """Собираем словарь с вложенными объектами из других таблиц."""
        drink_dict = {
            "name": self.name,
            "description": self.description,
            "photos": [],
            "ingredients": [],
        }
        if self.photos:
            drink_dict["photos"] = [{"photo_string": photo.photo_string} for photo in self.photos]
        if self.ingredients:
            drink_dict["ingredients"] = [
                {"id": ingredient.id, "name": ingredient.name}
                for ingredient in self.ingredients
            ]
        return drink_dict
