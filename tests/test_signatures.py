from almunqith.core.carve.signatures import REGISTRY, for_categories


def test_registry_has_m1_formats():
    names = {s.name for s in REGISTRY}
    assert {"jpeg", "png", "avi", "mp4"} <= names


def test_mp4_magic_offset_is_4():
    mp4 = next(s for s in REGISTRY if s.name == "mp4")
    assert mp4.magics == (b"ftyp",)
    assert mp4.magic_offset == 4


def test_for_categories_filters():
    photos = for_categories({"photos"})
    assert all(s.category == "photos" for s in photos)
    assert {s.name for s in photos} == {"jpeg", "png"}
    assert len(for_categories({"all"})) == len(REGISTRY)
