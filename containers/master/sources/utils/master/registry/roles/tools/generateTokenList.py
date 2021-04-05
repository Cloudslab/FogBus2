from secrets import token_hex as tokenHex


def generateTokenList(length: int):
    tokenList = [tokenHex(32) for _ in range(length)]
    return tokenList
