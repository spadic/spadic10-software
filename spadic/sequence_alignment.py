from itertools import product

def similarity_score(a, b):
    return 3 if a == b else - 3

def gap_penalty(gap_length):
    return 2 * gap_length

def scoring_matrix(a, b):
    """Return the scoring matrix of the Smith-Waterman algorithm
    for sequences a and b.

    >>> scoring_matrix('TGTTACGG', 'GGTTGACTA') # doctest: +NORMALIZE_WHITESPACE
    [[0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 3, 1, 0, 0, 0, 3, 3],
     [0, 0, 3, 1, 0, 0, 0, 3, 6],
     [0, 3, 1, 6, 4, 2, 0, 1, 4],
     [0, 3, 1, 4, 9, 7, 5, 3, 2],
     [0, 1, 6, 4, 7, 6, 4, 8, 6],
     [0, 0, 4, 3, 5, 10, 8, 6, 5],
     [0, 0, 2, 1, 3, 8, 13, 11, 9],
     [0, 3, 1, 5, 4, 6, 11, 10, 8],
     [0, 1, 0, 3, 2, 7, 9, 8, 7]]

    >>> scoring_matrix('ba', 'abac') # doctest: +NORMALIZE_WHITESPACE
    [[0, 0, 0],
     [0, 0, 3],
     [0, 3, 1],
     [0, 1, 6],
     [0, 0, 4]]
    """
    def sources(pos, scores):
        column, row = pos
        yield (scores[row - 1][column - 1]
               + similarity_score(a[column - 1], b[row - 1])
        ) # diag
        yield max(scores[row - gap][column]
                  - gap_penalty(gap)
                  for gap in range(1, row + 1)
        ) # top
        yield max(scores[row][column - gap]
                  - gap_penalty(gap)
                  for gap in range(1, column + 1)
        ) # left
        yield 0 # default

    scores = [[0] * (len(a) + 1) for _ in range(len(b) + 1)]
    for row, column in product(range(1, len(b) + 1), range(1, len(a) + 1)):
        scores[row][column] = max(sources((column, row), scores))
    return scores
