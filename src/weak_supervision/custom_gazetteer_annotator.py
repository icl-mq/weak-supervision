from typing import Sequence, List, Dict

from skweak import gazetteers, utils
from spacy.tokens import Span

class CustomGazetteerAnnotator(gazetteers.GazetteerAnnotator):
    """
    Gazetteer with same valid match implementation as span annotators
    """
    def __init__(self, name: str, tries: Dict[str, 'gazetteers.Trie'], case_sensitive: bool = True, 
                lookahead: int = 10, to_exclude: Sequence[str] = ()):
        super().__init__(name, tries, case_sensitive, lookahead, additional_checks=True)
        self.incompatible_sources = to_exclude

    def _is_valid_match(self, match_span: Span, ent_tokens: List[str]) -> bool:
        doc = match_span.doc
        for other_source in self.incompatible_sources:

            intervals = sorted((span.start, span.end) for span in
                            doc.spans.get(other_source, []))

            # Performs a binary search to efficiently detect overlapping spans
            start_search, end_search = utils._binary_search(
                match_span.start, match_span.end, intervals)
            for interval_start, interval_end in intervals[start_search:end_search]:
                if match_span.start < interval_end and match_span.end > interval_start:
                    return False
        return True