"""Test base models."""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Type
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from aiohttp.web import HTTPBadRequest, HTTPClientError, HTTPForbidden, HTTPUnauthorized
from slide.authentication import calculate_digest_key, parse_response_header
from slide.base_models import TIMEOUT, RequestTypes, SlideCloud, SlideLocal


@pytest.mark.parametrize(
    "username, password, expected_username, expected_password",
    [
        (None, "some-pass", "user", "some-pass"),
        (
            "test_user",
            "test_password",
            "test_user",
            "test_password",
        ),
        (
            "username",
            "pass",
            "username",
            "pass",
        ),
    ],
)
def test_slide_cloud_initialization(
    username: str | None,
    password: str | None,
    expected_username: str,
    expected_password: str,
):
    """Test SlideCloud initialization."""
    os.environ["SLIDE_API_USERNAME"] = "user"
    os.environ["SLIDE_API_PASSWORD"] = ""

    slide = SlideCloud(username=username, password=password)

    assert slide.username == expected_username
    assert slide.password == expected_password
    assert slide.headers == {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # pylint: disable=protected-access
    assert slide._cnoncecount == 0  # type: ignore
    assert slide._access_token == ""  # type: ignore

    del os.environ["SLIDE_API_USERNAME"]
    del os.environ["SLIDE_API_PASSWORD"]


# pylint: disable=too-many-arguments
@pytest.mark.asyncio
@patch("slide.base_models.aiohttp.request")
@patch("slide.base_models.aiohttp.TCPConnector")
@pytest.mark.parametrize(
    "request_type, url_suffix, data, headers, verify_ssl",
    [
        (
            RequestTypes.POST,
            "/zones/1/position",
            {"pos": 0.5},
            {"Content-Type": "application/json"},
            True,
        ),
        (
            RequestTypes.GET,
            "/zones/2/data",
            None,
            {"Authorization": "Bearer token123"},
            False,
        ),
        # Add more test cases as needed
    ],
)
async def test_raw_request(
    mock_tcp_connector: Mock,
    mock_request: Mock,
    request_type: RequestTypes,
    url_suffix: str,
    data: dict[str, Any] | None,
    headers: dict[str, Any],
    verify_ssl: bool,
):
    """Test Slide._raw_request."""
    slide = SlideCloud()
    # pylint: disable=protected-access
    expected_url = slide._base_url + url_suffix
    mock_tcp_connector.return_value = "test"

    async with slide._raw_request(
        request_type=request_type,
        url_suffix=url_suffix,
        data=data,
        headers=headers,
        verify_ssl=verify_ssl,
    ) as _:
        # Assert that aiohttp.request was called with the correct arguments
        mock_request.assert_called_once_with(
            method=request_type.name,
            url=expected_url,
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            connector=None if verify_ssl else mock_tcp_connector.return_value,
        )


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.login")
@patch("slide.base_models.Slide._raw_request")
@pytest.mark.parametrize(
    "data, verify_ssl, expected_json",
    [
        (
            {"foo": "bar"},
            True,
            {"success": True},
        ),
        (
            None,
            False,
            {"success": True},
        ),
        (
            [1, 2, 3],
            True,
            {"success": True},
        ),
    ],
)
async def test_request_200(
    mock_raw_request: Mock,
    mock_login: Mock,
    data: dict[str, Any] | list[str] | None,
    verify_ssl: bool,
    expected_json: dict[str, Any],
):
    slide = SlideCloud("username", "password")

    mock_raw_request.return_value.__aenter__.return_value = Mock(
        status=200,
        json=AsyncMock(return_value=expected_json),
        text=AsyncMock(return_value=json.dumps(expected_json)),
    )

    response = await slide.request(
        request_type=RequestTypes.POST,
        url_suffix="/api/v1/some-endpoint",
        data=data,
        verify_ssl=verify_ssl,
    )

    mock_login.assert_called_once()

    assert response == expected_json


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.login")
@patch("slide.base_models.Slide._raw_request")
@pytest.mark.parametrize(
    "data, verify_ssl, expected_json",
    [
        (
            {"foo": "bar"},
            True,
            {"success": False},
        ),
        (
            None,
            False,
            {"success": False},
        ),
        (
            [1, 2, 3],
            True,
            {"success": False},
        ),
    ],
)
async def test_request_401(
    mock_raw_request: Mock,
    mock_login: Mock,
    data: dict[str, Any] | list[str] | None,
    verify_ssl: bool,
    expected_json: dict[str, Any],
):
    slide = SlideCloud("username", "password")

    mock_raw_request.return_value.__aenter__.side_effect = [
        Mock(
            status=401,
            json=AsyncMock(return_value=expected_json),
            text=AsyncMock(return_value=json.dumps(expected_json)),
        ),
        Mock(
            status=200,
            json=AsyncMock(return_value=expected_json),
            text=AsyncMock(return_value=json.dumps(expected_json)),
        ),
    ]

    response = await slide.request(
        request_type=RequestTypes.POST,
        url_suffix="/api/v1/some-endpoint",
        data=data,
        verify_ssl=verify_ssl,
    )

    assert mock_login.call_count == 3
    assert response == expected_json


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.login")
@patch("slide.base_models.Slide._raw_request")
@pytest.mark.parametrize(
    "status_code, raised_exception",
    [
        (400, HTTPBadRequest),
        (403, HTTPForbidden),
    ],
)
async def test_request_400_403(
    mock_raw_request: Mock,
    mock_login: Mock,
    status_code: int,
    raised_exception: Type[HTTPClientError],
):
    slide = SlideCloud("username", "password")

    mock_raw_request.return_value.__aenter__.return_value = Mock(
        status=status_code,
        json=AsyncMock(return_value={"error": "message"}),
        text=AsyncMock(return_value="Error message"),
    )

    with pytest.raises(raised_exception):
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/api/v1/some-endpoint",
            data={},
            verify_ssl=True,
            skip_login=True,
        )

    mock_login.assert_not_called()


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.login")
@patch("slide.base_models.Slide._raw_request")
@pytest.mark.parametrize(
    "data, verify_ssl, expected_json",
    [
        (
            {"foo": "bar"},
            True,
            {"success": False},
        ),
        (
            None,
            False,
            {"success": False},
        ),
        (
            [1, 2, 3],
            True,
            {"success": False},
        ),
    ],
)
async def test_request_401_failed_login(
    mock_raw_request: Mock,
    mock_login: Mock,
    data: dict[str, Any] | list[str] | None,
    verify_ssl: bool,
    expected_json: dict[str, Any],
):
    slide = SlideCloud("username", "password")

    mock_raw_request.return_value.__aenter__.return_value = Mock(
        status=401,
        json=AsyncMock(return_value=expected_json),
        text=AsyncMock(return_value=json.dumps(expected_json)),
    )

    with pytest.raises(HTTPUnauthorized) as _:
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/api/v1/some-endpoint",
            data=data,
            verify_ssl=verify_ssl,
            skip_login=True,
        )

    mock_login.assert_not_called()


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.login")
@patch("slide.base_models.Slide._raw_request")
@pytest.mark.parametrize(
    "data, verify_ssl, expected_json",
    [
        (
            {"foo": "bar"},
            True,
            {"success": False},
        ),
        (
            None,
            False,
            {"success": False},
        ),
        (
            [1, 2, 3],
            True,
            {"success": False},
        ),
    ],
)
async def test_request_unknown_status(
    mock_raw_request: Mock,
    mock_login: Mock,
    data: dict[str, Any] | list[str] | None,
    verify_ssl: bool,
    expected_json: dict[str, Any],
):
    slide = SlideCloud("username", "password")

    mock_raw_request.return_value.__aenter__.return_value = Mock(
        status=333,
        json=AsyncMock(return_value=expected_json),
        text=AsyncMock(return_value=json.dumps(expected_json)),
    )

    with pytest.raises(NotImplementedError) as _:
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/api/v1/some-endpoint",
            data=data,
            verify_ssl=verify_ssl,
            skip_login=True,
        )

    mock_login.assert_not_called()


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "access_token, token_expires, response, expected_token",
    [
        (
            "token1",
            datetime.now() - timedelta(hours=1),
            {"access_token": "another-token", "expires_at": "2022-01-01 00:00:00"},
            "token1",
        ),
        (
            None,
            None,
            {"access_token": "token3", "expires_at": "2022-01-01 00:00:00"},
            "token3",
        ),
    ],
)
async def test_slide_cloud_login(
    mock_request: AsyncMock,
    access_token: str,
    token_expires: datetime,
    response: dict[str, Any],
    expected_token: str,
):
    """Test that the SlideCloud.login method works as expected."""
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")
    slide._access_token = access_token
    slide._token_expires = token_expires

    token = await slide.login(response)  # type: ignore

    if not response:
        mock_request.assert_not_called()

    assert token == expected_token
    assert slide.headers["Authorization"] == f"Bearer {expected_token}"


