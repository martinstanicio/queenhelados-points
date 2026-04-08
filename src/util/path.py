def get_path_components(path: str) -> list[str]:
    raw_components = path.split("/")

    resolved_components = [
        component for component in raw_components if component not in ("", ".")
    ]

    return resolved_components
