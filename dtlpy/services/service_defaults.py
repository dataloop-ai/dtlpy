import os

DATALOOP_PATH = os.environ['DATALOOP_PATH'] if 'DATALOOP_PATH' in os.environ \
    else os.path.join(os.path.expanduser('~'), '.dataloop')
DEFAULT_ENVIRONMENT = 'https://gate.dataloop.ai/api/v1'
DEFAULT_ENVIRONMENTS = {
    'https://dev-gate.dataloop.ai/api/v1':
        {'alias': 'dev',
         'audience': 'https://dataloop-development.auth0.com/api/v2/',
         'client_id': 'I4Arr9ixs5RT4qIjOGtIZ30MVXzEM4w8',
         'auth0_url': 'https://dataloop-development.auth0.com',
         'token': None,
         'refresh_token': None,
         'verify_ssl': True},
    'https://rc-gate.dataloop.ai/api/v1':
        {'alias': 'rc',
         'audience': 'https://dataloop-development.auth0.com/api/v2/',
         'client_id': 'I4Arr9ixs5RT4qIjOGtIZ30MVXzEM4w8',
         'auth0_url': 'https://dataloop-development.auth0.com',
         'token': None,
         'refresh_token': None,
         'verify_ssl': True},
    'https://gate.dataloop.ai/api/v1': {
        'alias': 'prod',
        'audience': 'https://dataloop-production.auth0.com/userinfo',
        'client_id': 'FrG0HZga1CK5UVUSJJuDkSDqItPieWGW',
        'auth0_url': 'https://dataloop-production.auth0.com',
        'token': None,
        'refresh_token': None,
        'verify_ssl': True},
    'https://localhost:8443/api/v1': {
        'alias': 'local',
        'audience': 'https://dataloop-local.auth0.com/userinfo',
        'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
        'auth0_url': 'https://dataloop-local.auth0.com',
        'token': None,
        'refresh_token': None,
        'verify_ssl': False},
    'https://poc-gate.dataloop.ai/api/v1': {
        'alias': 'aws',
        'audience': 'https://dataloop-aws-poc.eu.auth0.com/api/v2/',
        'client_id': 'dHHctbFPa4TFgo1hh9Ig2Fyh71N46BEM',
        'auth0_url': 'https://dataloop-aws-poc.eu.auth0.com',
        'token': None,
        'refresh_token': None,
        'verify_ssl': True},
    'https://host.docker.internal:8443/api/v1': {
        'alias': 'docker_windows',
        'audience': 'https://dataloop-local.auth0.com/userinfo',
        'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
        'auth0_url': 'https://dataloop-local.auth0.com',
        'token': None,
        'refresh_token': None,
        'verify_ssl': False},
    'https://docker.for.mac.localhost:8443/api/v1': {
        'alias': 'minikube_local_mac',
        'audience': 'https://dataloop-local.auth0.com/userinfo',
        'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
        'auth0_url': 'https://dataloop-local.auth0.com',
        'token': None,
        'refresh_token': None,
        'verify_ssl': False}
}
