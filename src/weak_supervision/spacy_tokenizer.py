import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_infix_regex
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, HYPHENS

nlp = spacy.blank('en')
infixes = (
            r"[._'-]",
            r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
            r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
            r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
            r"(?<=[{al}])(?=[{au}])|(?<=[{au}])(?=[{au}][{al}])".format(al=ALPHA_LOWER, au=ALPHA_UPPER),
            r"(?<=[{a}])(?=[0-9])".format(a=ALPHA),
)
infix_re = compile_infix_regex(infixes)

nlp.tokenizer = Tokenizer(
                    nlp.vocab, 
                    suffix_search=None,
                    prefix_search=None,
                    infix_finditer=infix_re.finditer,
                    token_match=None)