import dictdiffer
import logging
from typing import Union

logger = logging.getLogger(name=__name__)
TYPE = 0
FIELD = 1
LIST = 2


class DictDiffer:

    @staticmethod
    def diff(origin, modified):
        diffs = dict()

        dict_diff = list(dictdiffer.diff(origin, modified))
        for i_diff, diff in enumerate(dict_diff):
            modified_field_pointer = modified
            if len(diff[FIELD]) > 0:
                field_pointer, modified_field_pointer, is_list = DictDiffer.get_field_path(
                    diffs=diffs,
                    path=diff[FIELD],
                    diff_type=diff[TYPE],
                    values=diff[LIST],
                    modified_field_pointer=modified_field_pointer
                )
            else:
                field_pointer, modified_field_pointer, is_list = origin, modified, False

            if is_list:
                for i in modified_field_pointer:
                    if i not in field_pointer:
                        field_pointer.append(i)
                continue
            else:
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
    def next_is_list(path: list, i_level: Union[str, int], values):
        if len(path) > (i_level + 1):
            if isinstance(path[i_level + 1], int):
                return True
        elif isinstance(values[0][0], int):
            return True
        return False

    @staticmethod
    def get_field_path(diffs, path, diff_type, modified_field_pointer, values):
        field_pointer = diffs
        if not isinstance(path, list):
            path = path.split('.')

        next_is_list = False
        if len(path) > 1 or diff_type != 'change':
            for i_level, level in enumerate(path):
                next_is_list = DictDiffer.next_is_list(i_level=i_level, path=path, values=values)
                if diff_type == 'change' and level == path[-2]:
                    if level not in field_pointer:
                        if next_is_list:
                            field_pointer[level] = list()
                        else:
                            field_pointer[level] = dict()
                    field_pointer = field_pointer[level]
                    modified_field_pointer = modified_field_pointer[level]
                    break
                if level not in field_pointer:
                    if next_is_list:
                        field_pointer[level] = list()
                    else:
                        field_pointer[level] = dict()
                field_pointer = field_pointer[level]
                modified_field_pointer = modified_field_pointer[level]

                if next_is_list:
                    break

        return field_pointer, modified_field_pointer, next_is_list
