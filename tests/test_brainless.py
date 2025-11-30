import sys

def test_always_passes():
    assert True


def test_basic_math():
    four = 4
    assert 2 + 2 == four


def test_string():
    name = "GitHub Actions"
    name_len = 14
    assert "Actions" in name
    assert len(name) == name_len


def test_python_version():
    assert sys.version_info >= (3, 9)