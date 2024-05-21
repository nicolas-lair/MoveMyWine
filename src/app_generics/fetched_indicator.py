from dataclasses import dataclass


@dataclass
class FetchedIndicator:
    retrieved: bool
    valid_date: bool = False
    value: float = 1.0
