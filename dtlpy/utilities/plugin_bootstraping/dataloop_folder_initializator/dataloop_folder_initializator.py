import os
from shutil import copyfile
from dtlpy.services import CookieIO

def init_dataloop_folder():
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
    CookieIO.init_local_cookie()