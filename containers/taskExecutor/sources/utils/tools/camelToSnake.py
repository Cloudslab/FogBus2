from re import sub


def camelToSnake(name):
    # https://stackoverflow.com/questions/1175208
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
