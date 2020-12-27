from aurweb.exceptions import (AlreadyVotedException, AurwebException, BannedException, BrokenUpdateHookException,
                               InvalidArgumentsException, InvalidCommentException, InvalidPackageBaseException,
                               InvalidReasonException, InvalidRepositoryNameException, InvalidUserException,
                               MaintenanceException, NotVotedException, PackageBaseExistsException, PermissionDeniedException)


def test_aurweb_exception():
    try:
        raise AurwebException("test")
    except AurwebException as exc:
        assert str(exc) == "test"


def test_maintenance_exception():
    try:
        raise MaintenanceException("test")
    except MaintenanceException as exc:
        assert str(exc) == "test"


def test_banned_exception():
    try:
        raise BannedException("test")
    except BannedException as exc:
        assert str(exc) == "test"


def test_already_voted_exception():
    try:
        raise AlreadyVotedException("test")
    except AlreadyVotedException as exc:
        assert str(exc) == "already voted for package base: test"


def test_broken_update_hook_exception():
    try:
        raise BrokenUpdateHookException("test")
    except BrokenUpdateHookException as exc:
        assert str(exc) == "broken update hook: test"


def test_invalid_arguments_exception():
    try:
        raise InvalidArgumentsException("test")
    except InvalidArgumentsException as exc:
        assert str(exc) == "test"


def test_invalid_packagebase_exception():
    try:
        raise InvalidPackageBaseException("test")
    except InvalidPackageBaseException as exc:
        assert str(exc) == "package base not found: test"


def test_invalid_comment_exception():
    try:
        raise InvalidCommentException("test")
    except InvalidCommentException as exc:
        assert str(exc) == "comment is too short: test"


def test_invalid_reason_exception():
    try:
        raise InvalidReasonException("test")
    except InvalidReasonException as exc:
        assert str(exc) == "invalid reason: test"


def test_invalid_user_exception():
    try:
        raise InvalidUserException("test")
    except InvalidUserException as exc:
        assert str(exc) == "unknown user: test"


def test_not_voted_exception():
    try:
        raise NotVotedException("test")
    except NotVotedException as exc:
        assert str(exc) == "missing vote for package base: test"


def test_packagebase_exists_exception():
    try:
        raise PackageBaseExistsException("test")
    except PackageBaseExistsException as exc:
        assert str(exc) == "package base already exists: test"


def test_permission_denied_exception():
    try:
        raise PermissionDeniedException("test")
    except PermissionDeniedException as exc:
        assert str(exc) == "permission denied: test"


def test_repository_name_exception():
    try:
        raise InvalidRepositoryNameException("test")
    except InvalidRepositoryNameException as exc:
        assert str(exc) == "invalid repository name: test"