@pytest.mark.parametrize(
    # pylint: disable=line-too-long
    (
        "base_url, device_code, expected_username, expected_url_info, "
        "expected_url_stop, expected_url_position, expected_url_calibrate"
    ),
    [
        (
            "https://example.com",
            "12345",
            "user",
            "/rpc/Slide.GetInfo",
            "/rpc/Slide.Stop",
            "/rpc/Slide.SetPos",
            "/rpc/Slide.Calibrate",
        ),
        (
            "https://test.com",
            "67890",
            "user",
            "/rpc/Slide.GetInfo",
            "/rpc/Slide.Stop",
            "/rpc/Slide.SetPos",
            "/rpc/Slide.Calibrate",
        ),
    ],
)
def test_slide_local_initialization(
    base_url: str,
    device_code: str,
    expected_username: str,
    expected_url_info: str,
    expected_url_stop: str,
    expected_url_position: str,
    expected_url_calibrate: str,
):
    slide_local = SlideLocal(base_url=base_url, device_code=device_code)

    assert slide_local.username == expected_username
    assert slide_local.url.info == expected_url_info
    assert slide_local.url.stop == expected_url_stop
    assert slide_local.url.position == expected_url_position
    assert slide_local.url.calibrate == expected_url_calibrate


@patch(
    "slide.base_models.SlideLocal.request_digest_access_token", new_callable=AsyncMock
)
@pytest.mark.parametrize(
    "request_type, url_suffix, headers, data, expected_token",
    [
        (RequestTypes.GET, "/some-url", {}, {"data": "anything"}, "token1"),
        (RequestTypes.POST, "/another-url", {"header": "data"}, {}, "token2"),
    ],
)
@pytest.mark.asyncio
async def test_slide_local_login(
    mock_request_digest_access_token: AsyncMock,
    request_type: RequestTypes,
    url_suffix: str,
    headers: dict[str, Any] | None,
    data: dict[str, Any] | list[Any] | None,
    expected_token: str,
):
    slide = SlideLocal(base_url="https://example.com", device_code="12345")
    mock_request_digest_access_token.return_value = expected_token

    response = Mock(
        _url=Mock(path=url_suffix),
        request_info=Mock(method=request_type.value, headers=headers),
    )

    token = await slide.login(response)  # type: ignore

    mock_request_digest_access_token.assert_called_once_with(
        request_type=request_type,
        url_suffix=url_suffix,
        headers=headers,
    )

    assert token == expected_token
    assert slide.headers["Authorization"] == f"Bearer {token}"


