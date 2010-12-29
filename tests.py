#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kakuro
import puzzles

import logging
import unittest

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

# Manually verified solutions to sample puzzles
solution_1 = [0, 0, (0, 7), (0, 6),
              0, (4, 4), 1, 3,
              (7, 0), 1, 4, 2,
              (6, 0), 3, 2, 1]

solution_2 = [0, 0, (0, 23), (0, 21), 0,
              0, (8, 15), 1, 7, 0,
              (8, 0), 1, 2, 5, 0,
              (27, 0), 7, 8, 9, 3,
              (5, 0), 2, 3, 0, 0,
              (14, 0), 5, 9, 0, 0,
              0, 0, 0, 0, 0]

solution_3 = [0, (0, 23), (0, 30), 0, 0, (0, 27), (0, 12), (0, 16),
             (16, 0), 9, 7, 0, (24, 17), 8, 7, 9,
             (17, 0), 8, 9, (29, 15), 8, 9, 5, 7,
             (35, 0), 6, 8, 5, 9, 7, (0, 12), 0,
             0, (7, 0), 6, 1, (8, 7), 2, 6, (0, 7),
             0, (0, 11), (16, 10), 4, 6, 1, 3, 2,
             (21, 0), 8, 9, 3, 1, (5, 0), 1, 4,
             (6, 0), 3, 1, 2, 0, (3, 0), 2, 1]

solution_4 = [0, 0, 0, 0, 0, 0, (0, 16), (0, 3),
              0, 0, 0, 0, 0, (8, 6), 7, 1,
              0, (0, 16), (0, 6), 0, (14, 30), 3, 9, 2,
              (11, 0), 9, 2, (7, 0), 6, 1, (0, 6), 0,
              (10, 0), 7, 3, (13, 7), 8, 2, 3, (0, 16),
              0, (14, 0), 1, 4, 9, (8, 0), 1, 7,
              0, (0, 4), (9, 17), 2, 7, (11, 0), 2, 9,
              (12, 0), 3, 8, 1, 0, 0, 0, 0,
              (10, 0), 1, 9, 0, 0, 0, 0, 0]

class TestSolutions(unittest.TestCase):
  def test_solve_examples(self):
    p_list = [
      (puzzles.one,   solution_1, "one"),
      (puzzles.two,   solution_2, "two"),
      (puzzles.three, solution_3, "three"),
      (puzzles.four,  solution_4, "four"),
    ]

    for puzzle, solution, name in p_list:
      puzzle.solve()
      self.assertEqual(puzzle.data, solution,
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
