from typing import (Iterable, Union, Pattern, Dict, List, Tuple, Optional, Callable, Sequence)
import re

from weak_supervision.utils import compile_regex_list

from spacy.tokens import Span, Doc

from skweak.base import SpanAnnotator
from skweak import utils

"""
This is a much genral version of the TemplateAnnotator class. It is intended for use when the
tokenisation is word or subword based. It also works for character based tokenisation.
"""


def make_rules(template:str, patterns: Dict[str,List[Pattern]]) -> Iterable[Tuple[Callable[[str],bool],Optional[str]]]:
    """ Comvert a template and a dictionary of LABEL:Pattern into an array of functions returning bool
    and (optionally) a label to apply
    """

    # expression matches text between <> (a pattern key) and text between >< (literal text)
    # Need to also consider start/end of string, and two adjacent patterns (<><>)
    for match in re.finditer(r'(?<=>)([^<]+)|^([^<]+?)(?=[<])|(?<=<)(.+?)(?=>)', template):
        if match.group(3):  # TODO: should use named match groups here!
            # Match is a template argument, lookup and compile associated expression
            label = match.group(3)
            pattern = compile_regex_list(patterns[label], flags=re.IGNORECASE)
            expr = lambda text, pattern=pattern: re.match(pattern, text) # need to explicity pass pattern as a default
            yield (expr, label if label!='*' else None)                  # * is reserved for wildcard matches
        elif match.group(1):
            # Match is a raw string
            expr = lambda text, pattern=match.group(1): text==pattern
            yield (expr, None)
        elif match.group(2):
            # Match is a raw string
            expr = lambda text, pattern=match.group(2): text==pattern
            yield (expr, None)

def match(rules, tokens, n=0, spans=(), max_span_width=None) -> Iterable[Iterable[Tuple[int,int,str,str]]]:
    """ Recusively match rule[n] to tokens and store in list of spans

        If each rule is matched, and all tokens consumed than list of
        matched spans in returned. Multiple sequences are returned as
        there could be multiple ways of matching any given string to
        a template
    """
    max_width = max_span_width or len(tokens)+1
    if n >= len(rules): # no more rules
        if tokens==[]:  # all tokens matched
            yield spans
    else:
        rule, label = rules[n]

        # special case because wildcard rule (*) must match zero length string 
        # i.e. Drivers.CN_MCC_01_B_BASEMENT.Elect_Meter_27.points.Total KW with template <*>.<*><EQUIP><*>.points.<*>
        # without zero match resutls in Elect_Meter_2 being only EQUIP candidate since following * swallows the 7
        if rule('') and len(tokens) > 0:
            span = (tokens[0].i, tokens[0].i + 1, label, None)
            yield from match(rules, tokens[0:], n+1, spans=(*spans,span) if label is not None else spans)

        # enumerate all spans from start of tokens
        for end_index in range(min(max_width,len(tokens))): 
            text = "".join(token.text_with_ws for token in tokens[:end_index + 1])

            if rule(text): # if potential match then recurse
                span = (tokens[0].i, tokens[end_index].i + 1, label, text)
                # need to be careful not to modified inplace the spans tuple inside this loop!
                yield from match(rules, tokens[end_index + 1:], n+1, spans=(*spans,span) if label is not None else spans)


class TemplateAnnotator(SpanAnnotator):
    """
    Enumerate all spans that match provided template. Template is a string of the form
    <EQUIP>.<POINT> where text in <> represets labelled spans and other text represents
    literals. For each <XXX> a series of regular expressions are matched.
    """
    def __init__(
        self, 
        name: str, 
        template:str, 
        patterns: Dict[str,List[Pattern]],
        to_exclude: Sequence[str] = (), 
        max_span_width: int = None,
        ):
        super().__init__(name)
        self.rules = list(make_rules(template, patterns))
        self.max_span_width = max_span_width
        self.add_incompatible_sources(to_exclude)

    def __call__(self, doc: Doc) -> Doc:

        # We start by clearing all existing annotations
        doc.spans[self.name] = []

        spans = []

        # And we look at all suggested spans
        for start, end, label in self.find_spans(doc):

            # We only add the span if it is compatible with other sources
            if self._is_allowed_span(doc, start, end):
                span = Span(doc, start, end, label)
                spans.append(span)

        # longest non-overlapping spans
        spans = utils._remove_overlaps(spans)
        doc.spans[self.name].extend(spans)

        return doc

    def find_spans(self, doc: Doc) -> Iterable[Tuple[int, int]]:
        # return all matching candidate spans
        tokens = [token for token in doc]
        max_length = self.max_span_width or len(doc)
        
        # generate list of list of spans
        matches = set(match(self.rules, tokens, max_span_width=max_length))
        for span in matches:
            # each match is a sequence of spans
            for start_index, end_index, label, _ in span:
                yield (start_index, end_index, label)
