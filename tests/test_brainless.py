def test_always_passes():
    """Самый простой тест в мире — всегда проходит"""
    assert True


def test_basic_math():
    """Проверим, что 2 + 2 = 4 (если это сломается — мир кончился)"""
    assert 2 + 2 == 4


def test_string():
    name = "GitHub Actions"
    assert "Actions" in name
    assert len(name) == 14


# Бонус: проверим, что Python версия правильная (полезно в матрице)
import sys

def test_python_version():
    assert sys.version_info >= (3, 9)