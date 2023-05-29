"""Module for dealing with the Slide API."""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, AsyncIterator

import aiohttp
from aiohttp.web import HTTPBadRequest, HTTPForbidden, HTTPUnauthorized

from slide.authentication import calculate_digest_key, parse_response_header

logger = logging.getLogger(__name__)

TIMEOUT = 30
DEFAULT_BASE_URL = "https://api.goslide.io/api"


class RequestTypes(Enum):
    """Possible request types for Slide API."""

    GET = auto()
    POST = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()


@dataclass
class SlideURLMapping:
    """Mapping of Slide API endpoints."""

    stop: str
    calibrate: str
    info: str
    position: str


@dataclass
class RoutinePayload:
    """Holiday mode update model for the payload of each cron job."""

    pos: int
    type: str
    openTime: str  # pylint: disable=invalid-name
    closeTime: str  # pylint: disable=invalid-name
    sound: bool | None
    offset: int


@dataclass
class Routine:
    """A holiday routine."""

    id: str  # pylint: disable=invalid-name
    at: str  # pylint: disable=invalid-name
    enable: bool
    action: str
    payload: RoutinePayload


# pylint: disable=too-many-instance-attributes
class Slide(ABC):
    """Slide object that holds authentication details throughout the session."""

    username: str | None
    password: str | None
    device_code: str | None
    _base_url: str
    _digest: str
    _token_expires: datetime
    _access_token: str
    _cnoncecount: int
    url: SlideURLMapping

    def __init__(
        self: Slide,
        username: str | None = None,
        password: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        device_code: str | None = None,
    ) -> None:
        self.username = username or os.environ.get("SLIDE_API_USERNAME", "user")
        self.password = password or os.environ.get("SLIDE_API_PASSWORD", None)
        self.device_code = device_code or os.environ.get("SLIDE_API_DEVICE_CODE", None)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._cnoncecount = 0
        self._access_token = ""
        self._token_expires = datetime.now()
        self._base_url = base_url

    @abstractmethod
    async def login(
        self: Slide,
        response: aiohttp.ClientResponse | None = None,
    ) -> None:
        """Set authentication headers."""

    @asynccontextmanager
    async def _raw_request(
        self,
        request_type: RequestTypes,
        *,
        url_suffix: str,
        data: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, Any] | None = None,
        verify_ssl: bool = True,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """Send a request and yield its raw response."""
        logger.debug(
            "Request: type=%s, url=%s%s, verify_ssl=%s",
            request_type.name,
            self._base_url,
            url_suffix,
            verify_ssl,
        )
        async with aiohttp.request(
            method=request_type.name,
            url=self._base_url + url_suffix,
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            connector=None if verify_ssl else aiohttp.TCPConnector(verify_ssl=False),
        ) as response:
            yield response

    async def request(
        self: Slide,
        request_type: RequestTypes,
        *,
        url_suffix: str,
        data: dict[str, Any] | list[Any] | None = None,
        verify_ssl: bool | None = None,
        headers: dict[str, Any] | None = None,
        is_retry: bool = False,
        skip_login: bool = False,
    ) -> dict[str, Any]:
        """Generic request handler."""
        verify_ssl = (
            verify_ssl if verify_ssl is not None else isinstance(self, SlideCloud)
        )
        if isinstance(self, SlideCloud) and not skip_login:
            await self.login(response=None)

        headers = {
            **{"Content-Type": "application/json", "Accept": "application/json"},
            **(self.headers or {}),
        }

        # Known error codes from the Cloud API:
        # 200 - All OK
        # 400 - Unable to find details for the given ID
        # 401 - Authentication failed
        # 403 - Forbidden, most likely we want to control a slide
        #       which isn't in our account
        # 404 - Can't find API endpoint
        # 422 - The given data was invalid
        # 424 - If one or multiple Slides are offline. The 'device_info'
        #       will contain code=500, 'Device unavailable' for those slides
        async with self._raw_request(
            request_type=request_type,
            url_suffix=url_suffix,
            headers=headers,
            data=data,
            verify_ssl=verify_ssl,
        ) as response:
            match response.status:
                case 200 | 424:
                    return await response.json()
                case 400:
                    raise HTTPBadRequest(
                        headers=self.headers,
                        reason="Invalid ID provided",
                        body=None,
                        text=await response.text(),
                    )
                case 403:
                    raise HTTPForbidden(
                        headers=self.headers,
                        reason="Forbidden route",
                        body=None,
                        text=await response.text(),
                    )
                case 401 | 422:
                    if not is_retry and not skip_login:
                        # Retry once by re-authenticating.
                        logger.debug(
                            "Got status %d. Will retry this request once.",
                            response.status,
                        )
                        self._access_token = ""
                        await self.login(response=response)
                        return await self.request(
                            request_type=request_type,
                            url_suffix=url_suffix,
                            data=data,
                            headers=headers,
                            verify_ssl=verify_ssl,
                            is_retry=True,
                        )
                    raise HTTPUnauthorized(
                        headers=self.headers, reason="Authentication failed."
                    )
                case _:
                    response_text = await response.text()
                    logger.fatal("Unable to process response:\n%s", response)
                    logger.fatal("Got the following response text:\n%s", response_text)
                    raise NotImplementedError(
                        f"Unable to process response.\n{response_text}"
                    )


