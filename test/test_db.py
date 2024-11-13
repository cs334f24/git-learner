import pytest

from db import DBManager


@pytest.fixture
def db() -> DBManager:
    return DBManager(":memory:")


def test_add_user(db: DBManager):
    pass


def test_create_session(db: DBManager):
    pass


def test_get_progress(db: DBManager):
    pass
