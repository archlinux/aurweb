import functools
from typing import Any, Callable

import fastapi


class AurwebException(Exception):
    pass


class MaintenanceException(AurwebException):
    pass


class BannedException(AurwebException):
    pass


class PermissionDeniedException(AurwebException):
    def __init__(self, user):
        msg = f"permission denied: {user:s}"
        super(PermissionDeniedException, self).__init__(msg)


class BrokenUpdateHookException(AurwebException):
    def __init__(self, cmd):
        msg = f"broken update hook: {cmd:s}"
        super(BrokenUpdateHookException, self).__init__(msg)


class InvalidUserException(AurwebException):
    def __init__(self, user):
        msg = f"unknown user: {user:s}"
        super(InvalidUserException, self).__init__(msg)


class InvalidPackageBaseException(AurwebException):
    def __init__(self, pkgbase):
        msg = f"package base not found: {pkgbase:s}"
        super(InvalidPackageBaseException, self).__init__(msg)


class InvalidRepositoryNameException(AurwebException):
    def __init__(self, pkgbase):
        msg = f"invalid repository name: {pkgbase:s}"
        super(InvalidRepositoryNameException, self).__init__(msg)


class PackageBaseExistsException(AurwebException):
    def __init__(self, pkgbase):
        msg = f"package base already exists: {pkgbase:s}"
        super(PackageBaseExistsException, self).__init__(msg)


class InvalidReasonException(AurwebException):
    def __init__(self, reason):
        msg = f"invalid reason: {reason:s}"
        super(InvalidReasonException, self).__init__(msg)


class InvalidCommentException(AurwebException):
    def __init__(self, comment):
        msg = f"comment is too short: {comment:s}"
        super(InvalidCommentException, self).__init__(msg)


class AlreadyVotedException(AurwebException):
    def __init__(self, comment):
        msg = f"already voted for package base: {comment:s}"
        super(AlreadyVotedException, self).__init__(msg)


class NotVotedException(AurwebException):
    def __init__(self, comment):
        msg = f"missing vote for package base: {comment:s}"
        super(NotVotedException, self).__init__(msg)


class InvalidArgumentsException(AurwebException):
    def __init__(self, msg):
        super(InvalidArgumentsException, self).__init__(msg)


class RPCError(AurwebException):
    pass


class ValidationError(AurwebException):
    def __init__(self, data: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data


class InvariantError(AurwebException):
    pass


def handle_form_exceptions(route: Callable) -> fastapi.Response:
    """
    A decorator required when fastapi POST routes are defined.

    This decorator populates fastapi's `request.state` with a `form_data`
    attribute, which is then used to report form data when exceptions
    are caught and reported.
    """

    @functools.wraps(route)
    async def wrapper(request: fastapi.Request, *args, **kwargs):
        request.state.form_data = await request.form()
        return await route(request, *args, **kwargs)

    return wrapper
