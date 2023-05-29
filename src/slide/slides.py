"""Methods that manage the slide."""
import logging
from dataclasses import dataclass
from typing import Any

from slide.base_models import RequestTypes, Routine, Slide, SlideCloud, SlideLocal

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
@dataclass
class SlideDetail:
    """Slide details when multiple are listed (somehow this is different)."""

    id: str  # pylint: disable=invalid-name
    device_name: str
    slide_setup: str
    curtain_type: str
    device_id: int
    household_id: int
    zone_id: int
    touch_go: bool
    max_pwm: int
    features: dict[str, Any]
    device_info: dict[str, Any]
    routines: list[dict[str, Any]]


@dataclass
class SlideDetailSingle:
    """Details of a single requested Slide."""

    id: int  # pylint: disable=invalid-name
    device_name: str
    slide_setup: str
    edition: int
    curtain_type: str
    mac_address: str
    device_id: str
    firmware_version: str
    pcb_version: str
    household_id: int
    zone_id: int
    touch_go: bool
    max_pwm: int
    created_at: str
    updated_at: str
    features: dict[str, Any]


# pylint: disable=too-many-instance-attributes
@dataclass
class SlideState:
    """State of a Slide."""

    board_rev: int
    calib_time: int
    mac: str
    pos: float
    slide_id: str
    touch_go: bool
    max_pwm: int | None = None


async def get_slides(slide: SlideCloud) -> list[SlideDetail]:
    """
    This powerful call returns a large set of information for each Slide in the
    household:

    - Device ID (required for device-specific calls)
    - Human-readable device name (as set by user)
    - Slide setup and curtain type (as set by user)
    - Household ID that each Slide belongs to (will be the same for all devices in a
      household)
    - Zone ID that each Slide belongs to (required for zone-specific calls)
    - If Touch&Go is enabled/disabled for that Slide
    - The current position of that Slide, expressed in a floating point between 0 and 1
    - Currently configured routines (Please note we use CRON format to define time
      settings, see: http://www.nncron.ru/help/EN/working/cron-format.htm). ALL TIMES
      ARE IN UTC.
    """
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix="/slides/overview"
    )
    return [SlideDetail(**r) for r in raw_response["slides"]]


async def get_slide(slide: Slide, slide_id: int) -> SlideDetailSingle:
    """
    This powerful call returns a large set of information for the specified Slide.

    - Device ID (required for device-specific calls)
    - Human-readable device name (as set by user)
    - Slide setup and curtain type (as set by user)
    - Household ID that each Slide belongs to (will be the same for all devices in a
      household)
    - Zone ID that each Slide belongs to (required for zone-specific calls)
    - If Touch&Go is enabled/disabled for that Slide
    - The current position of that Slide, expressed in a floating point between 0 and 1
    - Currently configured routines (Please note we use CRON format to define time
      settings, see: http://www.nncron.ru/help/EN/working/cron-format.htm). ALL TIMES
      ARE IN UTC.
    """
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix=f"/slides/{slide_id}"
    )
    return SlideDetailSingle(**raw_response["data"])


async def set_touch_and_go(slide: SlideCloud, slide_id: int, enable: bool) -> bool:
    """Enable or disable Touch&Go for a specific Slide."""
    return bool(
        await slide.request(
            request_type=RequestTypes.PATCH,
            url_suffix=f"/slide/{slide_id}",
            data={"touch_go": enable},
        )
    )


async def get_slide_state(
    slide: SlideLocal | SlideCloud, slide_id: int | None = None
) -> SlideState:
    """Find the current position of a slide and whether Touch&Go is enabled/disabled."""
    if isinstance(slide, SlideCloud) and slide_id is None:  # pragma: no cover
        raise ValueError("Slide ID is required to get the state of the Slide.")
    raw_response = await slide.request(
        request_type=RequestTypes.GET,
        url_suffix=slide.url.info.format(slide_id=slide_id),
    )

    data = raw_response["data"] if isinstance(slide, SlideCloud) else raw_response

    return SlideState(
        **{k: v for k, v in data.items() if k in SlideState.__dataclass_fields__.keys()}
    )


