import fire
from dtlpy import PlatformInterface


class IngestionStage(object):
    def run(self):
        return 'Ingesting! Nom nom nom...'


class Projects(object):
    def __init__(self, platform_interface):
        self.platform_interface = platform_interface

    def list(self, volume=1):
        """
        What to do
        :param volume: inputs
        :return:
        """
        return ' '.join(['Burp!'] * volume)

    def status(self):
        return 'Satiated.'


class DLP(object):
    platform_interface = PlatformInterface()

    def __init__(self):
        self.projects = Projects(self.platform_interface)


if __name__ == '__main__':
    fire.Fire(DLP)
