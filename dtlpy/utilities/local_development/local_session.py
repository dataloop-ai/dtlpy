import requests
import logging
import shutil
import time
import sys
import os

import dtlpy as dl

logger = logging.getLogger('dtlpy')
DOCKER_CONTAINER_NAME = 'dtlpy-development'


def spinning_cursor():
    while True:
        for cursor in ["(●             ●)",
                       "( ●           ● )",
                       "(  ●         ●  )",
                       "(   ●       ●   )",
                       "(    ●     ●    )",
                       "(     ●   ●     )",
                       "(      ● ●      )",
                       "(       ●       )",
                       "(      ● ●      )",
                       "(     ●   ●     )",
                       "(    ●     ●    )",
                       "(   ●       ●   )",
                       "(  ●         ●  )",
                       "( ●           ● )",
                       "(●             ●)",
                       ]:
            yield cursor


def copy_files_to_docker_container():
    from distutils.dir_util import copy_tree
    local_state_directory = os.path.dirname(dl.client_api.state_io.COOKIE)
    root_dir = os.path.dirname(local_state_directory)
    dtlpy_code_server_dir = os.path.join(dl.__path__[0], 'assets', 'code_server')
    local_code_server_dir = os.path.join(local_state_directory, 'code_server')
    copy_tree(src=dtlpy_code_server_dir, dst=local_code_server_dir)
    if not os.path.isdir(os.path.join(root_dir, '.vscode')):
        os.makedirs(os.path.join(root_dir, '.vscode'))
        shutil.copy(src=os.path.join(dl.__path__[0], 'assets', 'code_server', 'launch.json'),
                    dst=os.path.join(root_dir, '.vscode', 'launch.json'))
        shutil.copy(src=os.path.join(dl.__path__[0], 'assets', 'code_server', 'settings.json'),
                    dst=os.path.join(root_dir, '.vscode', 'settings.json'))


def get_container(client):
    try:
        container = client.containers.get(container_id=DOCKER_CONTAINER_NAME)
    except Exception:
        container = None
    return container


def start_session():
    try:
        import docker
    except (ImportError, ModuleNotFoundError):
        logger.error(
            'Import Error! Cant import "docker". Must install docker package for local development. run "pip install docker"')
        raise

    try:
        client = docker.from_env()
        client.ping()
    except Exception:
        raise RuntimeError(
            'Cannot communicate with docker daemon. Make sure everything is up and ready (docker client ping)'
        ) from None
    copy_files_to_docker_container()
    logger.info('Starting local development session')
    development = dl.client_api.state_io.get('development')
    port = development['port']
    docker_image = development['docker_image']
    hostname = f"http://localhost:{port}"
    logger.info(f'Starting docker image: {docker_image}, to {hostname}')

    need_to_create_container = True
    container = get_container(client=client)
    if container is not None:
        if not any([tag == docker_image for tag in container.image.tags]):
            # container with different image already running - delete it
            logger.info(f'Found a running image: {container.image.tags!r}, replacing to {docker_image!r}')
            container.stop()
            container.remove()
            need_to_create_container = True
        else:
            # container with SAME image already running - verify is running
            need_to_create_container = False

    if need_to_create_container:
        logger.info(f'Creating a container from docker image: {docker_image}')
        container = client.containers.run(docker_image,
                                          name=DOCKER_CONTAINER_NAME,
                                          tty=True,
                                          volumes={os.getcwd(): {'bind': "/tmp/app", 'mode': 'rw'}},
                                          ports={port: port},
                                          detach=True,
                                          command='/bin/bash')

    logger.info('Installing vscode on in the docker container')
    container = client.containers.get(container_id=DOCKER_CONTAINER_NAME)
    if container.status in "exited":
        container.start()
    elif container.status in "paused":
        container.unpause()

    resp = container.exec_run(
        cmd=f'/tmp/app/.dataloop/code_server/installation.sh {port}',
        detach=True,
        tty=True)
    spinner = spinning_cursor()
    while True:
        try:
            resp = requests.get(hostname, verify=False, timeout=0.5)
            success = resp.ok
        except Exception:
            success = False
        # write spinner
        sys.stdout.write(f'\r{next(spinner)}')
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')

        # check response to break
        if success:
            logger.info(f'VScode server is up! {hostname}')
            break

    # open webbrowser to debug
    import webbrowser
    webbrowser.open(url=hostname, new=2, autoraise=True)


def pause_session():
    try:
        import docker
    except (ImportError, ModuleNotFoundError):
        logger.error(
            'Import Error! Cant import "docker". Must install docker package for local development. run "pip install docker"')
        raise

    try:
        client = docker.from_env()
        client.ping()
    except Exception:
        raise RuntimeError(
            'Cannot communicate with docker daemon. Make sure everything is up and ready (docker client ping)'
        ) from None

    container = get_container(client)
    if container is not None:
        container.pause()
    logger.info('Local development session paused')


def stop_session():
    try:
        import docker
    except (ImportError, ModuleNotFoundError):
        logger.error(
            'Import Error! Cant import "docker". Must install docker package for local development. run "pip install docker"')
        raise

    try:
        client = docker.from_env()
        client.ping()
    except Exception:
        raise RuntimeError(
            'Cannot communicate with docker daemon. Make sure everything is up and ready (docker client ping)'
        ) from None

    container = get_container(client=client)
    if container is not None:
        container.stop()
    logger.info('Local development session stopped')
