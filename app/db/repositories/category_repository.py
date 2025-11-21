from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def exists(self, category_id: UUID) -> bool:
        return (
            self.db.query(Category.id)
            .filter(Category.id == category_id)
            .first()
            is not None
        )

    def list_all(self) -> list[Category]:
        return self.db.query(Category).order_by(Category.name.asc()).all()
