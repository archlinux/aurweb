from sqlalchemy import and_, case, or_, orm

from aurweb import config, db
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comaintainer import PackageComaintainer
from aurweb.models.package_keyword import PackageKeyword
from aurweb.models.package_notification import PackageNotification
from aurweb.models.package_vote import PackageVote
from aurweb.models.user import User

DEFAULT_MAX_RESULTS = 2500


class PackageSearch:
    """ A Package search query builder. """

    # A constant mapping of short to full name sort orderings.
    FULL_SORT_ORDER = {"d": "desc", "a": "asc"}

    def __init__(self, user: User):
        """ Construct an instance of PackageSearch.

        This constructors performs several steps during initialization:
            1. Setup self.query: an ORM query of Package joined by PackageBase.
        """
        self.user = user
        self.query = db.query(Package).join(PackageBase).join(
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

    def _search_by_namedesc(self, keywords: str) -> orm.Query:
        self.query = self.query.filter(
            or_(Package.Name.like(f"%{keywords}%"),
                Package.Description.like(f"%{keywords}%"))
        )
        return self

    def _search_by_name(self, keywords: str) -> orm.Query:
        self.query = self.query.filter(Package.Name.like(f"%{keywords}%"))
        return self

    def _search_by_exact_name(self, keywords: str) -> orm.Query:
        self.query = self.query.filter(Package.Name == keywords)
        return self

    def _search_by_pkgbase(self, keywords: str) -> orm.Query:
        self.query = self.query.filter(PackageBase.Name.like(f"%{keywords}%"))
        return self

    def _search_by_exact_pkgbase(self, keywords: str) -> orm.Query:
        self.query = self.query.filter(PackageBase.Name == keywords)
        return self

    def _search_by_keywords(self, keywords: str) -> orm.Query:
        self.query = self.query.join(PackageKeyword).filter(
            PackageKeyword.Keyword == keywords
        )
        return self

    def _search_by_maintainer(self, keywords: str) -> orm.Query:
        self.query = self.query.join(
            User, User.ID == PackageBase.MaintainerUID
        ).filter(User.Username == keywords)
        return self

    def _search_by_comaintainer(self, keywords: str) -> orm.Query:
        self.query = self.query.join(PackageComaintainer).join(
            User, User.ID == PackageComaintainer.UsersID
        ).filter(User.Username == keywords)
        return self

    def _search_by_co_or_maintainer(self, keywords: str) -> orm.Query:
        self.query = self.query.join(
            PackageComaintainer,
            isouter=True
        ).join(
            User, or_(User.ID == PackageBase.MaintainerUID,
                      User.ID == PackageComaintainer.UsersID)
        ).filter(User.Username == keywords)
        return self

    def _search_by_submitter(self, keywords: str) -> orm.Query:
        self.query = self.query.join(
            User, User.ID == PackageBase.SubmitterUID
        ).filter(User.Username == keywords)
        return self

    def search_by(self, search_by: str, keywords: str) -> orm.Query:
        if search_by not in self.search_by_cb:
            search_by = "nd"  # Default: Name, Description
        callback = self.search_by_cb.get(search_by)
        result = callback(keywords)
        return result

    def _sort_by_name(self, order: str):
        column = getattr(Package.Name, order)
        self.query = self.query.order_by(column())
        return self

    def _sort_by_votes(self, order: str):
        column = getattr(PackageBase.NumVotes, order)
        self.query = self.query.order_by(column())
        return self

    def _sort_by_popularity(self, order: str):
        column = getattr(PackageBase.Popularity, order)
        self.query = self.query.order_by(column())
        return self

    def _sort_by_voted(self, order: str):
        # FIXME: Currently, PHP is destroying this implementation
        # in terms of performance. We should improve this; there's no
        # reason it should take _longer_.
        column = getattr(
            case([(PackageVote.UsersID == self.user.ID, 1)], else_=0),
            order
        )
        self.query = self.query.order_by(column(), Package.Name.desc())
        return self

    def _sort_by_notify(self, order: str):
        # FIXME: Currently, PHP is destroying this implementation
        # in terms of performance. We should improve this; there's no
        # reason it should take _longer_.
        column = getattr(
            case([(PackageNotification.UserID == self.user.ID, 1)], else_=0),
            order
        )
        self.query = self.query.order_by(column(), Package.Name.desc())
        return self

    def _sort_by_maintainer(self, order: str):
        column = getattr(User.Username, order)
        self.query = self.query.join(
            User, User.ID == PackageBase.MaintainerUID, isouter=True
        ).order_by(column())
        return self

    def _sort_by_last_modified(self, order: str):
        column = getattr(PackageBase.ModifiedTS, order)
        self.query = self.query.order_by(column())
        return self

    def sort_by(self, sort_by: str, ordering: str = "d") -> orm.Query:
        if sort_by not in self.sort_by_cb:
            sort_by = "n"  # Default: Name.
        callback = self.sort_by_cb.get(sort_by)
        if ordering not in self.FULL_SORT_ORDER:
            ordering = "d"  # Default: Descending.
        ordering = self.FULL_SORT_ORDER.get(ordering)
        return callback(ordering)

    def results(self) -> orm.Query:
        # Store the total count of all records found up to limit.
        limit = (config.getint("options", "max_search_results")
                 or DEFAULT_MAX_RESULTS)
        self.total_count = self.query.limit(limit).count()

        # Return the query to the user.
        return self.query
