"""Small statistics for counts: a Wilson interval and an exact McNemar test."""

from math import comb, sqrt


def wilson_interval(successes: int, total: int, z: float = 1.959964) -> tuple[float, float]:
    """A 95% Wilson score interval for a proportion."""
    share = successes / total
    denominator = 1 + z**2 / total
    center = (share + z**2 / (2 * total)) / denominator
    margin = z * sqrt(share * (1 - share) / total + z**2 / (4 * total**2)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def paired_difference_interval(first_only: int, second_only: int, total: int, z: float = 1.959964):
    """A 95% interval, in cases, for how many more the first method got right than the second."""
    difference = first_only - second_only
    margin = z * sqrt(first_only + second_only - difference**2 / total)
    return difference - margin, difference + margin


def exact_mcnemar(first_only: int, second_only: int) -> float:
    """The two-sided exact McNemar p-value, from the counts where only one method was right."""
    total = first_only + second_only
    tail = sum(comb(total, k) for k in range(min(first_only, second_only) + 1))
    return min(1.0, 2 * tail / 2**total)
