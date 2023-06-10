"""Simplify imports."""
import logging

from slide.authentication import (
    DigestAuthenticationHeader,
    calculate_digest_key,
    parse_response_header,
)
from slide.base_models import RequestTypes, SlideCloud, SlideLocal
from slide.household import (
    Household,
    edit_household,
    get_household,
    set_holiday_mode,
)
from slide.slides import (
    SlideDetail,
    SlideState,
    get_slide,
    get_slide_routines,
    get_slide_state,
    get_slides,
)
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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

__version__ = "0.1.1"

__all__ = [
    "DigestAuthenticationHeader",
    "calculate_digest_key",
    "parse_response_header",
    "SlideCloud",
    "SlideLocal",
    "RequestTypes",
    "Household",
    "edit_household",
    "get_household",
    "set_holiday_mode",
    "SlideDetail",
    "SlideState",
    "get_slide",
    # "get_slide_routine",
    "get_slide_routines",
    "get_slide_state",
    "get_slides",
    "Zone",
    "calibrate_zone",
    "create_zone",
    "create_zone_routine",
    "get_zone_routines",
    "get_zone_slides",
    "get_zones",
    "move_slide_to_zone",
    "remove_zone",
    "set_zone_position",
    "update_zone",
]