async def set_slide_position(
    slide: SlideCloud | SlideLocal, position: float, slide_id: int | None = None
) -> bool:
    """
    Set position of a specific Slide, expressed as floating point with range
    0-1, where 0 is open and 1 is closed.
    """
    if isinstance(slide, SlideCloud) and not slide_id:  # pragma: no cover
        raise ValueError("Slide ID is required to get the state of the Slide.")

    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=slide.url.position.format(slide_id=slide_id),
            data={"pos": position},
        )
    )


async def calibrate_slide(
    slide: SlideCloud | SlideLocal, slide_id: int | None = None
) -> bool:
    """Trigger a re-calibration of a specific Slide."""
    if isinstance(slide, SlideCloud) and slide_id is None:  # pragma: no cover
        raise ValueError("Slide ID is required to get the state of the Slide.")

    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=slide.url.calibrate.format(slide_id=slide_id),
        )
    )


async def stop_slide(
    slide: SlideCloud | SlideLocal, slide_id: int | None = None
) -> bool:
    """Stop motor of a specific Slide."""
    if isinstance(slide, SlideCloud) and slide_id is None:  # pragma: no cover
        raise ValueError("Slide ID is required to get the state of the Slide.")

    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=slide.url.stop.format(slide_id=slide_id),
        )
    )


async def get_slide_routines(slide: SlideCloud, slide_id: int) -> list[Routine]:
    """Provide list of routines currently set on the device."""
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix=f"/slide/{slide_id}/routines"
    )

    return [Routine(**d) for d in raw_response["data"]]


# TODO: Uncomment, but there seems to be an issue with the Slide API here.
#       It always returns:
#       {'data': {'code': 400, 'message': '{"response":"invalid id"}'}, 'error': None}
# async def get_slide_routine(
#     slide: SlideCloud, slide_id: int, routine_id: str
# ) -> Routine:
#     """Get details of a specific routine ID."""
#     raw_response = await slide.request(
#         request_type=RequestTypes.GET,
#         url_suffix=f"/slide/{slide_id}/routines/{routine_id}",
#     )
#     return Routine(**raw_response["data"])


async def delete_slide_routines(
    slide: SlideCloud, slide_id: int, routine_ids: list[str]
) -> bool:
    """Get details of a specific routine ID."""
    return bool(
        await slide.request(
            request_type=RequestTypes.DELETE,
            url_suffix=f"/slide/{slide_id}/routines",
            data=[{"id": routine_id} for routine_id in routine_ids],
        )
    )


async def update_slide_routine(
    slide: SlideCloud, slide_id: int, routines: list[dict[str, Any]]
) -> bool:
    # pylint: disable=line-too-long
    """
    Edit routines of specific Slide.

    More details on the format of `routines` can be found
    [here](https://documenter.getpostman.com/view/6223391/S1Lu2pSf?version=latest#dd7b7e1f-6105-470e-ac90-6e0771680f9c).

    IMPORTANT: The first two routines are used exclusively for Holiday Mode.
               Routine-IDs 1 & 2 must always be used for holiday-mode for the mobile app
               to work.
    """
    return bool(
        await slide.request(
            request_type=RequestTypes.PUT,
            url_suffix=f"/slide/{slide_id}/routines",
            data=routines,
        )
    )


async def create_slide_routine(
    slide: SlideCloud, slide_id: int, routines: list[dict[str, Any]]
) -> bool:
    # pylint: disable=line-too-long
    """
    Edit routines of specific Slide.

    More details on the format of `routines` can be found
    [here](https://documenter.getpostman.com/view/6223391/S1Lu2pSf?version=latest#dd7b7e1f-6105-470e-ac90-6e0771680f9c).

    IMPORTANT: The first two routines are used exclusively for Holiday Mode.
               Routine-IDs 1 & 2 must always be used for holiday-mode for the mobile app
               to work.
    """
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=f"/slide/{slide_id}/routines",
            data=routines,
        )
    )


async def configure_slide_wifi(slide: SlideLocal, ssid: str, password: str) -> bool:
    """Update the WiFi credentials that your Slide connects to."""
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/rpc/Slide.Config.WiFi",
            data={"ssid": ssid, "pass": password},
        )
    )
