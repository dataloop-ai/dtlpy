import behave
import os
import json
import tempfile
import shutil
from .. import fixtures


@behave.when(u'I list all project plugins')
def step_impl(context):
    context.plugins_list = context.project.plugins.list()


@behave.then(u'I receive a list of "{num_plugins}" plugins')
def step_impl(context, num_plugins):
    assert len(context.plugins_list) == int(num_plugins)
