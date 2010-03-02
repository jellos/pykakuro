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

def test_two():
  solution = [0, 0, (0, 23), (0, 21), 0,
              0, (8, 15), 1, 7, 0,
              (8, 0), 1, 2, 5, 0,
              (27, 0), 7, 8, 9, 3,
              (5, 0), 2, 3, 0, 0,
              (14, 0), 5, 9, 0, 0,
              0, 0, 0, 0, 0]

  assert solution == kakuro.solve(puzzles.two, 5)

def test_three():
  solution = [0, (0, 23), (0, 30), 0, 0, (0, 27), (0, 12), (0, 16),
             (16, 0), 9, 7, 0, (24, 17), 8, 7, 9,
             (17, 0), 8, 9, (29, 15), 8, 9, 5, 7,
             (35, 0), 6, 8, 5, 9, 7, (0, 12), 0,
             0, (7, 0), 6, 1, (8, 7), 2, 6, (0, 7),
             0, (0, 11), (16, 10), 4, 6, 1, 3, 2,
             (21, 0), 8, 9, 3, 1, (5, 0), 1, 4,
             (6, 0), 3, 1, 2, 0, (3, 0), 2, 1]

  assert solution == kakuro.solve(puzzles.three, 8)
