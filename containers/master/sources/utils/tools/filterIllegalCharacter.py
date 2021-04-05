import re


def filterIllegalCharacter(string: str):
    filtered = re.sub(r'[^a-zA-Z0-9_.-]*', '', string)
    return filtered
