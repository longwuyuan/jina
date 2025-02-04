import json
import logging
import re
from copy import copy
from logging import Formatter

from ..enums import LogVerbosity
from ..helper import colored

if False:
    from logging import LogRecord


class ColorFormatter(Formatter):
    """Format the log into colored logs based on the log-level."""

    MAPPING = {
        LogVerbosity.DEBUG: dict(color='black', attrs=['bold']),  # grey
        LogVerbosity.INFO: dict(),
        LogVerbosity.SUCCESS: dict(color='green'),
        LogVerbosity.WARNING: dict(color='yellow'),
        LogVerbosity.ERROR: dict(color='red'),
        LogVerbosity.CRITICAL: dict(color='red', attrs=['bold']),
    }  #: log-level to color mapping

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatters = {
            k: logging.Formatter(colored(self._fmt, **v))
            for k, v in self.MAPPING.items()
        }

    def format(self, record):
        """
        Format the LogRecord with corresponding colour.

        :param record: A LogRecord object
        :return:: Formatted LogRecord with level-colour MAPPING to add corresponding colour.
        """
        formatter = self.formatters.get(record.levelno)
        return formatter.format(record)


class PlainFormatter(Formatter):
    """Remove all control chars from the log and format it as plain text, also restrict the max-length of msg to 512."""

    def format(self, record):
        """
        Format the LogRecord by removing all control chars and plain text, and restrict the max-length of msg to 512.

        :param record: A LogRecord object.
        :return:: Formatted plain LogRecord.
        """
        cr = copy(record)
        if isinstance(cr.msg, str):
            cr.msg = re.sub(r'\u001b\[.*?[@-~]', '', str(cr.msg))[:512]
        return super().format(cr)


class JsonFormatter(Formatter):
    """Format the log message as a JSON object so that it can be later used/parsed in browser with javascript."""

    KEYS = {
        'created',
        'filename',
        'funcName',
        'levelname',
        'lineno',
        'msg',
        'module',
        'name',
        'pathname',
        'process',
        'thread',
        'processName',
        'threadName',
        'log_id',
    }  #: keys to extract from the log

    def format(self, record: 'LogRecord'):
        """
        Format the log message as a JSON object.

        :param record: A LogRecord object.
        :return:: LogRecord with JSON format.
        """
        cr = copy(record)
        cr.msg = re.sub(r'\u001b\[.*?[@-~]', '', str(cr.msg))
        return json.dumps(
            {k: getattr(cr, k) for k in self.KEYS if hasattr(cr, k)}, sort_keys=True
        )


class ProfileFormatter(Formatter):
    """Format the log message as JSON object and add the current used memory into it."""

    def format(self, record: 'LogRecord'):
        """
        Format the log message as JSON object and add the current used memory.

        :param record: A LogRecord object.
        :return:: Return JSON formatted log if msg of LogRecord is dict type else return empty.
        """
        from .profile import used_memory

        cr = copy(record)
        if isinstance(cr.msg, dict):
            cr.msg.update(
                {k: getattr(cr, k) for k in ['created', 'module', 'process', 'thread']}
            )
            cr.msg['memory'] = used_memory(unit=1)
            return json.dumps(cr.msg, sort_keys=True)
        else:
            return ''
