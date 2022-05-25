import time
import logging
import threading
import traceback
import jwt

logger = logging.getLogger('dtlpy')


def check_in_thread(version, client_api):
    try:
        # check for a valid token
        if client_api.token_expired():
            # wait for user to maybe login in the next 2 minutes
            time.sleep(120)
        # check for a valid token again
        if client_api.token_expired():
            # return if cant find a valid token
            logger.debug('Cant check_sdk without a valid token.')
            return

        # try read token for email
        try:
            payload = jwt.decode(client_api.token, algorithms=['HS256'],
                                 verify=False, options={'verify_signature': False})
            user_email = payload['email']
        except Exception:
            user_email = 'na'
        logger.debug('SDK info: user: {}, version: {}'.format(user_email, version))
        return_type, resp = client_api.gen_request(req_type='POST',
                                                   path='/sdk/check',
                                                   data={'version': version,
                                                         'email': user_email},
                                                   log_error=False)
        if resp.ok:
            resp = resp.json()
            client_api.cookie_io.put(key='check_version_status',
                                     value={'level': resp['level'],
                                            'msg': resp['msg']})
        else:
            client_api.cookie_io.put(key='check_version_status',
                                     value={'level': 'debug',
                                            'msg': 'unknown'})
    except Exception:
        logger.debug(traceback.format_exc())
        logger.debug('Error in check sdk manager.')


def check(version, client_api):
    worker = threading.Thread(target=check_in_thread,
                              kwargs={'version': version,
                                      'client_api': client_api})
    worker.daemon = True
    worker.start()
    status = client_api.cookie_io.get('check_version_status')
    if status is not None:
        level = status['level']
        msg = status['msg']
        if level.lower() == 'debug':
            logger.debug(msg=msg)
        elif level.lower() == 'info':
            logger.info(msg=msg)
        elif level.lower() == 'warning':
            logger.warning(msg=msg)
        elif level.lower() == 'error':
            logger.error(msg=msg)
        else:
            logger.debug(msg='unknown')


def resolve_platform_settings_in_thread(settings, client_api):
    try:
        # check for a valid token
        if client_api.token_expired():
            # wait for user to maybe login in the next 2 minutes
            time.sleep(120)
        # check for a valid token again
        if client_api.token_expired():
            # return if cant find a valid token
            logger.debug('Cant check_sdk without a valid token.')
            return
        settings_list = settings.resolve(user_email=client_api.info()['user_email'])
        settings_dict = {s.name: {s.scope.id: s.value,
                                  "default": s.default_value}
                         for s in settings_list}
        client_api.platform_settings.settings.update(settings_dict)
        client_api.platform_settings.to_cookie()

    except Exception:
        logger.debug(traceback.format_exc())
        logger.debug('Error in add settings.')


def resolve_platform_settings(client_api, settings):
    worker = threading.Thread(target=resolve_platform_settings_in_thread,
                              kwargs={'client_api': client_api, 'settings': settings})
    worker.daemon = True
    worker.start()
