import behave
import random
import dtlpy as dl
import subprocess
import os
import shutil


@behave.then(u'Version is correct')
def step_impl(context):
    output = context.out.decode('utf-8')
    assert context.dl.__version__ in output


@behave.then(u'"{msg}" in output')
def step_impl(context, msg):
    msg = msg.replace('<random>', context.random)
    output = context.out.decode('utf-8')
    assert msg.lower() in output.lower()
