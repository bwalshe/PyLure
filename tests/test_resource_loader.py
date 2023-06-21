from pylure.resource import LureFileResourceLoader


def test_loader():
    with open("data/lure.dat", "rb") as data_file:
        loader = LureFileResourceLoader(data_file)
        assert len(loader) > 0
        assert len(loader.keys()) == len(loader)
        first_key = list(loader.keys())[0]
        assert first_key in loader.keys()
        assert -1 not in loader.keys()
        first_item = loader[first_key]
        assert first_item is not None
        assert len(first_item) > 0
        assert loader[-1] is None
