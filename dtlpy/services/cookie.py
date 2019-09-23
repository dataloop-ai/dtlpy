"""
Dataloop cookie state
"""

import os
import time
import json
import logging

logger = logging.getLogger(name=__name__)

NUM_TRIES = 3


class CookieIO:
    """
    Cookie interface for Dataloop parameters
    """

    def __init__(self, path, create=True, local=False):
        self.COOKIE = path
        self.local = local
        if create:
            self.create()

    @staticmethod
    def init():
        global_dataloop_dir = os.path.join(os.path.expanduser('~'), '.dataloop')
        global_cookie_file = os.path.join(global_dataloop_dir, 'cookie.json')
        return CookieIO(global_cookie_file)

    @staticmethod
    def init_local_cookie(create=False):
        local_cookie_file = os.path.join(os.getcwd(), '.dataloop', 'state.json')
        return CookieIO(local_cookie_file, create=create, local=True)

    @staticmethod
    def init_plugin_json_cookie(create=False):
        plugin_json_file = os.path.join(os.getcwd(), 'plugin.json')
        return CookieIO(plugin_json_file, create=create, local=True)

    def create(self):
        # create directory '.dataloop' if not exists
        if not os.path.isdir(os.path.dirname(self.COOKIE)):
            os.makedirs(os.path.dirname(self.COOKIE))

        if not os.path.isfile(self.COOKIE) or os.path.getsize(self.COOKIE) == 0:
            logger.debug('COOKIE.create: File: {}'.format(self.COOKIE))
            self.reset()
        try:
            with open(self.COOKIE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            print('{} is corrupted'.format(self.COOKIE))
            raise SystemExit

    def read_json(self, create=False):
        # which cookie
        if self.local:
            self.COOKIE = os.path.join(os.getcwd(), '.dataloop', 'state.json')

        # check if file exists - and create
        if not os.path.isfile(self.COOKIE) and create:
            self.create()

        # check if file exists
        if not os.path.isfile(self.COOKIE):
            logger.debug('COOKIE.read: File does not exist: {}. Return None'.format(self.COOKIE))
            cfg = {}
        else:
            # read cookie
            cfg = {}
            for i in range(NUM_TRIES):
                try:
                    with open(self.COOKIE, 'r') as fp:
                        cfg = json.load(fp)
                    break
                except json.decoder.JSONDecodeError:
                    if i == (NUM_TRIES - 1):
                        raise
                    time.sleep(0.1)
                    continue
        return cfg

    def get(self, key):
        if key not in ['calls_counter']:
            # ignore logging for some keys
            logger.debug('COOKIE.read: key: {}'.format(key))
        cfg = self.read_json()
        if key in cfg.keys():
            value = cfg[key]
        else:
            logger.warning(msg='Key not in platform cookie file: %s. Return None' % key)
            value = None
        return value

    def put(self, key, value):
        if key not in ['calls_counter']:
            # ignore logging for some keys
            logger.debug('COOKIE.write: key: {}'.format(key))
        # read and write
        cfg = self.read_json(create=True)
        cfg[key] = value
        with open(self.COOKIE, 'w') as fp:
            json.dump(cfg, fp, indent=4)

    def reset(self):
        with open(self.COOKIE, 'w') as fp:
            json.dump({}, fp)
