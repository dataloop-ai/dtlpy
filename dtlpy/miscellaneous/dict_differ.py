import dictdiffer
import logging

logger = logging.getLogger(name=__name__)


# noinspection PyPep8Naming
class DictDiffer:

    @staticmethod
    def diff(origin, modified):
        TYPE = 0
        FIELD = 1
        LIST = 2

        diffs = dict()
        dict_diff = list(dictdiffer.diff(origin, modified))
        for diff in dict_diff:
            field_pointer = DictDiffer.get_field_path(diffs=diffs, path=diff[FIELD], diff_type=diff[TYPE])
            if diff[TYPE] == 'add':
                for addition in diff[LIST]:
                    field_pointer[addition[0]] = addition[1]

            elif diff[TYPE] == 'remove':
                for deletion in diff[LIST]:
                    field_pointer[deletion[0]] = None

            elif diff[TYPE] == 'change':
                change = diff[LIST]
                field = diff[FIELD]
                if not isinstance(field, list):
                    field = field.split('.')
                field_pointer[field[-1]] = change[1]
        return diffs

    @staticmethod
    def get_field_path(diffs, path, diff_type):
        field_pointer = diffs
        if not isinstance(path, list):
            path = path.split('.')

        if len(path) > 1 or diff_type != 'change':
            for level in path:
                if diff_type == 'change' and level == path[-2]:
                    if level not in field_pointer:
                        field_pointer[level] = dict()
                    field_pointer = field_pointer[level]
                    break
                if level in field_pointer:
                    field_pointer = field_pointer[level]
                else:
                    field_pointer[level] = dict()
                    field_pointer = field_pointer[level]

        return field_pointer
