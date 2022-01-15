import datetime

from tzlocal import get_localzone


class TimeUtils:

    @classmethod
    def now(cls, no_ms=False) -> datetime.datetime:
        """overwrite/mock in test"""
        now = datetime.datetime.now(tz=get_localzone())
        if no_ms:
            now = now.replace(microsecond=0)
        return now
