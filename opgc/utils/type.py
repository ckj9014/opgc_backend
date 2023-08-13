def convert_dict_key_lower(data: dict) -> dict:
    """dict Key를 모두 소문자로 변경"""
    if isinstance(data, dict):
        return {k.lower(): convert_dict_key_lower(v) for k, v in data.items()}
    else:
        return data
