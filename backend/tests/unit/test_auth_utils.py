"""Tests for password hashing used by registration and login."""

from auth.auth_utils import get_password_hash, verify_password


def test_password_hash_round_trip():
    hashed = get_password_hash("correct-password")
    assert hashed != "correct-password"
    assert verify_password("correct-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hash_accepts_long_passwords():
    long_password = "a" * 200
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed)
