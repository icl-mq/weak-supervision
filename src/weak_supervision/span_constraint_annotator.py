from typing import Callable, Iterable, Sequence, Tuple
from spacy.tokens import Span, Doc
from skweak.base import SpanAnnotator
from skweak import utils

class SpanConstraintAnnotator(SpanAnnotator):
    """
    Enumerates all spans up to length `max_span_width` and returns the longest non-overlapping spans. 
    """
    def __init__(
        self, 
        name: str, 
        constraint: Callable[[str], bool], 
        label: str, 
        to_exclude: Sequence[str] = (), 
        max_span_width: int = None,
        prefix_length: int =0,
        suffix_length: int =0,
        ):
        super().__init__(name)
        self.constraint = constraint
        self.label = label
        self.max_span_width = max_span_width
        self.prefix_length = prefix_length
        self.suffix_length = suffix_length
        self.add_incompatible_sources(to_exclude)

    def __call__(self, doc: Doc) -> Doc:

        # We start by clearing all existing annotations
        doc.spans[self.name] = []

        spans = []

        # And we look at all suggested spans
        for start, end, in self.find_spans(doc):

            # We only add the span if it is compatible with other sources
            if self._is_allowed_span(doc, start, end):
                span = Span(doc, start, end, self.label)
                spans.append(span)

        # longest non-overlapping spans
        spans = utils._remove_overlaps(spans)
        doc.spans[self.name].extend(spans)

        return doc

    def find_spans(self, doc: Doc) -> Iterable[Tuple[int, int]]:
        # return all matching candidate spans
        tokens = utils.get_tokens(doc)
        max_length = self.max_span_width or len(doc)
        min_length = 1

        for start_index in range(len(tokens)):
            last_end_index = min(start_index + max_length, len(tokens))
            first_end_index = min(start_index + min_length - 1, len(tokens))
            for end_index in range(first_end_index, last_end_index):
                text = "".join(word.text_with_ws for word in doc[start_index:end_index+1])
                text = text.strip()

                #print(text)
                if self.constraint(text):
                    #print(text,start_index,end_index+1)
                    # suffix and prefix length enable us to match on characters either side of entity
                    # but then only return the actual entity span
                    yield start_index+self.prefix_length ,end_index-self.suffix_length+1


