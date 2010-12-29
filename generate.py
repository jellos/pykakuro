#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Uses multiprocessing pool to generate and test lots of puzzles. Puzzles
# which take too long to solve are discarded.

DISCARD_TIMEOUT = 5
POOL_SIZE = 4
PUZZLE_COUNT = 100

import kakuro
from multiprocessing import Pool, TimeoutError

def f(i):
  k = kakuro.gen_random(10, 10, seed=i, is_solved=False)
  success = k.solve(timeout=DISCARD_TIMEOUT, timeout_exception=False)
  if success:
    k.check_solution()
    return i, k
  else:
    return i, None

pool = Pool(POOL_SIZE)

for seed, puzzle in pool.imap_unordered(f, range(PUZZLE_COUNT), 10):
  print seed, repr(puzzle)
