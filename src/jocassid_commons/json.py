
from collections import namedtuple

def json_get(collection, default, *keys):
    """function to extract values from a dict of dicts like what is returned
    by json.load

    collection can be either a mapping or a list.
    keys can be keys (if collection is a mapping)
    or indexes (if collection is a list)"""

    for key in keys:
        if isinstance(collection, str):
            return default
        try:
            collection = collection[key]
        except (KeyError, IndexError, TypeError):
            return default
    return collection


def locate_key(collection, pattern, path_prefix='/'):

    regex_compatible = (str, bytes)
    dict_or_list = (dict, list)

    def of_types(obj, types):
        return any(isinstance(obj, t) for t in types)

    if isinstance(collection, dict):
        search_key = True
        key_value_generator = collection.items()
    elif isinstance(collection, list):
        search_key = False
        key_value_generator = enumerate(collection)
    else:
        raise ValueError(
            f"{type(collection)} {collection!r} is invalid type for locate "
            f"key.  It should be dict or list",
        )

    for key, value in key_value_generator:
        if search_key and of_types(key, regex_compatible):
            if pattern.search(key):
                yield f"{path_prefix}{key}"
        if not of_types(value, dict_or_list):
            continue
        for json_path in locate_key(value, pattern, f"{path_prefix}{key}/"):
            yield json_path


class JsonDiff:

    KEY_LEFT = 1
    KEY_RIGHT = 2
    KEY_BOTH = 3

    COLUMN_SEPARATOR = '  '

    def __init__(self, max_width=80, diff_only=False, indent_size=2):
        self.max_width = max_width
        self.diff_only = diff_only
        self.indent_size = indent_size


    def run(self, json1, json2):
        if isinstance(json1, dict) and isinstance(json2, dict):
            yield from self.compare_dicts(json1, json2)



    def compare_dicts(self, json1, json2, depth=0):
        column_format = self.get_column_format(depth)

        keys1 = sorted(json1.keys())
        keys2 = sorted(json2.keys())
        for i in range(len(keys1) + len(keys2)):

            if keys1 and keys2:
                key1 = keys1[0]
                key2 = keys2[0]
                if key1 < key2:
                    yield from self.show_values(
                        key1,
                        json1[key1],
                        None,
                        self.KEY_LEFT,
                        column_format
                    )
                    keys1.pop(0)
                elif key1 == key2:
                    yield from self.show_values(
                        key1,
                        json1[key1],
                        json2[key2],
                        self.KEY_BOTH,
                        column_format,
                    )
                    keys1.pop(0)
                    keys2.pop(0)
                else:
                    yield from self.show_values(
                        key2,
                        None,
                        json2[key2],
                        self.KEY_RIGHT,
                        column_format
                    )
                    keys2.pop(0)
                continue

            for key1 in keys1:
                yield from self.show_values(
                    key1,
                    json1[key1],
                    None,
                    self.KEY_LEFT,
                    column_format,
                )

            for key2 in keys2:
                yield from self.show_values(
                    key2,
                    None,
                    json2[key2],
                    self.KEY_RIGHT,
                    column_format,
                )

            break

    def get_column_format(self, depth):
        indent_width = self.indent_size * depth
        column_separation = len(self.COLUMN_SEPARATOR) * 2
        column_width = self.max_width - indent_width - column_separation
        if column_width <= 0:
            raise ValueError(f"{column_width=}")
        column_width = column_width // 3
        ColumnFormat = namedtuple(
            'ColumnFormat',
            ['indent', 'column_width']
        )
        return ColumnFormat(' ' * indent_width, column_width)


    def show_values(self, key, value1, value2, key_side, column_format):
        column_width = column_format.column_width

        pieces = [
            column_format.indent,
            repr(key).ljust(column_width),
            self.COLUMN_SEPARATOR
        ]

        if key_side in (self.KEY_LEFT, self.KEY_BOTH):
            pieces.append(repr(value1).ljust(column_width))
        else:
            pieces.append(' ' * column_width)

        pieces.append(self.COLUMN_SEPARATOR)

        if key_side in (self.KEY_RIGHT, self.KEY_BOTH):
            pieces.append(repr(value2).ljust(column_width))
        else:
            pieces.append(' ' * column_width)

        yield "".join(pieces)


def json_diff(json1, json2, max_width=80, diff_only=False, indent_size=2):
    yield from JsonDiff(
        max_width,
        diff_only,
        indent_size,
    ).run(
        json1,
        json2,
    )



