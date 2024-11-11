import pytest

from db import DBMan


@pytest.fixture
def db() -> DBMan:
    return DBMan(":memory:")


def test_add_user(db: DBMan):
    pass


def test_create_session(db: DBMan):
    pass


def test_get_progress(db: DBMan):
    pass
