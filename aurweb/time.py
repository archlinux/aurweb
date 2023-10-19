import zoneinfo
from collections import OrderedDict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Request

import aurweb.config


def tz_offset(name: str):
    """Get a timezone offset in the form "+00:00" by its name.

    Example: tz_offset('America/Los_Angeles')

    :param name: Timezone name
    :return: UTC offset in the form "+00:00"
    """
    dt = datetime.now(tz=zoneinfo.ZoneInfo(name))

    # Our offset in hours.
    offset = dt.utcoffset().total_seconds() / 60 / 60

    # Prefix the offset string with a - or +.
    offset_string = "-" if offset < 0 else "+"

    # Remove any negativity from the offset. We want a good offset. :)
    offset = abs(offset)

    # Truncate the floating point digits, giving the hours.
    hours = int(offset)

    # Subtract hours from the offset, and multiply the remaining fraction
    # (0 - 0.99[repeated]) with 60 minutes to get the number of minutes
    # remaining in the hour.
    minutes = int((offset - hours) * 60)

    # Pad the hours and minutes by two places.
    offset_string += "{:0>2}:{:0>2}".format(hours, minutes)
    return offset_string


SUPPORTED_TIMEZONES = OrderedDict(
    {
        # Flatten out the list of tuples into an OrderedDict.
        timezone: offset
        for timezone, offset in sorted(
            [
                # Comprehend a list of tuples (timezone, offset display string)
                # and sort them by (offset, timezone).
                (tz, "(UTC%s) %s" % (tz_offset(tz), tz))
                for tz in zoneinfo.available_timezones()
            ],
            key=lambda element: (tz_offset(element[0]), element[0]),
        )
    }
)


def get_request_timezone(request: Request) -> str:
    """Get a request's timezone from either query param or user settings.
    We use the configuration's [options] default_timezone otherwise.

    @param request FastAPI request
    """
    request_tz = request.query_params.get("timezone")
    if request_tz and request_tz in SUPPORTED_TIMEZONES:
        return request_tz
    elif (
        request.user.is_authenticated() and request.user.Timezone in SUPPORTED_TIMEZONES
    ):
        return request.user.Timezone
    return aurweb.config.get_with_fallback("options", "default_timezone", "UTC")


def now(timezone: str) -> datetime:
    """
    Get the current timezone-localized timestamp.

    :param timezone: Valid timezone supported by ZoneInfo
    :return: Current localized datetime
    """
    return datetime.now(tz=ZoneInfo(timezone))


def utcnow() -> int:
    """
    Get the current UTC timestamp.

    :return: Current UTC timestamp
    """
    return int(datetime.utcnow().timestamp())
