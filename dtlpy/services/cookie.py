"""
Dataloop cookie state
"""

import os
import time
import json
import logging

logger = logging.getLogger('dataloop.cookie')


class CookieIO:
    """
    Cookie interface for Dataloop parameters
    """
    cwd = os.getcwd()
    local_dataloop_dir = os.path.join(cwd, '.dataloop')
    global_dataloop_dir = os.path.join(os.path.expanduser('~'), '.dataloop')
    global_cookie_file = os.path.join(global_dataloop_dir, 'cookie.json')
    local_cookie_file = os.path.join(local_dataloop_dir, 'state.json')
    local_cookie = None
    global_cookie = None

    @staticmethod
    def init():
        CookieIO.global_cookie = CookieIO(CookieIO.global_cookie_file)

    @staticmethod
    def init_local_cookie():
        CookieIO.local_cookie = CookieIO(CookieIO.local_cookie_file)

    def __init__(self, path):
        self.COOKIE = path
        # create directory '.dataloop' if not exists
        if not os.path.exists(os.path.dirname(self.COOKIE)):
            os.makedirs(os.path.dirname(self.COOKIE))

        if not os.path.exists(self.COOKIE) or os.path.getsize(self.COOKIE) == 0:
            self.reset()
        try:
            with open(self.COOKIE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            print('{} is corrupted'.format(self.COOKIE))
            raise SystemExit

    def get(self, key):
        logger.debug('COOKIE: Reading key: {}'.format(key))
        num_tries = 3
        for i in range(num_tries):
            try:
                with open(self.COOKIE, 'r') as fp:
                    cfg = json.load(fp)
                break
            except json.decoder.JSONDecodeError:
                if i == (num_tries-1):
                    raise
                time.sleep(0.1)
                continue
        if key in cfg.keys():
            return cfg[key]
        else:
            logger.warning(msg='key not in platform cookie file: %s. default is None' % key)
            return None

    def put(self, key, value):
        logger.debug('COOKIE: Writing key: {}'.format(key))
        with open(self.COOKIE, 'r') as fp:
            cfg = json.load(fp)
        cfg[key] = value
        with open(self.COOKIE, 'w') as fp:
            json.dump(cfg, fp, indent=4)

    def reset(self):
        with open(self.COOKIE, 'w') as fp:
            json.dump({}, fp)
