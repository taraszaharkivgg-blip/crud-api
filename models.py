from sqlalchemy import String, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List as PyList
from db import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    boards: Mapped[PyList['Board']] = relationship(back_populates='owner', cascade='all, delete-orphan')

class Board(Base):
    __tablename__ = 'boards'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

    owner: Mapped['User'] = relationship(back_populates='boards')
    lists: Mapped[PyList['BoardList']] = relationship(back_populates='board', cascade='all, delete-orphan')

class BoardList(Base):
    __tablename__ = 'lists'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    board_id: Mapped[int] = mapped_column(ForeignKey('boards.id', ondelete='CASCADE'))
    position: Mapped[float] = mapped_column(Float, default=100.0)

    board: Mapped['Board'] = relationship(back_populates='lists')
    cards: Mapped[PyList['Card']] = relationship(back_populates='list', cascade='all, delete-orphan')

class Card(Base):
    __tablename__ = 'cards'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    list_id: Mapped[int] = mapped_column(ForeignKey('lists.id', ondelete='CASCADE'))
    position: Mapped[float] = mapped_column(Float, default=100.0)

    list: Mapped['BoardList'] = relationship(back_populates='cards')