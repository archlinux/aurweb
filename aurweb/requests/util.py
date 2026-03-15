from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select

from aurweb import db
from aurweb.models import PackageRequest


def get_pkgreq_by_id(id: int) -> PackageRequest:
    pkgreq = (
        db.get_session()
        .execute(select(PackageRequest).filter(PackageRequest.ID == id))
        .scalars()
        .first()
    )
    if not pkgreq:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return db.refresh(pkgreq)
