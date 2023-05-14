def build_component_id(separator: str = "-", *args: str) -> str:
    return separator.join(args)
