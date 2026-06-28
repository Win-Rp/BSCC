def normalize_base_url(value: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    return normalized.rstrip("/")


def join_base_url(base_url: str, path: str) -> str:
    normalized_base = normalize_base_url(base_url)
    normalized_path = "/" + path.lstrip("/")
    if not normalized_base:
        return ""
    return f"{normalized_base}{normalized_path}"
