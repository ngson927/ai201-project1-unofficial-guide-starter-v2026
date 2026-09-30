"""
The relevance gate.

This runs *before* the model does. It looks at how close the best retrieved
chunk actually is, and if nothing came back close enough it refuses the
question outright.

Why this exists as its own step, rather than just asking the model nicely to
admit when it doesn't know: if you only ask nicely, it will sometimes ignore
you and write something confident and wrong. Those answers are much harder to
catch than obvious errors. Deciding in your own code when there's nothing worth
answering from is more reliable than hoping.

You keep the polite instruction too — it's in generate.py — but as a second
layer. The gate catches the clear misses; the prompt catches the near ones.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache

import config
from store import Result

REFUSAL = "I don't have enough information about that."


@lru_cache(maxsize=8)
def _corpus_vocabulary(corpus: str | None = None) -> frozenset:
    """Every word that appears anywhere in the corpus, lowercased."""
    from ingest import load_documents

    words: set[str] = set()
    for doc in load_documents(corpus):
        words |= set(re.findall(r"[A-Za-z0-9]+", doc.text.lower()))
    return frozenset(words)


def unknown_proper_nouns(question: str, corpus: str | None = None) -> list[str]:
    """
    Capitalised words in the question that appear nowhere in the corpus.

    This exists because of a measured weakness in the embedding. It scores a
    question mostly by its shape and barely at all by the entities in it:
    holding the frame fixed and swapping only the place name, "the best time to
    visit Halden Bay" scores 0.226 while Tokyo, Zurich, Reykjavik and
    Ouagadougou all land between 0.606 and 0.643 — a band 0.037 wide, with
    Ouagadougou scoring better than Tokyo. The name is doing almost no work, so
    a question about a place I have never heard of still lands under the cutoff
    on the strength of its frame alone.

    Distance cannot separate those, because legitimate vague questions about my
    own region score 0.609 to 0.722 and these score 0.575 to 0.643. So this
    checks the entity directly instead.

    The first word is skipped because it is capitalised by sentence position
    rather than by being a name. A question that opens with a proper noun —
    "Tokyo in November, what is it like?" — slips through; that is a known
    limitation, not an oversight.
    """
    vocabulary = _corpus_vocabulary(corpus)
    tokens = re.findall(r"\b[A-Za-z][A-Za-z]+\b", question)
    return [
        token
        for position, token in enumerate(tokens)
        if position > 0 and token[0].isupper() and token.lower() not in vocabulary
    ]


@dataclass
class GateDecision:
    passed: bool
    best_distance: float
    threshold: float
    unknown_terms: list[str] = field(default_factory=list)

    @property
    def explanation(self) -> str:
        if self.unknown_terms:
            names = ", ".join(self.unknown_terms)
            return (
                f"best distance {self.best_distance:.3f} is under the "
                f"{self.threshold} cutoff, but {names} "
                f"{'appear' if len(self.unknown_terms) > 1 else 'appears'} "
                f"nowhere in the corpus — refusing"
            )
        if self.passed:
            return (
                f"best distance {self.best_distance:.3f} "
                f"is under the {self.threshold} cutoff"
            )
        return (
            f"best distance {self.best_distance:.3f} "
            f"is over the {self.threshold} cutoff — refusing"
        )


def check(
    results: list[Result],
    threshold: float | None = None,
    question: str | None = None,
    corpus: str | None = None,
) -> GateDecision:
    """
    Decide whether the retrieved chunks are close enough to answer from.

    Remember: LOWER distance is better. A question passes when its best chunk
    is *under* the threshold.

    Two tests, not one. Distance catches questions whose subject matter is
    foreign — a question about Rust or the World Cup matches no frame I have,
    so it scores 0.86 or higher and is stopped here. `unknown_proper_nouns`
    catches the opposite case: a question shaped exactly like one my guides
    answer, about a place they have never mentioned. Passing `question` turns
    the second test on; without it this behaves as it always did.
    """
    threshold = config.THRESHOLD if threshold is None else threshold

    if not results:
        return GateDecision(passed=False, best_distance=1.0, threshold=threshold)

    best = min(r.distance for r in results)
    unknown = unknown_proper_nouns(question, corpus) if question else []

    return GateDecision(
        passed=best < threshold and not unknown,
        best_distance=best,
        threshold=threshold,
        unknown_terms=unknown,
    )
