from itertools import product

def similarity_score(a, b):
    return 3 if a == b else - 3

def gap_penalty(gap_length):
    return 2 * gap_length

def scoring_matrix(a, b):
    """Generate entries in the scoring matrix of the Smith-Waterman algorithm
    for sequences a and b.

    >>> list(scoring_matrix('TGTTACGG', 'GGTTGACTA')) # doctest: +NORMALIZE_WHITESPACE
    [0, 3, 1, 0, 0, 0, 3, 3,
     0, 3, 1, 0, 0, 0, 3, 6,
     3, 1, 6, 4, 2, 0, 1, 4,
     3, 1, 4, 9, 7, 5, 3, 2,
     1, 6, 4, 7, 6, 4, 8, 6,
     0, 4, 3, 5, 10, 8, 6, 5,
     0, 2, 1, 3, 8, 13, 11, 9,
     3, 1, 5, 4, 6, 11, 10, 8,
     1, 0, 3, 2, 7, 9, 8, 7]

    >>> list(scoring_matrix('ba', 'abac')) # doctest: +NORMALIZE_WHITESPACE
    [0, 3,
     3, 1,
     1, 6,
     0, 4]
    """
    def sources(pos, scores):
        column, row = pos
        yield (scores.get((column - 1, row - 1), 0)
               + similarity_score(a[column], b[row])
        ) # diag
        yield max(scores.get((column, row - gap), 0)
                  - gap_penalty(gap)
                  for gap in range(1, row + 2)
        ) # top
        yield max(scores.get((column - gap, row), 0)
                  - gap_penalty(gap)
                  for gap in range(1, column + 2)
        ) # left
        yield 0 # default

    scores = {}
    # Generate row-wise for easier docstring formatting.
    for row, column in product(range(len(b)), range(len(a))):
        score = max(sources((column, row), scores))
        scores[column, row] = score
        yield score
