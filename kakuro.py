#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pykakuro - Kakuro Tools For Python
# Copyright (c) 2010 Brandon Thomson <brandon.j.thomson@gmail.com>
# Made available under an MIT license, terms at bottom of file

# Kakuro boards don't really lend themselves to being drawn in ASCII, but we'll
# give it a shot. Here's a board the way you might see it drawn in a puzzle
# book:
#
#      |\ |\
#      |7\|6\
#   |\4|  |  |
#   |4\|--+--+
# \7|  |  |  |
#  \|--|--+--+
# \6|  |  |  |
#  \|--+--+--+
#
# To represent the board, we use a 0 for the cells that don't take a number and
# a 1 for the cells that do. Constraint squares are a tuple of two integers,
# with the first being the constraint ACROSS and the second being the
# constraint DOWN. If no constraint is specified for a particular direction,
# the integer should be 0. Here is the puzzle shown above in this format:
#
#  0 | 0 |0,7|0,6|
# ---+---+---+---+
#  0 |4,4| 1 | 1 |
# ---+---+---+---+
# 7,0| 1 | 1 | 1 |
# ---+---+---+---+
# 6,0| 1 | 1 | 1 |
# ---+---+---+---+
#
# And here is the same puzzle encoded in the canonical format used by this
# program:
#
# sample_puzzle = (0 ,   0 ,(0,7),(0,6),
#                  0 ,(4,4),   1 ,   1 ,
#               (7,0),   1 ,   1 ,   1 ,
#               (6,0),   1 ,   1 ,   1 ,
#                 )
#
# When we call solve, we get back an output string:
# >>> kakuro.solve(sample_puzzle, 4)
# [0, 0, (0, 7), (0, 6), 0, (4, 4), 1, 3, (7, 0), 1, 4, 2, (6, 0), 3, 2, 1]
#
# In the grid form, that looks like this:
# >>> print kakuro.data_to_grid(result,4)
#
#  0 | 0 |0,7|0,6|
# ---+---+---+---+
#  0 |4,4| 1 | 3 |
# ---+---+---+---+
# 7,0| 1 | 4 | 2 |
# ---+---+---+---+
# 6,0| 3 | 2 | 1 |
# ---+---+---+---+
#
# Various options affect the solving routines:
#
# Setting this to true enforces an additonal constraint that only the integers
# 1 through 9 can be placed in each box.
ONE_TO_NINE_EXCLUSIVE = False

#############################################################################

import logging

logging.basicConfig(level=logging.DEBUG)

class Cell(object):
  def __init__(self, start=None):
    if start == None:
      start = [1,2,3,4,5,6,7,8,9]
    if type(start) == type(0):
      start = [start]
    self.set = set(start)

  def __repr__(self):
    if self.set == set([]):
      return "Cell([])"
    if len(self.set) == 1:
      for x in self.set:
        return "Cell(%d)" % x
    return "Cell(%s)" % list(self.set)


def data_to_grid(data, x_size):
  """Quick util func to draw prettier version of puzzle strings"""
  strings = []
  for x in data:
    if type(x) == type(()):
      strings.append(','.join(str(y) for y in x))
    else:
      strings.append(str(x))
  cell_width = max(len(x) for x in strings)
  centered = [x.center(cell_width) for x in strings]
  by_row = [centered[z:z+x_size] for z in range(0,len(data)-x_size+1,x_size)]
  separator = '+'.join(["-"*cell_width]*x_size) + '+'
  row_strings = ['|'.join(x)+'|' for x in by_row]
  y=len(row_strings)
  for x in range(y):
    row_strings.insert(y-x, separator)

  return '\n'.join((row_strings))

def is_solved(constraints):
    return all(all(len(x.set) == 1 for x in c[1:]) for c in constraints)

