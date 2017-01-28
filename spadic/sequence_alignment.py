from collections import namedtuple
from itertools import product

def similarity_score(a, b):
    return 3 if a == b else - 3

def gap_penalty(gap_length):
    return 2 * gap_length

ScoringEntry = namedtuple('ScoringEntry', 'pos source score')

def scoring_matrix(a, b):
    """Generate entries in the scoring matrix of the Smith-Waterman algorithm
    for sequences a and b.

    >>> entries = scoring_matrix('ba', 'abac')
    >>> list((e.pos, e.source, e.score) for e in entries) # doctest: +NORMALIZE_WHITESPACE
    [((0, 0), None,   0), ((1, 0), 'diag', 3),
     ((0, 1), 'diag', 3), ((1, 1), 'top',  1),
     ((0, 2), 'top',  1), ((1, 2), 'diag', 6),
     ((0, 3), None,   0), ((1, 3), 'top',  4)]
    """
    def sources(pos, scores):
        column, row = pos
        yield ScoringEntry(
            score=(scores.get((column - 1, row - 1), 0)
                   + similarity_score(a[column], b[row])
                  ),
            source='diag', pos=pos
        )
        yield ScoringEntry(
            score=max(scores.get((column, row - gap), 0)
                      - gap_penalty(gap)
                      for gap in range(1, row + 2)),
            source='top', pos=pos
        )
        yield ScoringEntry(
            score=max(scores.get((column - gap, row), 0)
                      - gap_penalty(gap)
                      for gap in range(1, column + 2)),
            source='left', pos=pos
        )
        yield ScoringEntry(
            score=0,
            source=None, pos=pos
        )

    scores = {}
    # Generate row-wise for easier docstring formatting.
    for row, column in product(range(len(b)), range(len(a))):
        entry = max(sources((column, row), scores), key=lambda e: e.score)
        scores[column, row] = entry.score
        yield entry
