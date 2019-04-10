

def get_value_from_context(params, context, name=None):
    if isinstance(params, list):
        if name is None:
            raise ValueError('"name" must be defined when searching in a list of inputs')
    elif isinstance(params, dict):
        name = params['name']
        params = [params]
    else:
        raise ValueError('unknown "params" type')

    output = None

    for param in params:
        if 'by' not in param:
            param['by'] = 'ref'

        if param['name'] == name:
            if param['by'] == 'val':
                output = param['from']
            elif param['by'] == 'ref':
                for key, val in context.items():
                    if key == param['from']:
                        output = val
            else:
                raise ValueError('unknown "by" value: %s' % param['by'])
    return output
