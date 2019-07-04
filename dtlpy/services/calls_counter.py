from .cookie import CookieIO


class CallsCounter:
    def __init__(self, filepath):
        self.io = CookieIO(filepath)
        self.state = 'off'
        self.number = 0
        self.load()

    def add(self):
        if self.state == 'on':
            self.load()
            self.number += 1
            self.save()

    def reset(self):
        self.number = 0
        self.save()

    def save(self):
        self.io.put('calls_counter', {'state': self.state,
                                      'number': self.number})

    def on(self):
        self.state = 'on'
        self.save()

    def off(self):
        self.state = 'off'
        self.save()

    def on_exit(self):
        self.save()

    def load(self):
        calls = self.io.get('calls_counter')
        if calls is None:
            # not set in cookie - set default
            calls = {'state': 'off',
                     'number': 0}
            self.io.put('calls_counter', calls)
        self.state = calls['state']
        self.number = calls['number']
