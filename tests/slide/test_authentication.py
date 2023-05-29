"""Unittests for authentication methods."""
from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
from slide import (
    DigestAuthenticationHeader,
    RequestTypes,
    calculate_digest_key,
    parse_response_header,
)


@pytest.mark.parametrize(
    "header_data, cnonce_count, expected_result",
    [
        (
            'nonce="1234567890", realm="example.com", qop="auth"',
            5,
            DigestAuthenticationHeader(
                nonce="1234567890",
                realm="example.com",
                qop="auth",
                nc="00000001",
                cnonce_count=5,
            ),
        ),
        (
            'nonce="abcdefg", realm="test", qop="auth"',
            2,
            DigestAuthenticationHeader(
                nonce="abcdefg",
                realm="test",
                qop="auth",
                nc="00000001",
                cnonce_count=2,
            ),
        ),
    ],
)
def test_parse_response_header(
    header_data: str, cnonce_count: int, expected_result: DigestAuthenticationHeader
):
    """Test parsing of response header."""
    result = parse_response_header(header_data, cnonce_count)
    assert result == expected_result


# pylint: disable=too-many-arguments,line-too-long
@patch("slide.authentication.hashlib")
@patch("slide.authentication.time")
@pytest.mark.parametrize(
    "username, password, uri, request_type, digest_info, expected_result",
    [
        (
            "john",
            "password123",
            "/api/resource",
            RequestTypes.GET,
            DigestAuthenticationHeader(
                nonce="1234567890",
                realm="example.com",
                qop="anything",
                nc="00000001",
                cnonce_count=5,
                algorithm="MD5",
            ),
            (
                'Digest username="john", realm="example.com", nonce="1234567890", '
                'uri="/api/resource", algorithm="MD5", qop=anything, nc=00000001, '
                'cnonce="cnonce12", response="hash123"'
            ),
        ),
        (
            "jane",
            "password456",
            "/api/endpoint",
            RequestTypes.GET,
            DigestAuthenticationHeader(
                nonce="abcdefg",
                realm="test",
                qop="anything",
                nc="00000002",
                cnonce_count=2,
                algorithm="MD5",
            ),
            (
                'Digest username="jane", realm="test", nonce="abcdefg", '
                'uri="/api/endpoint", algorithm="MD5", qop=anything, '
                'nc=00000002, cnonce="cnonce12", response="hash123"'
            ),
        ),
    ],
)
def test_calculate_digest_key(
    mock_time: Mock,
    mock_hashlib: Mock,
    username: str,
    password: str,
    uri: str,
    request_type: RequestTypes,
    digest_info: DigestAuthenticationHeader,
    expected_result: str,
):
    """Test calculation of digest key."""
    # Mock the necessary functions and methods for hashlib and os
    mock_hashlib.sha1 = Mock(
        return_value=Mock(hexdigest=Mock(return_value="cnonce123"))
    )
    mock_hashlib.md5.return_value = Mock(hexdigest=Mock(return_value="hash123"))

    os.urandom = Mock(return_value=b"cnonce123")

    # Mock the time.ctime() function
    mock_time.ctime.return_value = "Mon Jan 01 00:00:00 2023"

    result = calculate_digest_key(
        username, password, uri, request_type.name, digest_info
    )
    assert result == expected_result


@pytest.mark.parametrize(
    "username, password, uri, request_type, digest_info",
    [
        (
            "john",
            "password123",
            "/api/resource",
            RequestTypes.GET,
            DigestAuthenticationHeader(
                nonce="1234567890",
                realm="example.com",
                qop="anything",
                nc="00000001",
                cnonce_count=5,
                algorithm="FAKEALGO",
            ),
        ),
        (
            "john",
            "password123",
            "/api/resource",
            RequestTypes.GET,
            DigestAuthenticationHeader(
                nonce="1234567890",
                realm="example.com",
                qop="auth",
                nc="00000001",
                cnonce_count=5,
                algorithm="MD5",
            ),
        ),
    ],
)
def test_calculate_digest_key_value_errors(
    username: str,
    password: str,
    uri: str,
    request_type: RequestTypes,
    digest_info: DigestAuthenticationHeader,
):
    """Test calculation of digest key when the hashing algorithm doesn't exist."""
    with pytest.raises(ValueError) as _:
        _ = calculate_digest_key(
            username, password, uri, request_type.name, digest_info
        )
