import pytest

from pylure.resource import (
    LureFileResourceLoader,
    find_language_offset,
    LureGameResourceManager,
    file_for_id,
    LURE_FILES
)


def test_lure_file_resource_loader(pytestconfig):
    with (pytestconfig.rootpath / "data" / "lure.dat").open("rb") as data_file:
        offset = find_language_offset(data_file)
        header = LureFileResourceLoader(data_file, 0, offset)
        assert len(header) > 0
        assert len(header.keys()) == len(header)
        first_key = list(header.keys())[0]
        assert first_key in header.keys()
        assert -1 not in header.keys()
        assert header[first_key] is not None
        assert len(header[first_key]) > 0
        with pytest.raises(KeyError):
            _ = header[-1]


def test_lure_game_resource_manager(pytestconfig):
    with LureGameResourceManager(pytestconfig.rootpath / "data") as manager:
        keys = list(manager.keys())
        assert len(keys) > 100
        assert len(keys) == len(set(keys))
        assert len(manager[keys[0]]) > 0
        assert len(manager[keys[-1]]) > 0
        assert set(file_for_id(k) for k in keys) == set(LURE_FILES)
