import pytest

from aurweb.scripts import popupdate


@pytest.fixture(autouse=True)
def setup(db_test):
    return


def test_popupdate():
    popupdate.main()
