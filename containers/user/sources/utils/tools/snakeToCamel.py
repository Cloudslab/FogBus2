def snakeToCamel(snakeStr: str):
    if snakeStr == snakeStr.lower():
        return snakeStr.upper()
    # https://stackoverflow.com/questions/19053707
    components = snakeStr.split('_')
    return ''.join(x.title() for x in components)