@pytest.mark.asyncio
@patch("slide.base_models.Slide._raw_request")
@patch("slide.authentication.os")
@patch("slide.authentication.time")
@pytest.mark.parametrize(
    "response_headers",
    [
        (
            {
                "WWW-Authenticate": (
                    'Digest realm="example.com", nonce="12345", '
                    'op="testvalue", qop="something"'
                )
            }
        ),
        ({}),
    ],
)
async def test_request_digest_access_token(
    mock_time: Mock,
    mock_os: Mock,
    mock_raw_request: Mock,
    response_headers: dict[str, Any],
):
    mock_time.ctime.return_value = "Fri Jun  2 23:53:00 2023"
    mock_os.urandom.return_value = b"testvalue"
    mock_raw_request.return_value.__aenter__.return_value = Mock(
        headers=response_headers,
    )

    slide_local = SlideLocal(base_url="https://example.com", device_code="12345")

    if not response_headers:
        with pytest.raises(HTTPUnauthorized):
            await slide_local.request_digest_access_token(
                request_type=RequestTypes.POST,
                url_suffix="/some-url",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    else:
        token = await slide_local.request_digest_access_token(
            request_type=RequestTypes.POST,
            url_suffix="/some-url",
            headers=response_headers,
        )

        assert token == calculate_digest_key(
            username="user",
            password=str(slide_local.device_code),
            uri=slide_local._base_url + "/some-url",
            request_type=RequestTypes.POST.name,
            digest_info=parse_response_header(
                response_headers["WWW-Authenticate"], cnonce_count=1
            ),
        )


@pytest.mark.asyncio
async def test_local_no_login():
    """Test login when no response is given."""
    slide_local = SlideLocal(base_url="https://example.com", device_code="12345")

    assert await slide_local.login(response=None) == slide_local._access_token
