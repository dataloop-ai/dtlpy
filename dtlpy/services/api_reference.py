class ApiReference(object):

    def __init__(self):
        self.references = {'paths': dict()}

    def add(self, path, method):
        def wrapper(f):
            if path not in self.references['paths']:
                self.references['paths'][path] = dict()
            if method not in self.references['paths'][path]:
                self.references['paths'][path][method] = dict()

            docstring = f.__doc__
            docstring = docstring.split('\n')
            in_code = False

            code_list = list()
            docs_list = list()
            for i_line in range(len(docstring)):
                if '.. code-block::' in docstring[i_line]:
                    in_code = True
                    continue
                if '**Example**' in docstring[i_line]:
                    continue
                if docstring[i_line].startswith('    ') and not docstring[i_line].startswith('        '):
                    in_code = False
                if in_code:
                    code_list.append('{}'.format(docstring[i_line].strip()))
                else:
                    docs_list.append('# {}'.format(docstring[i_line].strip()))
                # assert False
            docstring = '\n'.join(code_list + docs_list)
            self.references['paths'][path][method]['x-codeSamples'] = [{"lang": "Python",
                                                                        "source": docstring}]
            return f

        return wrapper


api_reference = ApiReference()
