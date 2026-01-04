"""Test auth security functions."""


from src.auth.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestAuthSecurity:
    """Test authentication security functions."""

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        plain_password = "SecurePass123!"
        hashed = get_password_hash(plain_password)

        assert verify_password(plain_password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        plain_password = "SecurePass123!"
        wrong_password = "WrongPass!"

        hashed = get_password_hash(plain_password)

        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Test decoding valid JWT token."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["email"] == "test@example.com"

    def test_decode_access_token_invalid(self):
        """Test decoding invalid JWT token."""
        invalid_token = "invalid.token.string"

        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_password_hash_is_different_each_time(self):
        """Test that password hash is different each time."""
        password = "SecurePass123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
