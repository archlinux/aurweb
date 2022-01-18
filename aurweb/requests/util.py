from http import HTTPStatus

from fastapi import HTTPException

from aurweb import db
from aurweb.models import PackageRequest


def get_pkgreq_by_id(id: int) -> PackageRequest:
    pkgreq = db.query(PackageRequest).filter(PackageRequest.ID == id).first()
    if not pkgreq:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return db.refresh(pkgreq)
