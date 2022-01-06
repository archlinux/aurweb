from sqlalchemy import and_, case, or_, orm

from aurweb import db, models, util
from aurweb.models import Package, PackageBase, User
from aurweb.models.dependency_type import CHECKDEPENDS_ID, DEPENDS_ID, MAKEDEPENDS_ID, OPTDEPENDS_ID
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_vote import PackageVote


class PackageSearch:
    """ A Package search query builder. """

    # A constant mapping of short to full name sort orderings.
    FULL_SORT_ORDER = {"d": "desc", "a": "asc"}

    def __init__(self, user: models.User = None):
        self.query = db.query(Package).join(PackageBase)

        self.user = user
        if self.user:
            self.query = self.query.join(
                PackageVote,
                and_(PackageVote.PackageBaseID == PackageBase.ID,
                     PackageVote.UsersID == self.user.ID),
                isouter=True
            ).join(
                PackageNotification,
                and_(PackageNotification.PackageBaseID == PackageBase.ID,
                     PackageNotification.UserID == self.user.ID),
                isouter=True
            )

        self.ordering = "d"

        # Setup SeB (Search By) callbacks.
        self.search_by_cb = {
            "nd": self._search_by_namedesc,
            "n": self._search_by_name,
            "b": self._search_by_pkgbase,
            "N": self._search_by_exact_name,
            "B": self._search_by_exact_pkgbase,
            "k": self._search_by_keywords,
            "m": self._search_by_maintainer,
            "c": self._search_by_comaintainer,
            "M": self._search_by_co_or_maintainer,
            "s": self._search_by_submitter
        }

        # Setup SB (Sort By) callbacks.
        self.sort_by_cb = {
            "n": self._sort_by_name,
            "v": self._sort_by_votes,
            "p": self._sort_by_popularity,
            "w": self._sort_by_voted,
            "o": self._sort_by_notify,
            "m": self._sort_by_maintainer,
            "l": self._sort_by_last_modified
        }

        self._joined = False

    def _join_user(self, outer: bool = True) -> orm.Query:
        """ Centralized joining of a package base's maintainer. """
        if not self._joined:
            self.query = self.query.join(
                User,
                User.ID == PackageBase.MaintainerUID,
                isouter=outer
            )
            self._joined = True
            return self.query

    def _search_by_namedesc(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.filter(
            or_(Package.Name.like(f"%{keywords}%"),
                Package.Description.like(f"%{keywords}%"))
        )
        return self

    def _search_by_name(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.filter(Package.Name.like(f"%{keywords}%"))
        return self

    def _search_by_exact_name(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.filter(Package.Name == keywords)
        return self

    def _search_by_pkgbase(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.filter(PackageBase.Name.like(f"%{keywords}%"))
        return self

    def _search_by_exact_pkgbase(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.filter(PackageBase.Name == keywords)
        return self

    def _search_by_keywords(self, keywords: str) -> orm.Query:
        self._join_user()
        self.query = self.query.join(PackageKeyword).filter(
            PackageKeyword.Keyword == keywords
        )
        return self

    def _search_by_maintainer(self, keywords: str) -> orm.Query:
        self._join_user()
        if keywords:
            self.query = self.query.filter(
                and_(User.Username == keywords,
                     User.ID == PackageBase.MaintainerUID)
            )
        else:
            self.query = self.query.filter(PackageBase.MaintainerUID.is_(None))
        return self

    def _search_by_comaintainer(self, keywords: str) -> orm.Query:
        self._join_user()
        exists_subq = db.query(PackageComaintainer).join(User).filter(
            and_(PackageComaintainer.PackageBaseID == PackageBase.ID,
                 User.Username == keywords)
        ).exists()
        self.query = self.query.filter(db.query(exists_subq).scalar_subquery())
        return self

    def _search_by_co_or_maintainer(self, keywords: str) -> orm.Query:
        self._join_user()
        exists_subq = db.query(PackageComaintainer).join(User).filter(
            and_(PackageComaintainer.PackageBaseID == PackageBase.ID,
                 User.Username == keywords)
        ).exists()
        self.query = self.query.filter(
            or_(and_(User.Username == keywords,
                     User.ID == PackageBase.MaintainerUID),
                db.query(exists_subq).scalar_subquery())
        )
        return self

    def _search_by_submitter(self, keywords: str) -> orm.Query:
        self._join_user()

        uid = 0
        user = db.query(User).filter(User.Username == keywords).first()
        if user:
            uid = user.ID

        self.query = self.query.filter(PackageBase.SubmitterUID == uid)
        return self

    def search_by(self, search_by: str, keywords: str) -> orm.Query:
        if search_by not in self.search_by_cb:
            search_by = "nd"  # Default: Name, Description
        callback = self.search_by_cb.get(search_by)
        result = callback(keywords)
        return result

    def _sort_by_name(self, order: str):
        column = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column())
        return self

    def _sort_by_votes(self, order: str):
        column = getattr(models.PackageBase.NumVotes, order)
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def _sort_by_popularity(self, order: str):
        column = getattr(models.PackageBase.Popularity, order)
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def _sort_by_voted(self, order: str):
        # FIXME: Currently, PHP is destroying this implementation
        # in terms of performance. We should improve this; there's no
        # reason it should take _longer_.
        column = getattr(
            case([(models.PackageVote.UsersID == self.user.ID, 1)], else_=0),
            order
        )
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def _sort_by_notify(self, order: str):
        # FIXME: Currently, PHP is destroying this implementation
        # in terms of performance. We should improve this; there's no
        # reason it should take _longer_.
        column = getattr(
            case([(models.PackageNotification.UserID == self.user.ID, 1)],
                 else_=0),
            order
        )
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def _sort_by_maintainer(self, order: str):
        column = getattr(models.User.Username, order)
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def _sort_by_last_modified(self, order: str):
        column = getattr(models.PackageBase.ModifiedTS, order)
        name = getattr(models.Package.Name, order)
        self.query = self.query.order_by(column(), name())
        return self

    def sort_by(self, sort_by: str, ordering: str = "d") -> orm.Query:
        if sort_by not in self.sort_by_cb:
            sort_by = "p"  # Default: Popularity
        callback = self.sort_by_cb.get(sort_by)
        if ordering not in self.FULL_SORT_ORDER:
            ordering = "d"  # Default: Descending
        ordering = self.FULL_SORT_ORDER.get(ordering)
        return callback(ordering)

    def count(self, limit: int) -> int:
        """
        Return internal query's count up to `limit`.

        :param limit: Upper bound
        :return: Database count up to `limit`
        """
        return self.query.limit(limit).count()

    def results(self) -> orm.Query:
        """ Return internal query. """
        return self.query


class RPCSearch(PackageSearch):
    """ A PackageSearch-derived RPC package search query builder.

    With RPC search, we need a subset of PackageSearch's handlers,
    with a few additional handlers added. So, within the RPCSearch
    constructor, we pop unneeded keys out of inherited self.search_by_cb
    and add a few more keys to it, namely: depends, makedepends,
    optdepends and checkdepends.

    Additionally, some logic within the inherited PackageSearch.search_by
    method is not needed, so it is overridden in this class without
    sanitization done for the PackageSearch `by` argument.
    """

    keys_removed = ("b", "N", "B", "k", "c", "M", "s")

    def __init__(self) -> "RPCSearch":
        super().__init__()

        # Fix-up inherited search_by_cb to reflect RPC-specific by params.
        # We keep: "nd", "n" and "m". We also overlay four new by params
        # on top: "depends", "makedepends", "optdepends" and "checkdepends".
        util.apply_all(RPCSearch.keys_removed,
                       lambda k: self.search_by_cb.pop(k))
        self.search_by_cb.update({
            "depends": self._search_by_depends,
            "makedepends": self._search_by_makedepends,
            "optdepends": self._search_by_optdepends,
            "checkdepends": self._search_by_checkdepends
        })

    def _join_depends(self, dep_type_id: int) -> orm.Query:
        """ Join Package with PackageDependency and filter results
        based on `dep_type_id`.

        :param dep_type_id: DependencyType ID
        :returns: PackageDependency-joined orm.Query
        """
        self.query = self.query.join(models.PackageDependency).filter(
            models.PackageDependency.DepTypeID == dep_type_id)
        return self.query

    def _search_by_depends(self, keywords: str) -> "RPCSearch":
        self.query = self._join_depends(DEPENDS_ID).filter(
            models.PackageDependency.DepName == keywords)
        return self

    def _search_by_makedepends(self, keywords: str) -> "RPCSearch":
        self.query = self._join_depends(MAKEDEPENDS_ID).filter(
            models.PackageDependency.DepName == keywords)
        return self

    def _search_by_optdepends(self, keywords: str) -> "RPCSearch":
        self.query = self._join_depends(OPTDEPENDS_ID).filter(
            models.PackageDependency.DepName == keywords)
        return self

    def _search_by_checkdepends(self, keywords: str) -> "RPCSearch":
        self.query = self._join_depends(CHECKDEPENDS_ID).filter(
            models.PackageDependency.DepName == keywords)
        return self

    def search_by(self, by: str, keywords: str) -> "RPCSearch":
        """ Override inherited search_by. In this override, we reduce the
        scope of what we handle within this function. We do not set `by`
        to a default of "nd" in the RPC, as the RPC returns an error when
        incorrect `by` fields are specified.

        :param by: RPC `by` argument
        :param keywords: RPC `arg` argument
        :returns: self
        """
        callback = self.search_by_cb.get(by)
        result = callback(keywords)
        return result

    def results(self) -> orm.Query:
        return self.query.filter(models.PackageBase.PackagerUID.isnot(None))
