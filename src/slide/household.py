"""Methods that manage household information."""
import logging
from dataclasses import dataclass
from datetime import datetime

from slide.base_models import RequestTypes, Routine, SlideCloud

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
@dataclass
class Household:
    """Response model for retrieving households."""

    id: str  # pylint: disable=invalid-name
    name: str
    address: str | None
    lat: float | None
    lon: float | None
    xs_code: str | None
    holiday_mode: bool | None
    holiday_routines: list[Routine] | None
    created_at: str | None
    updated_at: str | None

    @property
    def created_at_datetime(self) -> datetime | None:
        """Parsed created_at property."""
        if self.created_at:
            return datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
        return None

    @property
    def updated_at_datetime(self) -> datetime | None:
        """Parsed created_at property."""
        if self.updated_at:
            return datetime.strptime(self.updated_at, "%Y-%m-%d %H:%M:%S")
        return None


async def get_household(slide: SlideCloud) -> Household:
    """
    This call provides household ID, name, address (optional), location in
    lat/lon (optional), whether or not holiday_mode is enabled and what the holiday time
    settings are.
    """
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix="/households"
    )
    return Household(**raw_response["data"])


async def edit_household(
    slide: SlideCloud,
    name: str,
    address: str,
    latitude: float = 0,
    longitude: float = 0,
) -> bool:
    """
    Change the name, human-readable address (feature not yet in applied) and lat/long of
    the household. For lat/long, use two decimals. Lat/long is used for routines such as
    sunrise/sunset. Find your lat/long at https://www.latlong.net/convert-address-to-lat-long.html
    """
    return bool(
        await slide.request(
            request_type=RequestTypes.PATCH,
            url_suffix="/households",
            data={
                "name": name,
                "address": address,
                "lat": latitude,
                "long": longitude,
            },
        )
    )


# pylint: disable=too-many-arguments
async def set_holiday_mode(
    slide: SlideCloud,
    enable: bool,
    open_from: str,
    open_to: str,
    close_from: str,
    close_to: str,
) -> bool:
    """
    Holiday Mode is set for the entire household (True or False).
    This call sets the interval time range for every Slide in the household.
    The open_* and close_* parameters must contain a string in Cron format.
    """
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/households/holiday_mode",
            data={
                "holiday_mode": enable,
                "data": [
                    {
                        "id": "cron:1",
                        "at": (
                            "@random:{"
                            f'"from":"{open_from}",'
                            f'"to":"{open_to}",'
                            '"number":1}'
                        ),
                        "enable": enable,
                        "action": "set_pos",
                        "payload": {"pos": 0, "offset": 0},
                    },
                    {
                        "id": "cron:2",
                        "at": (
                            "@random:{"
                            f'"from":"{close_from}",'
                            f'"to":"{close_to}",'
                            '"number":1}'
                        ),
                        "enable": enable,
                        "action": "set_pos",
                        "payload": {"pos": 1, "sound": False, "offset": 0},
                    },
                ],
            },
        )
    )
