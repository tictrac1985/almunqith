from almunqith.ui import i18n


def test_arabic_default_and_lookup():
    i18n.set_language("ar")
    assert i18n.tr("app_title") == "المنقذ"
    assert i18n.is_rtl() is True


def test_english_and_formatting():
    i18n.set_language("en")
    assert i18n.tr("app_title") == "AlMunqith"
    assert i18n.is_rtl() is False
    assert i18n.tr("found_files", n=7) == "Found 7 files"


def test_missing_key_falls_back():
    i18n.set_language("ar")
    assert i18n.tr("no_such_key_xyz") == "no_such_key_xyz"
