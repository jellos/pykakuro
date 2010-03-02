#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kakuro
import puzzles

def test_one():
  solution = [0, 0, (0, 7), (0, 6),
              0, (4, 4), 1, 3,
              (7, 0), 1, 4, 2,
              (6, 0), 3, 2, 1]

  assert solution == kakuro.solve(puzzles.one, 4)
