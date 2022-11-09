class JsonUtils:
    @staticmethod
    def get_if_absent(value, default=None):
        if value is None:
            if default is None:
                value_type = type(value)
                if value_type == dict:
                    default = {}
                elif value_type == list:
                    default = []
                else:
                    default = ''
            value = default
        return value
