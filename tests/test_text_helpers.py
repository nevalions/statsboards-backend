import pytest

from src.helpers.text_helpers import convert_cyrillic_filename


class TestConvertCyrillicFilename:
    """Test suite for converting Cyrillic filenames to Latin alphabet."""

    def test_convert_simple_cyrillic_filename(self):
        """Test converting a simple Cyrillic filename."""
        original = "команда.jpg"
        result = convert_cyrillic_filename(original)
        assert result == "komanda.jpg"
        assert result != original

    def test_convert_cyrillic_filename_with_spaces(self):
        """Test converting Cyrillic filename with spaces."""
        original = "Турнир 2023.png"
        result = convert_cyrillic_filename(original)
        assert result == "Turnir_2023.png"
        assert " " not in result

    def test_convert_cyrillic_filename_with_multiple_words(self):
        """Test converting Cyrillic filename with multiple words."""
        original = "Фото команды.jpeg"
        result = convert_cyrillic_filename(original)
        assert result == "Foto_komandy.jpeg"
        assert "_" in result

    def test_convert_cyrillic_filename_with_underscore(self):
        """Test converting Cyrillic filename with underscore."""
        original = "Тестовый_файл.txt"
        result = convert_cyrillic_filename(original)
        assert result == "Testovyy_fayl.txt"
        assert "_" in result

    def test_convert_filename_without_extension(self):
        """Test converting filename without extension."""
        original = "Безрасширения"
        result = convert_cyrillic_filename(original)
        assert result == "Bezrasshireniya"
        assert "." not in result

    def test_convert_mixed_cyrillic_latin_filename(self):
        """Test converting filename with mixed Cyrillic and Latin characters."""
        original = "Team_команда_2024.jpg"
        result = convert_cyrillic_filename(original)
        assert "Team" in result
        assert "komanda" in result
        assert "2024" in result
        assert result.endswith(".jpg")

    def test_convert_empty_filename(self):
        """Test converting empty filename."""
        original = ""
        result = convert_cyrillic_filename(original)
        assert result == ""

    def test_convert_latin_only_filename(self):
        """Test converting Latin-only filename (should remain unchanged)."""
        original = "team_photo.jpg"
        result = convert_cyrillic_filename(original)
        assert result == original

    def test_convert_filename_with_special_chars(self):
        """Test converting filename with special characters."""
        original = "Фото-команды.png"
        result = convert_cyrillic_filename(original)
        assert "Foto" in result
        assert "komandy" in result
        assert "-" in result
        assert result.endswith(".png")

    def test_convert_uppercase_cyrillic(self):
        """Test converting uppercase Cyrillic characters."""
        original = "КОМАНДА.JPG"
        result = convert_cyrillic_filename(original)
        assert result == "KOMANDA.JPG"
        assert result != original

    def test_convert_mixed_case_cyrillic(self):
        """Test converting mixed case Cyrillic characters."""
        original = "Команда.команды.jpg"
        result = convert_cyrillic_filename(original)
        assert "Komanda" in result
        assert "komandy" in result
        assert result.endswith(".jpg")

    def test_convert_filename_with_numbers(self):
        """Test converting filename with numbers."""
        original = "Фото2024.jpg"
        result = convert_cyrillic_filename(original)
        assert "Foto2024" in result
        assert result.endswith(".jpg")

    def test_convert_filename_with_yo_character(self):
        """Test converting filename with ё/Ё characters."""
        original = "ёжик.png"
        result = convert_cyrillic_filename(original)
        assert "yozhik" in result
        assert result.endswith(".png")

    def test_convert_filename_with_hard_soft_signs(self):
        """Test converting filename with ъ/ь characters."""
        original = "подъезд_пять.txt"
        result = convert_cyrillic_filename(original)
        assert "podezd" in result
        assert "pyat" in result
        assert result.endswith(".txt")

    def test_convert_filename_with_special_letters(self):
        """Test converting filename with special Cyrillic letters."""
        original = "щука_чашка.jpg"
        result = convert_cyrillic_filename(original)
        assert "schuka" in result
        assert "chashka" in result
        assert result.endswith(".jpg")

    def test_convert_filename_preserves_extension(self):
        """Test that file extension is preserved."""
        test_cases = [
            ("файл.jpg", "fayl.jpg"),
            ("файл.png", "fayl.png"),
            ("файл.jpeg", "fayl.jpeg"),
            ("файl.gif", "fayl.gif"),
            ("файл.pdf", "fayl.pdf"),
            ("файl.txt", "fayl.txt"),
        ]

        for original, expected in test_cases:
            result = convert_cyrillic_filename(original)
            assert (
                result == expected
            ), f"Expected {expected} for {original}, got {result}"

    def test_convert_filename_multiple_extensions(self):
        """Test converting filename with multiple dots."""
        original = "файл.tar.gz"
        result = convert_cyrillic_filename(original)
        assert "fayl.tar.gz" == result

    def test_convert_filename_leading_trailing_spaces(self):
        """Test converting filename with leading/trailing spaces."""
        original = "  файл  "
        result = convert_cyrillic_filename(original)
        assert "fayl" == result
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_convert_filename_multiple_consecutive_spaces(self):
        """Test converting filename with multiple consecutive spaces."""
        original = "файл   с   пробелами.txt"
        result = convert_cyrillic_filename(original)
        assert "fayl_s_probelami.txt" == result

    def test_convert_all_cyrillic_chars(self):
        """Test converting a filename with all Cyrillic characters."""
        original = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        result = convert_cyrillic_filename(original)
        assert "ABVGDEYoZhZIYKLMNOPRSTUFHTsChShSchYEYuYa" == result

    def test_convert_lowercase_all_cyrillic_chars(self):
        """Test converting a filename with all lowercase Cyrillic characters."""
        original = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        result = convert_cyrillic_filename(original)
        assert "abvgdeyozhziyklmnoprstufhtschshschyeyuya" == result
