from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from slide.base_models import (
    RequestTypes,
    Routine,
    SlideCloud,
    SlideLocal,
)
from slide.slides import (
    SlideDetail,
    SlideDetailSingle,
    SlideState,
    calibrate_slide,
    configure_slide_wifi,
    create_slide_routine,
    delete_slide_routines,
    get_slide,
    get_slide_routines,
    get_slide_state,
    get_slides,
    set_slide_position,
    set_touch_and_go,
    stop_slide,
    update_slide_routine,
)


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "response, expected_result",
    [
        (
            {
                "slides": [
                    dict(
                        id="test",
                        device_name="some-name",
                        slide_setup="setup",
                        curtain_type="type",
                        device_id=1000,
                        household_id=1001,
                        zone_id=10002,
                        touch_go=True,
                        max_pwm=100,
                        features={},
                        device_info={},
                        routines=[],
                    )
                ]
            },
            [
                SlideDetail(
                    id="test",
                    device_name="some-name",
                    slide_setup="setup",
                    curtain_type="type",
                    device_id=1000,
                    household_id=1001,
                    zone_id=10002,
                    touch_go=True,
                    max_pwm=100,
                    features={},
                    device_info={},
                    routines=[],
                )
            ],
        ),
        ({"slides": []}, []),
    ],
)
async def test_get_slides(
    mock_request: AsyncMock,
    response: dict[str, Any],
    expected_result: list[SlideDetail],
):
    """Test get_slides."""
    mock_request.return_value = response

    slide_cloud = SlideCloud(username="user", password="password")

    result = await get_slides(slide=slide_cloud)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix="/slides/overview",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id, response, expected_result",
    [
        (
            1,
            {
                "data": dict(
                    id=1,
                    device_name="test",
                    slide_setup="something",
                    edition=1,
                    curtain_type="any",
                    mac_address="00:00:00:00:00",
                    device_id="something",
                    firmware_version="v1.0",
                    pcb_version="v2.0",
                    household_id=1,
                    zone_id=2,
                    touch_go=True,
                    max_pwm=100,
                    created_at="2020-01-01 00:00:00",
                    updated_at="2020-01-01 00:00:00",
                    features={},
                )
            },
            SlideDetailSingle(
                id=1,
                device_name="test",
                slide_setup="something",
                edition=1,
                curtain_type="any",
                mac_address="00:00:00:00:00",
                device_id="something",
                firmware_version="v1.0",
                pcb_version="v2.0",
                household_id=1,
                zone_id=2,
                touch_go=True,
                max_pwm=100,
                created_at="2020-01-01 00:00:00",
                updated_at="2020-01-01 00:00:00",
                features={},
            ),
        ),
    ],
)
async def test_get_slide(
    mock_request: AsyncMock,
    slide_id: int,
    response: dict[str, Any],
    expected_result: SlideDetailSingle,
):
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await get_slide(slide=slide, slide_id=slide_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix=f"/slides/{slide_id}",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id, enable",
    [
        (1, True),
        (2, False),
    ],
)
async def test_set_touch_and_go(
    mock_request: AsyncMock,
    slide_id: int,
    enable: bool,
):
    """Test set_touch_and_go."""
    mock_request.return_value = {"msg": "Hi!"}

    slide = SlideCloud(username="user", password="password")

    result = await set_touch_and_go(slide=slide, slide_id=slide_id, enable=enable)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.PATCH,
        url_suffix=f"/slide/{slide_id}",
        data={"touch_go": enable},
    )

    assert result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide, slide_id, response, expected_result",
    [
        (
            SlideCloud(username="user", password="password"),
            1,
            {
                "data": dict(
                    board_rev=1,
                    calib_time=2,
                    mac="00:00:00:00:00",
                    pos=1.2,
                    slide_id="slide",
                    touch_go=True,
                    max_pwm=None,
                )
            },
            SlideState(
                board_rev=1,
                calib_time=2,
                mac="00:00:00:00:00",
                pos=1.2,
                slide_id="slide",
                touch_go=True,
                max_pwm=None,
            ),
        ),
        (
            SlideLocal(device_code="asdf", base_url="http://localhost"),
            1,
            dict(
                board_rev=1,
                calib_time=2,
                mac="00:00:00:00:00",
                pos=1.2,
                slide_id="slide",
                touch_go=True,
                max_pwm=None,
            ),
            SlideState(
                board_rev=1,
                calib_time=2,
                mac="00:00:00:00:00",
                pos=1.2,
                slide_id="slide",
                touch_go=True,
                max_pwm=None,
            ),
        ),
    ],
)
async def test_get_slide_state(
    mock_request: AsyncMock,
    slide: SlideCloud | SlideLocal,
    slide_id: int,
    response: dict[str, Any],
    expected_result: SlideState | None,
):
    mock_request.return_value = response

    result = await get_slide_state(slide=slide, slide_id=slide_id)

    if isinstance(slide, SlideCloud):
        mock_request.assert_called_once_with(
            request_type=RequestTypes.GET,
            url_suffix=f"/slide/{slide_id}/info",
        )
    else:
        mock_request.assert_called_once_with(
            request_type=RequestTypes.GET,
            url_suffix="/rpc/Slide.GetInfo",
        )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide, slide_id, position",
    [
        (
            SlideCloud(username="user", password="password"),
            1,
            1.0,
        ),
        (
            SlideLocal(device_code="asdf", base_url="http://localhost"),
            1,
            0.0,
        ),
    ],
)
async def test_set_slide_position(
    mock_request: AsyncMock,
    slide: SlideCloud | SlideLocal,
    slide_id: int,
    position: float,
):
    """Test set_slide_position."""
    mock_request.return_value = {"msg": "Hi!"}

    result = await set_slide_position(slide=slide, slide_id=slide_id, position=position)

    if isinstance(slide, SlideCloud):
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix=f"/slide/{slide_id}/position",
            data={"pos": position},
        )
    else:
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix="/rpc/Slide.SetPos",
            data={"pos": position},
        )

    assert result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide, slide_id",
    [
        (
            SlideCloud(username="user", password="password"),
            1,
        ),
        (
            SlideLocal(device_code="asdf", base_url="http://localhost"),
            1,
        ),
    ],
)
async def test_calibrate_slide(
    mock_request: AsyncMock,
    slide: SlideCloud | SlideLocal,
    slide_id: int,
):
    """Test calibrate_slide."""
    mock_request.return_value = {"msg": "Hi!"}

    result = await calibrate_slide(slide=slide, slide_id=slide_id)

    if isinstance(slide, SlideCloud):
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix=f"/slide/{slide_id}/calibrate",
        )
    else:
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix="/rpc/Slide.Calibrate",
        )

    assert result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide, slide_id",
    [
        (
            SlideCloud(username="user", password="password"),
            1,
        ),
        (
            SlideLocal(device_code="asdf", base_url="http://localhost"),
            1,
        ),
    ],
)
async def test_stop_slide(
    mock_request: AsyncMock,
    slide: SlideCloud | SlideLocal,
    slide_id: int,
):
    """Test stop_slide."""
    mock_request.return_value = {"msg": "Hi!"}

    result = await stop_slide(slide=slide, slide_id=slide_id)

    if isinstance(slide, SlideCloud):
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix=f"/slide/{slide_id}/stop",
        )
    else:
        mock_request.assert_called_once_with(
            request_type=RequestTypes.POST,
            url_suffix="/rpc/Slide.Stop",
        )

    assert result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id, response, expected_result",
    [
        (
            1,
            {
                "data": [
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
                        ), # type: ignore
                    )
                ]
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
                    ), # type: ignore
                )
            ],
        ),
        (2, {"message": "Routines not found.", "data": []}, []),
    ],
)
async def test_get_slide_routines(
    mock_request: AsyncMock,
    slide_id: int,
    response: dict[str, Any],
    expected_result: list[Routine] | None,
):
    mock_request.return_value = response

    slide = SlideCloud(username="user", password="password")

    result = await get_slide_routines(slide=slide, slide_id=slide_id)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.GET,
        url_suffix=f"/slide/{slide_id}/routines",
    )

    assert result == expected_result


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id, routine_id",
    [
        (
            1,
            "2",
        ),
        (
            1,
            "2",
        ),
    ],
)
async def test_delete_slide_routines(
    mock_request: AsyncMock,
    slide_id: int,
    routine_id: str,
):
    """Test delete_slide_routines."""
    slide = SlideCloud(username="user", password="password")

    await delete_slide_routines(
        slide=slide, slide_id=slide_id, routine_ids=[routine_id]
    )

    mock_request.assert_called_once_with(
        request_type=RequestTypes.DELETE,
        url_suffix=f"/slide/{slide_id}/routines",
        data=[{"id": routine_id}],
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id",
    [
        1,
    ],
)
async def test_update_slide_routine(
    mock_request: AsyncMock,
    slide_id: int,
):
    """Test update_slide_routine."""
    slide = SlideCloud(username="user", password="password")
    await update_slide_routine(slide=slide, slide_id=slide_id, routines=[])

    mock_request.assert_called_once_with(
        request_type=RequestTypes.PUT,
        url_suffix=f"/slide/{slide_id}/routines",
        data=[],
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "slide_id",
    [1],
)
async def test_create_slide_routine(
    mock_request: AsyncMock,
    slide_id: int,
):
    """Test create_slide_routine."""
    slide = SlideCloud(username="user", password="password")

    await create_slide_routine(slide=slide, slide_id=slide_id, routines=[])

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST,
        url_suffix=f"/slide/{slide_id}/routines",
        data=[],
    )


@pytest.mark.asyncio
@patch("slide.base_models.Slide.request", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "ssid, password",
    [
        (
            "some-network",
            "fake-pass",
        ),
        (
            "another-network",
            "another-password",
        ),
    ],
)
async def test_configure_slide_wifi(
    mock_request: AsyncMock,
    ssid: str,
    password: str,
):
    """Test configure_slide_wifi."""
    slide = SlideLocal(device_code="device_code", base_url="http://localhost")

    await configure_slide_wifi(slide=slide, ssid=ssid, password=password)

    mock_request.assert_called_once_with(
        request_type=RequestTypes.POST,
        url_suffix="/rpc/Slide.Config.WiFi",
        data={"ssid": ssid, "pass": password},
    )
