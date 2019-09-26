import logging
import threading
import jwt

logger = logging.getLogger(__name__)


def check_in_thread(version, client_api):
    try:
        payload = jwt.decode(client_api.token, algorithms=['HS256'], verify=False)
        user_email = payload['email']
    except:
        user_email = 'na'

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


def check(version, client_api):
    threading.Thread(target=check_in_thread, kwargs={'version': version,
                                                     'client_api': client_api}) \
        .start()
    status = client_api.cookie_io.get('check_version_status')
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
