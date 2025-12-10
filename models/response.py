from __future__ import annotations

from datetime import datetime
from typing import Any

from extension import db


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    id_document = db.Column(db.String(255), unique=True, nullable=False)
    entities = db.Column(db.JSON, nullable=True)
    corrections_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "id_document": self.id_document,
            "entities": self.entities,
            "corrections_count": self.corrections_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def _get_or_create(cls, id_document: str) -> "Response":
        instance = cls.query.filter_by(id_document=id_document).first()
        if instance is None:
            instance = cls(id_document=id_document, corrections_count=0)
            db.session.add(instance)
        return instance

    @classmethod
    def add_response(cls, id_document: str, entities: dict | None = None) -> dict:
        instance = cls.query.filter_by(id_document=id_document).first()
        if instance:
            if entities is not None:
                instance.entities = entities
        else:
            instance = cls(id_document=id_document, entities=entities)
            db.session.add(instance)

        db.session.commit()
        return instance.to_dict()

    @classmethod
    def update_response(cls, id_document: str, entities: dict | None) -> dict:
        instance = cls._get_or_create(id_document)
        instance.entities = entities
        db.session.commit()
        return instance.to_dict()

    @classmethod
    def increment_correction(cls, id_document: str, increment_by: int = 1) -> dict:
        instance = cls._get_or_create(id_document)
        instance.corrections_count = (instance.corrections_count or 0) + increment_by
        db.session.commit()
        return instance.to_dict()