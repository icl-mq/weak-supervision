from typing import Iterable, Union, Pattern
import re

def compile_regex_list(entries: Iterable[Union[str, Pattern]], flags=0) -> Pattern:
    """Compile a sequence of rules into a regex object.

    Each entry is anchored to prevent partial matches
    """
    expression = "|".join(["^" + piece + "$" for piece in entries if piece.strip()])  # type: ignore[operator, union-attr]
    return re.compile(expression, flags)