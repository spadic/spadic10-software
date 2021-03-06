from collections import namedtuple
from itertools import product

def similarity_score(a, b, weight):
    return weight * (1 if a == b else -1)

def gap_penalty(gap_length, weight):
    return weight * gap_length

ScoringEntry = namedtuple('ScoringEntry', 'pos source score')

def scoring_matrix(a, b, similarity_weight, gap_weight):
    """Generate entries in the scoring matrix of the Smith-Waterman algorithm
    for sequences a and b, given the weights for the similarity score and the
    gap penalty.

    >>> entries = scoring_matrix('ba', 'abac', 3, 2)
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
                   + similarity_score(a[column], b[row],
                                      weight=similarity_weight)
                  ),
            source='diag', pos=pos
        )
        yield ScoringEntry(
            score=max(scores.get((column, row - gap), 0)
                      - gap_penalty(gap, weight=gap_weight)
                      for gap in range(1, row + 2)),
            source='top', pos=pos
        )
        yield ScoringEntry(
            score=max(scores.get((column - gap, row), 0)
                      - gap_penalty(gap, weight=gap_weight)
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

def align_local(a, b, similarity_weight=3, gap_weight=2):
    """Generate pairs of indexes into sequences a and b indicating local
    alignment.

    Implements the Smith-Waterman algorithm
    (see https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm).

    >>> list(align_local('', 'abc')) == list(align_local('abc', '')) == []
    True
    >>> list(align_local('abc', 'abc'))
    [(0, 0), (1, 1), (2, 2)]
    >>> list(align_local('TGTTACGG', 'GGTTGACTA'))
    [(1, 1), (2, 2), (3, 3), (4, 5), (5, 6)]
    """
    # Empty sequences would not be handled later.
    if not (a and b):
        return iter([])
    # Equal sequences would be handled later as well, but this is a shortcut.
    if a == b:
        return zip(range(len(a)), range(len(b)))

    entries = list(scoring_matrix(a, b, similarity_weight, gap_weight))
    def traceback():
        column, row = max(entries, key=lambda e: e.score).pos
        trace = {e.pos: e.source for e in entries}
        for source in iter(lambda: trace.get((column, row), None), None):
            if source == 'diag':
                yield column, row
            column, row = {
                'diag': (column - 1, row - 1),
                'top': (column, row - 1),
                'left': (column - 1, row),
            }[source]
    return reversed(list(traceback()))
