class AurwebException(Exception):
    pass


class MaintenanceException(AurwebException):
    pass


class BannedException(AurwebException):
    pass


class PermissionDeniedException(AurwebException):
    def __init__(self, user):
        msg = 'permission denied: {:s}'.format(user)
        super(PermissionDeniedException, self).__init__(msg)


class InvalidUserException(AurwebException):
    def __init__(self, user):
        msg = 'unknown user: {:s}'.format(user)
        super(InvalidUserException, self).__init__(msg)


class InvalidPackageBaseException(AurwebException):
    def __init__(self, pkgbase):
        msg = 'package base not found: {:s}'.format(pkgbase)
        super(InvalidPackageBaseException, self).__init__(msg)


class InvalidRepositoryNameException(AurwebException):
    def __init__(self, pkgbase):
        msg = 'invalid repository name: {:s}'.format(pkgbase)
        super(InvalidRepositoryNameException, self).__init__(msg)


class PackageBaseExistsException(AurwebException):
    def __init__(self, pkgbase):
        msg = 'package base already exists: {:s}'.format(pkgbase)
        super(PackageBaseExistsException, self).__init__(msg)


class InvalidReasonException(AurwebException):
    def __init__(self, reason):
        msg = 'invalid reason: {:s}'.format(reason)
        super(InvalidReasonException, self).__init__(msg)


class InvalidCommentException(AurwebException):
    def __init__(self, comment):
        msg = 'comment is too short: {:s}'.format(comment)
        super(InvalidCommentException, self).__init__(msg)


class AlreadyVotedException(AurwebException):
    def __init__(self, comment):
        msg = 'already voted for package base: {:s}'.format(comment)
        super(AlreadyVotedException, self).__init__(msg)


class NotVotedException(AurwebException):
    def __init__(self, comment):
        msg = 'missing vote for package base: {:s}'.format(comment)
        super(NotVotedException, self).__init__(msg)


class InvalidArgumentsException(AurwebException):
    def __init__(self, msg):
        super(InvalidArgumentsException, self).__init__(msg)
