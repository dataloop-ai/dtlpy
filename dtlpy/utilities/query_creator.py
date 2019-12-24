

def query_value(param):
    if isinstance(param, list):
        return ','.join([str(val) for val in param])
    else:
        return param


def create_query(url, params):
    is_first = True
    for param in params:
        if params[param] is not None:
            if is_first:
                url = '{}?{}={}'.format(url, param, query_value(params[param]))
                is_first = False
            else:
                url = '{}&{}={}'.format(url, param, query_value(params[param]))

    return url
