from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import func

from aurweb import db
from aurweb.models import User


def get_user_by_name(username: str) -> User:
    """
    Query a user by its username.

    :param username: User.Username
    :return: User instance
    """
    user = db.query(User).filter(func.lower(User.Username) == username.lower()).first()
    if not user:
        raise HTTPException(status_code=int(HTTPStatus.NOT_FOUND))
    return db.refresh(user)
