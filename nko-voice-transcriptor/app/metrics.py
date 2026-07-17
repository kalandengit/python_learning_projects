"""Dependency-free ASR word and character error rates."""

from __future__ import annotations


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, expected in enumerate(reference, 1):
        current = [i]
        for j, actual in enumerate(hypothesis, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (expected != actual))
            )
        previous = current
    return previous[-1]


def error_rate(reference: str, hypothesis: str, *, characters: bool = False) -> float:
    if characters:
        ref = list("".join(reference.casefold().split()))
        hyp = list("".join(hypothesis.casefold().split()))
    else:
        ref = reference.casefold().split()
        hyp = hypothesis.casefold().split()
    return edit_distance(ref, hyp) / max(1, len(ref))
