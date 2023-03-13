def clining_str_with_float(text: str) -> str:
    result = text.strip().replace(',', '.', 1)
    return result

def isfloat(text: str) -> bool:
    text = clining_str_with_float(text)
    try:
        float(text)
    except ValueError:
        return False
    return True