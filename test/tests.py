#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kakuro
import puzzles

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

# Manually verified solutions to some simple puzzles
solution_1 = (0, 0, (0, 7), (0, 6),
              0, (4, 4), 1, 3,
              (7, 0), 1, 4, 2,
              (6, 0), 3, 2, 1)

solution_2 = (0, 0, (0, 23), (0, 21), 0,
              0, (8, 15), 1, 7, 0,
              (8, 0), 1, 2, 5, 0,
              (27, 0), 7, 8, 9, 3,
              (5, 0), 2, 3, 0, 0,
              (14, 0), 5, 9, 0, 0,
              0, 0, 0, 0, 0)

solution_3 = (0, (0, 23), (0, 30), 0, 0, (0, 27), (0, 12), (0, 16),
             (16, 0), 9, 7, 0, (24, 17), 8, 7, 9,
             (17, 0), 8, 9, (29, 15), 8, 9, 5, 7,
             (35, 0), 6, 8, 5, 9, 7, (0, 12), 0,
             0, (7, 0), 6, 1, (8, 7), 2, 6, (0, 7),
             0, (0, 11), (16, 10), 4, 6, 1, 3, 2,
             (21, 0), 8, 9, 3, 1, (5, 0), 1, 4,
             (6, 0), 3, 1, 2, 0, (3, 0), 2, 1)

solution_4 = (0, 0, 0, 0, 0, 0, (0, 16), (0, 3),
              0, 0, 0, 0, 0, (8, 6), 7, 1,
              0, (0, 16), (0, 6), 0, (14, 30), 3, 9, 2,
              (11, 0), 9, 2, (7, 0), 6, 1, (0, 6), 0,
              (10, 0), 7, 3, (13, 7), 8, 2, 3, (0, 16),
              0, (14, 0), 1, 4, 9, (8, 0), 1, 7,
              0, (0, 4), (9, 17), 2, 7, (11, 0), 2, 9,
              (12, 0), 3, 8, 1, 0, 0, 0, 0,
              (10, 0), 1, 9, 0, 0, 0, 0, 0)

# This is the same solution obtained by
# http://cpark.users.sonic.net/kakuro-python/bk2-13.html so it is probably
# accurate
soln_killer = (
  (0, (0, 24), (0, 28), 0, (0, 14), (0, 33), (0, 13), (0, 8), (0, 39), 0,
   (0, 27), (0, 45), (0, 16), (0, 8), 0, (0, 20), (0, 32), (0, 21), (12, 0),
   7, 5, (16, 43), 1, 3, 4, 2, 6, (30, 0), 8, 9, 6, 7, (11, 10), 8, 1, 2,
   (43, 0), 8, 4, 5, 3, 6, 9, 1, 7, (36, 6), 5, 6, 2, 1, 3, 7, 8, 4, (32, 0),
   9, 8, 6, 2, 7, (22, 19), 5, 4, 2, 3, 7, 1, (11, 11), 2, 5, 3, 1, 0,
   (33, 13), 6, 7, 8, 9, 3, (42, 45), 9, 3, 6, 8, 7, 5, 4, (12, 40), 9, 3,
   (15, 0), 8, 3, 4, (29, 8), 8, 2, 6, 5, 1, 4, 3, (18, 30), 2, 1, 6, 4, 5,
   (11, 0), 5, 2, 3, 1, (24, 10), 7, 9, 8, (18, 0), 1, 5, 9, 3, (22, 12), 9,
   7, 6, 0, (0, 24), (34, 36), 9, 7, 4, 6, 8, (0, 35), 0, (23, 26), 2, 8, 1,
   9, 3, (0, 21), (0, 13), (24, 0), 7, 9, 8, (19, 26), 2, 1, 7, 9, (6, 6), 2,
   1, 3, (10, 27), 3, 1, 2, 4, (20, 0), 2, 6, 1, 8, 3, (42, 27), 5, 8, 3, 7,
   4, 6, 9, (23, 28), 8, 6, 9, (12, 0), 5, 7, (33, 7), 4, 1, 9, 3, 6, 2, 8,
   (33, 7), 4, 8, 9, 7, 5, (0, 22), (27, 0), 6, 8, 4, 9, (23, 12), 8, 2, 3, 1,
   5, 4, (24, 12), 1, 8, 2, 4, 9, (37, 0), 3, 2, 1, 5, 9, 6, 4, 7, (36, 0), 1,
   2, 8, 7, 5, 4, 3, 6, (7, 0), 1, 4, 2, (10, 0), 3, 4, 1, 2, (16, 0), 3, 1,
   4, 2, 6, (8, 0), 1, 7)
)

class TestSolutions(unittest.TestCase):
  def test_solve_examples(self):
    p_list = [
      (puzzles.one,     solution_1,  "one"),
      (puzzles.two,     solution_2,  "two"),
      (puzzles.three,   solution_3,  "three"),
      (puzzles.four,    solution_4,  "four"),
      (puzzles.killer2, soln_killer, "killer2"),
    ]

    for puzzle, solution, name in p_list:
      puzzle.solve()
      self.assertEqual(len(puzzle.solutions), 1,
                       "{0} has more solutions than expected".format(name))
      self.assertEqual(puzzle.solutions[0].data, solution,
                       "{0} solution incorrect".format(name))

  def test_random_puzzle_generation(self):
    for i in range(100):
      k = kakuro.gen_random(10, 10, seed=i)

      # Will raise exception on failure
      k.check_puzzle()

      # Will raise exception on failure
      k.check_solution()

  def test_random_puzzle_solutions(self):
    for i in range(100):
      logging.debug("Puzzle %d", i)
      k = kakuro.gen_random(10, 10, seed=i, is_solved=False)
      k.solve()

      # Will raise exception on failure
      k.check_solution()
