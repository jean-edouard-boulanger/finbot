from typing import Any

import pytest

from finbot.core.db.session import Session as DBSession
from finbot.core.kv_store import DBKVStore, KVEntity


class TestEntity(KVEntity):
    key = "test"

    def __init__(self, value: str):
        self.value = value

    def serialize(self) -> Any:
        return {"value": self.value}

    @staticmethod
    def deserialize(data: Any) -> "TestEntity":
        return TestEntity(data["value"])


@pytest.fixture(scope="function")
def kv_store(db_session: DBSession):
    return DBKVStore(db_session)


def test_init(db_session: DBSession):
    DBKVStore(db_session)


def test_contains_missing_kv(kv_store: DBKVStore):
    assert "missing_key" not in kv_store
    assert not kv_store.has_entity(TestEntity)


def test_get_missing_kv(kv_store: DBKVStore):
    with pytest.raises(KeyError):
        assert kv_store["missing_key"]
    assert kv_store.get("missing_key") is None
    assert kv_store.get("missing_key", "default") == "default"


def test_get_missing_entity(kv_store: DBKVStore):
    assert kv_store.get_entity(TestEntity) is None


def test_set_get_kv(kv_store: DBKVStore):
    assert "key" not in kv_store

    kv_store["key"] = "value"
    assert kv_store["key"] == "value"
    assert "key" in kv_store

    kv_store["key"] = "value1"
    assert kv_store["key"] == "value1"
    assert "key" in kv_store


def test_set_get_entity(kv_store: DBKVStore):
    kv_store.set_entity(TestEntity("hello"))
    assert kv_store.has_entity(TestEntity)
    entity = kv_store.get_entity(TestEntity)
    assert entity is not None
    assert entity.value == "hello"


def test_delete_kv(kv_store: DBKVStore):
    assert "key" not in kv_store
    kv_store["key"] = "value"
    assert "key" in kv_store
    del kv_store["key"]
    assert "key" not in kv_store


def test_delete_entity(kv_store: DBKVStore):
    assert not kv_store.has_entity(TestEntity)
    kv_store.set_entity(TestEntity("hello"))
    assert kv_store.has_entity(TestEntity)
    kv_store.delete_entity(TestEntity)
    assert not kv_store.has_entity(TestEntity)
