"""Tests for database URL handling (Neon, Railway, local)."""

from db import resolve_database_uri


def test_rewrites_postgres_scheme():
    uri = resolve_database_uri("postgres://user:pass@host/db")
    assert uri.startswith("postgresql://")


def test_adds_ssl_for_neon():
    uri = resolve_database_uri(
        "postgresql://user:pass@ep-example.eu-west-2.aws.neon.tech/neondb"
    )
    assert "sslmode=require" in uri


def test_does_not_duplicate_sslmode():
    raw = (
        "postgresql://user:pass@ep-example.eu-west-2.aws.neon.tech/neondb"
        "?sslmode=require"
    )
    uri = resolve_database_uri(raw)
    assert uri.count("sslmode=") == 1
