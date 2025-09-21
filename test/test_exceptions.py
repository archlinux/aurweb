from aurweb import exceptions


def test_aurweb_exception() -> None:
    try:
        raise exceptions.AurwebException("test")
    except exceptions.AurwebException as exc:
        assert str(exc) == "test"


def test_maintenance_exception() -> None:
    try:
        raise exceptions.MaintenanceException("test")
    except exceptions.MaintenanceException as exc:
        assert str(exc) == "test"


def test_banned_exception() -> None:
    try:
        raise exceptions.BannedException("test")
    except exceptions.BannedException as exc:
        assert str(exc) == "test"


def test_already_voted_exception() -> None:
    try:
        raise exceptions.AlreadyVotedException("test")
    except exceptions.AlreadyVotedException as exc:
        assert str(exc) == "already voted for package base: test"


def test_broken_update_hook_exception() -> None:
    try:
        raise exceptions.BrokenUpdateHookException("test")
    except exceptions.BrokenUpdateHookException as exc:
        assert str(exc) == "broken update hook: test"


def test_invalid_arguments_exception() -> None:
    try:
        raise exceptions.InvalidArgumentsException("test")
    except exceptions.InvalidArgumentsException as exc:
        assert str(exc) == "test"


def test_invalid_packagebase_exception() -> None:
    try:
        raise exceptions.InvalidPackageBaseException("test")
    except exceptions.InvalidPackageBaseException as exc:
        assert str(exc) == "package base not found: test"


def test_invalid_comment_exception() -> None:
    try:
        raise exceptions.InvalidCommentException("test")
    except exceptions.InvalidCommentException as exc:
        assert str(exc) == "comment is too short: test"


def test_invalid_reason_exception() -> None:
    try:
        raise exceptions.InvalidReasonException("test")
    except exceptions.InvalidReasonException as exc:
        assert str(exc) == "invalid reason: test"


def test_invalid_user_exception() -> None:
    try:
        raise exceptions.InvalidUserException("test")
    except exceptions.InvalidUserException as exc:
        assert str(exc) == "unknown user: test"


def test_not_voted_exception() -> None:
    try:
        raise exceptions.NotVotedException("test")
    except exceptions.NotVotedException as exc:
        assert str(exc) == "missing vote for package base: test"


def test_packagebase_exists_exception() -> None:
    try:
        raise exceptions.PackageBaseExistsException("test")
    except exceptions.PackageBaseExistsException as exc:
        assert str(exc) == "package base already exists: test"


def test_permission_denied_exception() -> None:
    try:
        raise exceptions.PermissionDeniedException("test")
    except exceptions.PermissionDeniedException as exc:
        assert str(exc) == "permission denied: test"


def test_repository_name_exception() -> None:
    try:
        raise exceptions.InvalidRepositoryNameException("test")
    except exceptions.InvalidRepositoryNameException as exc:
        assert str(exc) == "invalid repository name: test"


def test_invariant_error() -> None:
    try:
        raise exceptions.InvariantError("test")
    except exceptions.InvariantError as exc:
        assert str(exc) == "test"
