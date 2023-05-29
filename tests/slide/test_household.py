from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from slide.base_models import RequestTypes, SlideCloud
from slide.household import Household, edit_household, get_household, set_holiday_mode


@pytest.mark.parametrize(
    "created_at, updated_at, expected_created_at, expected_updated_at",
    [
        (
            "2022-01-01 00:00:00",
            "2022-01-02 00:00:00",
            datetime(2022, 1, 1, 0, 0, 0),
            datetime(2022, 1, 2, 0, 0, 0),
        ),
        ("2022-01-01 00:00:00", None, datetime(2022, 1, 1, 0, 0, 0), None),
        (None, "2022-01-02 00:00:00", None, datetime(2022, 1, 2, 0, 0, 0)),
    ],
)
def test_created_at_datetime(
    created_at: str,
    updated_at: str,
    expected_created_at: datetime | None,
    expected_updated_at: datetime | None,
):
    """Test created_at_datetime and updated_at_datetime properties."""
    household = Household(
        id="123",
        name="Test Household",
        address="123 Main St",
        lat=37.7749,
        lon=-122.4194,
        xs_code="ABC123",
        holiday_mode=True,
        holiday_routines=[],
        created_at=created_at,
        updated_at=updated_at,
    )

    assert household.created_at_datetime == expected_created_at
    assert household.updated_at_datetime == expected_updated_at


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_response, expected_household",
    [
        (
            {
                "data": {
                    "id": "123",
                    "name": "Test Household",
                    "address": "123 Main St",
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "xs_code": "ABC123",
                    "holiday_mode": True,
                    "holiday_routines": [],
                    "created_at": "2022-01-01 00:00:00",
                    "updated_at": "2022-01-02 00:00:00",
                }
            },
            Household(
                id="123",
                name="Test Household",
                address="123 Main St",
                lat=37.7749,
                lon=-122.4194,
                xs_code="ABC123",
                holiday_mode=True,
                holiday_routines=[],
                created_at="2022-01-01 00:00:00",
                updated_at="2022-01-02 00:00:00",
            ),
        ),
        (
            {
                "data": {
                    "id": "456",
                    "name": "Another Household",
                    "address": None,
                    "lat": None,
                    "lon": None,
                    "xs_code": None,
                    "holiday_mode": False,
                    "holiday_routines": None,
                    "created_at": "2022-01-03 00:00:00",
                    "updated_at": "2022-01-04 00:00:00",
                }
            },
            Household(
                id="456",
                name="Another Household",
                address=None,
                lat=None,
                lon=None,
                xs_code=None,
                holiday_mode=False,
                holiday_routines=None,
                created_at="2022-01-03 00:00:00",
                updated_at="2022-01-04 00:00:00",
            ),
        ),
    ],
)
async def test_get_household(mock_response: Mock, expected_household: Household):
    """Test get_household() function."""
    mock_slide = AsyncMock(spec=SlideCloud)
    mock_slide.request.return_value = mock_response

    household = await get_household(mock_slide)

    mock_slide.request.assert_called_once_with(
        request_type=RequestTypes.GET, url_suffix="/households"
    )
    assert household == expected_household

    assert isinstance(household.created_at_datetime, datetime)
    assert isinstance(household.updated_at_datetime, datetime)


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request")
@pytest.mark.parametrize(
    "name, address, latitude, longitude, response",
    [
        (
            "New Name",
            "New Address",
            1.23,
            4.56,
            {"message": "Household successfully updated."},
        )
    ],
)
async def test_edit_household(
    mock_request: AsyncMock,
    name: str,
    address: str,
    latitude: float,
    longitude: float,
    response: dict[str, Any],
):
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await edit_household(
        slide=slide,
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    mock_request.assert_called_once_with(
        request_type=RequestTypes.PATCH,
        url_suffix="/households",
        data={
            "name": name,
            "address": address,
            "lat": latitude,
            "long": longitude,
        },
    )

    assert result is True


@pytest.mark.asyncio
@patch("slide.base_models.SlideCloud.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "holiday_mode",
    [
        True,
        False,
    ],
)
async def test_set_holiday_mode(
    mock_request: AsyncMock,
    holiday_mode: bool,
):
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    result = await set_holiday_mode(
        slide=slide,
        enable=holiday_mode,
        open_from="0 0 12 * * *",
        open_to="0 30 8 * * *",
        close_from="0 0 20 * * *",
        close_to="0 30 20 * * *",
    )

    assert result

    mock_request.assert_called_once()