def solve(input, x_size):
  y_size = len(input) / x_size

  #TODO: validate input
  #raise MalformedBoardException("{0} not a valid token".format(cell))

  # To make the script more space and time efficient, each cell can be
  # represented as an integer and we can use bitwise operations to indicate
  # which integers are allowed in the slot.  Unfortunately this also makes the
  # code somewhat harder to read. Set operations are a natural fit for
  # readability since we are talking about possibilities for each cell.
  a=[Cell() if x==1 else x for x in input]
  rows = [a[z:z+x_size] for z in range(0,len(a)-x_size+1,x_size)]
  cols = [a[z::x_size] for z in range(x_size)]

  constraints = []
  ACROSS = 0
  DOWN = 1
  for row in rows:
    constraints.extend(process_row_or_col(row, ACROSS))

  for col in cols:
    constraints.extend(process_row_or_col(col, DOWN))

  first_run(constraints)

  for i in range(200):
    old = str(constraints)
    iterate(constraints)
    if is_solved(constraints):
      break
    if old == str(constraints):
      logging.debug("Begining speculative evaluation")
      #unsatisfied = [c for c in constraints if any(len(x) > 1 for x in c[1:])]
      #solutions = [[y for y in product(*x[1:]) if sum(y)==x[0]] for x in a]
      break

  return [x.set.copy().pop() if isinstance(x, Cell) else x for x in a]

class MalformedBoardException(Exception): pass

def process_row_or_col(record, row_or_col):
  constraints = []

  record.reverse()
  while record:
    cell = record.pop()
    if type(cell) == type(()):
      sum_val = cell[row_or_col]
      if sum_val != 0:
        constraint = [sum_val]
        cell = record.pop()
        if not isinstance(cell, Cell):
          raise MalformedBoardException("Constraint without adjacent '1'")
        constraint.append(cell)
        try:
          while True:
            cell = record.pop()
            if not isinstance(cell, Cell):
              record.append(cell) #unpop
              break
            constraint.append(cell)
        except IndexError: pass
        constraints.append(constraint)

  return constraints

from itertools import combinations
from itertools import chain

def get_vals(n_sum, num_boxes):
  return [x for x in combinations(range(1, n_sum),num_boxes) if
          sum(x) == n_sum and all(y<10 for y in x)]

class memoized(object):
  """Decorator that caches a function's return value each time it is called.
  If called later with the same arguments, the cached value is returned, and
  not re-evaluated.

  Found at http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
  """
  def __init__(self, func):
    self.func = func
    self.cache = {}
  def __call__(self, *args):
    try:
      return self.cache[args]
    except KeyError:
      self.cache[args] = value = self.func(*args)
      return value
    except TypeError:
      # uncachable -- for instance, passing a list as an argument.
      # Better to not cache than to blow up entirely.
      return self.func(*args)
  def __repr__(self):
    """Return the function's docstring."""
    return self.func.__doc__


@memoized
def get_set(n_sum, num_boxes):
  def flatten(listOfLists):
    return list(chain.from_iterable(listOfLists))
  return set(flatten(get_vals(n_sum, num_boxes)))

def first_run(constraints):
  for c in constraints:
    sum_val = c[0]
    num_boxes = len(c) - 1
    for x in c[1:]:
      x.set &= get_set(sum_val, num_boxes)
      print sum_val, num_boxes, x.set

def iterate(constraints):
  """This is the solver's main loop."""
  print constraints

  from itertools import product

  for c in constraints:
    sum_val = c[0]
    print sum_val
    cells = c[1:]
    sets = (cell.set for cell in cells)
    new_sets = zip(*[seq for seq in product(*sets) if sum(seq)==sum_val])
    for old, new in zip(cells, new_sets):
      print old.set, "->", new
      old.set &= set(new)



# http://www.kevinpluck.net/kakuro/KakuroCombinations.html
# Sum=3, Boxes=2: 12
# Sum=4, Boxes=2: 13
# Sum=5, Boxes=2: 14, 23
# Sum=5, Boxes=2: 15, 24
# Sum=5, Boxes=3: 123


# To solve the puzzle, we call solve(sample_puzzle, constraints=False)

# Copyright (c) 2010 Brandon Thomson <brandon.j.thomson@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
