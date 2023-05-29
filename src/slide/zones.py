"""Methods that manage zones and their Slides."""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from slide.base_models import RequestTypes, Routine, SlideCloud
from slide.slides import SlideState

logger = logging.getLogger(__name__)


@dataclass
class Zone:
    """Zone information."""

    id: str  # pylint: disable=invalid-name
    name: str
    household_id: int
    created_at: str | None
    updated_at: str | None

    @property
    def created_at_datetime(self) -> datetime | None:
        """Parsed created_at property."""
        if self.created_at:
            return datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        return None

    @property
    def updated_at_datetime(self) -> datetime | None:
        """Parsed created_at property."""
        if self.updated_at:
            return datetime.strptime(self.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        return None


async def get_zones(slide: SlideCloud) -> list[Zone]:
    """Get a list of all zones (ID and Name) currently in the household"""
    logger.info("Retrieving all zones.")
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix="/zones"
    )

    return [Zone(**v) for _, v in raw_response["data"].items()]


async def create_zone(slide: SlideCloud, zone_name: str) -> bool:
    """Create a new zone in the household."""
    logger.info("Creating zone: %s.", zone_name)
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix="/zones",
            data={"name": zone_name},
        )
    )


async def move_slide_to_zone(slide: SlideCloud, slide_id: int, zone_id: int) -> bool:
    """Move Slide to a different zone."""
    logger.info("Moving slide to zone %d", zone_id)
    return bool(
        await slide.request(
            request_type=RequestTypes.PATCH,
            url_suffix=f"/zones/{zone_id}/slides/{slide_id}/attach",
        )
    )


async def update_zone(slide: SlideCloud, zone_id: int, zone_name: str) -> bool:
    """Update a zone's name."""
    logger.info("Updating name for zone %d to %s", zone_id, zone_name)
    return bool(
        await slide.request(
            request_type=RequestTypes.PUT,
            url_suffix=f"/zones/{zone_id}",
            data={"name": zone_name},
        )
    )


async def remove_zone(slide: SlideCloud, zone_id: int) -> bool:
    """Update a zone's name."""
    logger.info("Removing zone %d.", zone_id)
    return bool(
        await slide.request(
            request_type=RequestTypes.DELETE,
            url_suffix=f"/zones/{zone_id}",
        )
    )


async def get_zone_routines(slide: SlideCloud, zone_id: int) -> list[Routine]:
    """Provide list of routines currently set in the zone."""
    logger.info("Retrieving routines for slides in zone %d.", zone_id)
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix=f"/zones/{zone_id}/routines"
    )
    found_routines = []
    for _, routines in raw_response["data"].items():
        found_routines += [Routine(**r) for r in routines]

    return found_routines


async def create_zone_routine(
    slide: SlideCloud, zone_id: int, routines: list[dict[str, Any]]
) -> bool:
    """Set a new routine for every Slide within the specified zone."""
    logger.info("Creating routine for zone %d.", zone_id)
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=f"/zones/{zone_id}/routines",
            data=routines,
        )
    )


async def get_zone_slides(slide: SlideCloud, zone_id: int) -> list[SlideState]:
    """Show Slide information within a specified zone."""
    logger.info("Retrieving slides in zone %d.", zone_id)
    raw_response = await slide.request(
        request_type=RequestTypes.GET, url_suffix=f"/zones/{zone_id}/slides/info"
    )
    slides = []
    for _, slide_response in raw_response["data"].items():
        # pylint: disable=no-member
        slides += [
            SlideState(
                **{
                    k: v
                    for k, v in slide_response["data"].items()
                    if k in SlideState.__dataclass_fields__.keys()
                }
            )
        ]

    return slides


async def set_zone_position(slide: SlideCloud, zone_id: int, position: float) -> bool:
    """
    Set position of a Slides within a zone, expressed as floating point with range
    0-1, where 0 is open and 1 is closed.
    """
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=f"/zones/{zone_id}/position",
            data={"pos": position},
        )
    )


async def calibrate_zone(slide: SlideCloud, zone_id: int) -> bool:
    """Calibrate all slides in a specified zone."""
    logger.info("Calibrating slides in zone %d.", zone_id)
    return bool(
        await slide.request(
            request_type=RequestTypes.POST,
            url_suffix=f"/zones/{zone_id}/calibrate",
        )
    )
