#
import sys
import traceback
import logging
logger = logging.getLogger(__name__)

def optional_reload(name, mod, noisy=False):
    try:
        reload(mod)
        logger.info("Reloaded module:%s", name)
    except :
        if noisy:
            traceback.print_exc()

def reload_all():
    [optional_reload(*x) for x in sys.modules.items()]
