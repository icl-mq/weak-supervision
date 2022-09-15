from typing import (Iterable, Union, Pattern, Dict, List, Tuple, Optional, Callable, Sequence)
import re

from weak_supervision.utils import compile_regex_list

from spacy.tokens import Span, Doc

from skweak.base import SpanAnnotator
from skweak import utils

"""
This is a much simplified version of the TemplateAnnotator class. It is intended for use when the
tokenisation is character based, the original TemplateAnnotator class will work for arbitrary 
tokenisation
"""

def expand_text(t):
    """
    Simple regular expression based escaping (WIP)
    """
    # expand * to non-greedy match, allow | and re.escape  ?
    return t.replace(".","\.").replace("*",".*?")

def expand_template(template:str, patterns: Dict[str,List[Pattern]], flags=0) -> Pattern:
    """ Expand a template into a compiled expression, and a map between match groups and labels
    """

    def _iter():
        i = 1
        for match in re.finditer(r'(?<=>)([^<]+)|^([^<]+?)(?=[<])|(?<=<)(.+?)(?=>)', template):
            if match.group(3):  # TODO: should use named match groups here!
            # Match is a template argument, lookup and compile associated expression
                label = match.group(3)
                key = f"G{i}"
                expression = f'(?P<{key}>{"|".join([piece for piece in patterns[label] if piece.strip()])})'
                i += 1
                yield (expression,key,label)                  
            elif match.group(1):
                expression = expand_text(match.group(1))
                yield (expression,None,None)
            elif match.group(2):
                expression = expand_text(match.group(2))
                yield (expression,None,None)
    
    expression = ""
    labels = {}
    for fragment,key,label in _iter():
        expression += fragment
        if key:
            labels[key] = label
    
    return re.compile("^" + expression + "$", flags), labels

class TemplateAnnotator(SpanAnnotator):
    """
    Enumerate all spans that match provided template. Template is a pattern of the form
    <EQUIP>.<POINT> where text in <> is expanded by replacing <PATTERN> with a named
    match group consisting of expressions from patterns[PATTERN] joined using '|'
    """
    def __init__(
        self, 
        name: str, 
        template:str, 
        patterns: Dict[str,List[Pattern]],
        to_exclude: Sequence[str] = (), 
        flags: int = re.IGNORECASE
        ):
        super().__init__(name)
        self.add_incompatible_sources(to_exclude)

        self.expression, self.labels = expand_template(template, patterns, flags=flags)

    def __call__(self, doc: Doc) -> Doc:
        spans = []
        for start, end, label in self.find_spans(doc):

            # We only add the span if it is compatible with other sources
            if self._is_allowed_span(doc, start, end):
                span = Span(doc, start, end, label)
                spans.append(span)

        # longest non-overlapping spans
        spans = utils._remove_overlaps(spans)
        doc.spans[self.name] = spans

        return doc

    def find_spans(self, doc: Doc) -> Iterable[Tuple[int, int]]:
        # return all matching candidate spans
        tokens = [token for token in doc]
        for match in re.finditer(self.expression, doc.text):
            for key,label in self.labels.items():
                # Attempt to align character spans onto tokens
                span = match.span(key)
                start_idx = None
                end_idx = None
                for i,token in enumerate(tokens): 
                    if token.idx == span[0]:
                        start_idx = i
                    if token.idx + len(token.text) == span[1]:
                        end_idx = i + 1

                    if (start_idx is not None) and (end_idx is not None):
                        yield (start_idx, end_idx, label)
                        break
