def clamp(min_value: float, max_value: float, value: float) -> float:
    """Clamps a value between a minimum and maximum value."""
    if value < min_value:
        return min_value

    if value > max_value:
        return max_value

    return value


def closest(lst: list, k: int) -> int:
    """Get the closest value in a list."""
    try:
        return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - k))]
    except ValueError:
        return k
