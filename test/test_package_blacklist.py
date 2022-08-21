import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.package_blacklist import PackageBlacklist


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_package_blacklist_creation():
    with db.begin():
        package_blacklist = db.create(PackageBlacklist, Name="evil-package")
    assert bool(package_blacklist.ID)
    assert package_blacklist.Name == "evil-package"


def test_package_blacklist_null_name_raises_exception():
    with pytest.raises(IntegrityError):
        PackageBlacklist()
