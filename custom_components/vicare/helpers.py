""" Helper utilities"""
import logging
from time import time


def getLogger(name):
    """
    Replaces the default Logger with our wrapped implementation:
    replace your logging.getLogger with helpers.getLogger et voilà
    """
    logger = logging.getLogger(name)
    logger.__class__ = type('Logger', (_Logger, logger.__class__, ), {})
    return logger


class _Logger(logging.Logger):
    """
    This wrapper will 'filter' log messages and avoid
    verbose over-logging for the same message by using a timeout
    to prevent repeating the very same log before the timeout expires.
    The implementation 'hacks' a standard Logger instance by mixin-ing
    """

    # default timeout: these can be overriden at the log call level
    # by passing in the 'timeout=' param
    # for example: LOGGER.error("This error will %s be logged again", "soon", timeout=5)
    # it can also be overriden at the 'Logger' instance level
    default_timeout = 60 * 60 * 8
    # cache of logged messages with relative last-thrown-epoch
    _LOGGER_TIMEOUTS = {}

    def _log(self, level, msg, args, **kwargs): # pylint: disable=arguments-differ

        timeout = kwargs.pop('timeout', self.default_timeout)
        epoch = time()
        trap_key = (hash(msg), args)
        if trap_key in _Logger._LOGGER_TIMEOUTS:
            if ((epoch - _Logger._LOGGER_TIMEOUTS[trap_key]) < timeout):
                if self.isEnabledFor(logging.DEBUG):
                    super()._log(logging.DEBUG, f"dropped log message for {msg}", args)
                return

        super()._log(level, msg, args, **kwargs)
        _Logger._LOGGER_TIMEOUTS[trap_key] = epoch