class SlideLocal(Slide):
    """A Slide that uses the local API."""

    def __init__(
        self: SlideLocal,
        base_url: str,
        device_code: str,
    ) -> None:
        """Initialize inherited class."""
        self.username = "user"
        self.url = SlideURLMapping(
            info="/rpc/Slide.GetInfo",
            stop="/rpc/Slide.Stop",
            position="/rpc/Slide.SetPos",
            calibrate="/rpc/Slide.Calibrate",
        )

        super().__init__(
            base_url=base_url,
            device_code=device_code,
        )

    async def login(
        self: SlideLocal,
        response: aiohttp.ClientResponse | None = None,
    ) -> str:
        """Generate authentication header."""
        if not response:
            return self._access_token
        logger.debug("Requesting access token using device code.")
        access_token = await self.request_digest_access_token(
            request_type=RequestTypes(response.request_info.method),
            url_suffix=response._url.path,
            headers=dict(response.request_info.headers),
        )
        self._access_token = access_token
        self.headers["Authorization"] = f"Bearer {self._access_token}"

        return self._access_token

    async def request_digest_access_token(
        self: SlideLocal,
        request_type: RequestTypes,
        url_suffix: str,
        headers: dict[str, Any],
    ) -> str:
        """Create an access token using Digest authentication."""
        if "WWW-Authenticate" in headers:
            self._cnoncecount += 1
            return calculate_digest_key(
                username=str(self.username),
                password=str(self.device_code),
                uri=self._base_url + url_suffix,
                request_type=request_type.name,
                digest_info=parse_response_header(
                    headers["WWW-Authenticate"],
                    cnonce_count=self._cnoncecount,
                ),
            )
        raise HTTPUnauthorized(headers=headers, reason="Authentication failed.")


class SlideCloud(Slide):
    """A Slide that uses the cloud API."""

    def __init__(
        self: SlideCloud,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize inherited class."""
        self.url = SlideURLMapping(
            info="/slide/{slide_id}/info",
            stop="/slide/{slide_id}/stop",
            position="/slide/{slide_id}/position",
            calibrate="/slide/{slide_id}/calibrate",
        )

        super().__init__(
            username=username,
            password=password,
            base_url=DEFAULT_BASE_URL,
        )

    async def login(
        self: SlideCloud,
        response: aiohttp.ClientResponse | None = None,
    ) -> str:
        """Generate authentication header."""
        if (
            self._access_token
            and self._token_expires
            and self._token_expires < datetime.now()
        ):
            # If an access token is already provided, don't request a new one.
            logger.debug("No new access token will be requested.")
        else:
            logger.debug("Requesting access token using username/password.")
            token_data = await self.request(
                request_type=RequestTypes.POST,
                url_suffix="/auth/login",
                data={"email": self.username, "password": self.password},
                skip_login=True,
            )
            self._token_expires = datetime.strptime(
                token_data["expires_at"] + " +0000", "%Y-%m-%d %H:%M:%S %z"
            )
            self._access_token = token_data["access_token"]
        self.headers["Authorization"] = f"Bearer {self._access_token}"
        return self._access_token
