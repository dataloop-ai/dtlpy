import logging
import jwt

logger = logging.getLogger(__name__)


def check(version, client_api):
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
        level = resp['level']
        msg = resp['msg']
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
    else:
        logger.debug(msg='unknown')
