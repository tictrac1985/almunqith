from almunqith.core.carve.signatures import REGISTRY, for_categories


def test_registry_has_m1_formats():
    names = {s.name for s in REGISTRY}
    assert {"jpeg", "png", "avi", "mp4"} <= names


def test_registry_has_25_plus_formats():
    assert len(REGISTRY) >= 20
    cats = {s.category for s in REGISTRY}
    assert {"photos", "videos", "audio", "documents", "archives"} <= cats


def test_every_signature_is_callable_and_distinct():
    names = [s.name for s in REGISTRY]
    assert len(names) == len(set(names))
    for s in REGISTRY:
        assert callable(s.validate)
        assert s.magic_offset >= 0


def test_mp4_magic_offset_is_4():
    mp4 = next(s for s in REGISTRY if s.name == "mp4")
    assert mp4.magics == (b"ftyp",)
    assert mp4.magic_offset == 4


def test_for_categories_filters():
    photos = for_categories({"photos"})
    assert all(s.category == "photos" for s in photos)
    assert {"jpeg", "png"} <= {s.name for s in photos}
    assert len(for_categories({"all"})) == len(REGISTRY)
