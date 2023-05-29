"""Test the zones module in the slide package."""
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from slide.base_models import (
    RequestTypes,
    Routine,
    SlideCloud,
)
from slide.slides import SlideState
from slide.zones import (
    Zone,
    calibrate_zone,
    create_zone,
    create_zone_routine,
    get_zone_routines,
    get_zone_slides,
    get_zones,
    move_slide_to_zone,
    remove_zone,
    set_zone_position,
    update_zone,
)


@pytest.mark.parametrize(
    "zone, expected_created_at, expected_updated_at",
    [
        (
            Zone(
                id="1",
                name="Zone 1",
                household_id=1,
                created_at="2022-01-01T00:00:00.000Z",
                updated_at="2022-01-02T00:00:00.000Z",
            ),
            datetime(2022, 1, 1, 0, 0, 0),
            datetime(2022, 1, 2, 0, 0, 0),
        ),
        (
            Zone(
                id="1",
                name="Zone 2",
                household_id=2,
                created_at=None,
                updated_at=None,
            ),
            None,
            None,
        ),
    ],
)
def test_created_at_datetime(
    zone: Zone, expected_created_at: datetime, expected_updated_at: datetime
):
    """Test the created_at_datetime and updated_at_datetime properties."""
    assert zone.created_at_datetime == expected_created_at
    assert zone.updated_at_datetime == expected_updated_at


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "response, expected_result",
    [
        (
            {
                "data": {
                    "1234": dict(
                        id="1",
                        name="Zone 1",
                        household_id=1,
                        created_at="2022-01-01T00:00:00.000Z",
                        updated_at="2022-01-02T00:00:00.000Z",
                    ),
                    "5678": dict(
                        id="2",
                        name="Zone 2",
                        household_id=1,
                        created_at="2022-01-01T00:00:00.000Z",
                        updated_at="2022-01-02T00:00:00.000Z",
                    ),
                }
            },
            [
                Zone(
                    id="1",
                    name="Zone 1",
                    household_id=1,
                    created_at="2022-01-01T00:00:00.000Z",
                    updated_at="2022-01-02T00:00:00.000Z",
                ),
                Zone(
                    id="2",
                    name="Zone 2",
                    household_id=1,
                    created_at="2022-01-01T00:00:00.000Z",
                    updated_at="2022-01-02T00:00:00.000Z",
                ),
            ],
        ),
    ],
)
async def test_get_zones(
    mock_request: AsyncMock,
    response: dict[str, Any],
    expected_result: list[Zone],
):
    """Test get_zones."""
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await get_zones(slide=slide)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix="/zones",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_name",
    [
        "test",
        "test-2",
    ],
)
async def test_create_zone(
    mock_request: AsyncMock,
    zone_name: str,
):
    """Test create_zone."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await create_zone(slide=slide, zone_name=zone_name)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST, url_suffix="/zones", data={"name": zone_name}
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id, zone_id",
    [
        (
            1,
            2,
        ),
        (
            2,
            3,
        ),
    ],
)
async def test_move_slide_to_zone(
    mock_request: AsyncMock,
    slide_id: int,
    zone_id: int,
):
    """Test move_slide_to_zone."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await move_slide_to_zone(slide=slide, slide_id=slide_id, zone_id=zone_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.PATCH,
        url_suffix=f"/zones/{zone_id}/slides/{slide_id}/attach",
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id, zone_name",
    [
        (
            1,
            "test",
        ),
        (
            2,
            "test-2",
        ),
    ],
)
async def test_update_zone(
    mock_request: AsyncMock,
    zone_id: int,
    zone_name: str,
):
    """Test update_zone."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await update_zone(slide=slide, zone_id=zone_id, zone_name=zone_name)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.PUT,
        url_suffix=f"/zones/{zone_id}",
        data={"name": zone_name},
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id",
    [1, 2],
)
async def test_remove_zone(
    mock_request: AsyncMock,
    zone_id: int,
):
    """Test update_zone."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await remove_zone(slide=slide, zone_id=zone_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.DELETE,
        url_suffix=f"/zones/{zone_id}",
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id, response, expected_result",
    [
        (
            1,
            {
                "data": {
                    "1234": [
                        dict(
                            id="1234",
                            at="12:00",
                            enable=True,
                            action="example_action",
                            payload=dict(
                                pos=1,
                                type="example",
                                openTime="08:00",
                                closeTime="17:00",
                                sound=True,
                                offset=10,
                            ),
                        )
                    ]
                }
            },
            [
                Routine(
                    id="1234",
                    at="12:00",
                    enable=True,
                    action="example_action",
                    payload=dict(
                        pos=1,
                        type="example",
                        openTime="08:00",
                        closeTime="17:00",
                        sound=True,
                        offset=10,
                    ),
                )
            ],
        ),
    ],
)
async def test_get_zone_routines(
    mock_request: AsyncMock,
    zone_id: int,
    response: dict[str, Any],
    expected_result: list[Zone],
):
    """Test get_zone_routines."""
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await get_zone_routines(slide=slide, zone_id=zone_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix=f"/zones/{zone_id}/routines",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id",
    [1, 2],
)
async def test_create_zone_routine(
    mock_request: AsyncMock,
    zone_id: int,
):
    """Test create_zone_routine."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await create_zone_routine(slide=slide, zone_id=zone_id, routines=[])

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST,
        url_suffix=f"/zones/{zone_id}/routines",
        data=[],
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id, response, expected_result",
    [
        (
            1,
            {
                "data": {
                    "1234": {
                        "data": dict(
                            board_rev=1,
                            calib_time=2,
                            mac="00:00:00:00:00",
                            pos=1.2,
                            slide_id="slide",
                            touch_go=True,
                            max_pwm=None,
                        )
                    }
                }
            },
            [
                SlideState(
                    board_rev=1,
                    calib_time=2,
                    mac="00:00:00:00:00",
                    pos=1.2,
                    slide_id="slide",
                    touch_go=True,
                    max_pwm=None,
                )
            ],
        ),
        (
            2,
            {"data": {}},
            [],
        ),
    ],
)
async def test_get_zone_slides(
    mock_request: AsyncMock,
    zone_id: int,
    response: dict[str, Any],
    expected_result: list[Zone],
):
    """Test get_zone_slides."""
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await get_zone_slides(slide=slide, zone_id=zone_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix=f"/zones/{zone_id}/slides/info",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id, position",
    [
        (
            1,
            0.5,
        ),
        (
            2,
            1,
        ),
    ],
)
async def test_set_zone_position(
    mock_request: AsyncMock,
    zone_id: int,
    position: float,
):
    """Test set_zone_position."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await set_zone_position(slide=slide, zone_id=zone_id, position=position)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST,
        url_suffix=f"/zones/{zone_id}/position",
        data={"pos": position},
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "zone_id",
    [1, 2],
)
async def test_calibrate_zone(
    mock_request: AsyncMock,
    zone_id: int,
):
    """Test calibrate_zone."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    await calibrate_zone(slide=slide, zone_id=zone_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST,
        url_suffix=f"/zones/{zone_id}/calibrate",
    )
