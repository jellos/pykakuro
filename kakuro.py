#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pykakuro - Kakuro Tools For Python
# Copyright (C) 2010 Brandon Thomson <brandon.j.thomson@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

##############################################################################

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
ONE_TO_NINE_EXCLUSIVE = True

# Setting this to true enforces that constraint blocks cannot have identical
# numbers in them.
IDENTICAL_EXCLUSION = True

#############################################################################

import logging

import itertools

logging.basicConfig(level=logging.DEBUG)

class Cell(object):
  def __init__(self, start=None):
    if start == None:
      start = [1,2,3,4,5,6,7,8,9]
    if type(start) == type(0):
      start = [start]
    self.set = set(start)
    self.test = 0

  def __repr__(self):
    if self.set == set([]):
      return "Cell([])"
    if len(self.set) == 1:
      for x in self.set:
        return "Cell(%d)" % x
    return "Cell(%s)" % list(self.set)

class Kakuro(object):
  def __str__(self):
    return data_to_grid(self.data, self.x_size)

  def __repr__(self):
    return '<%s.%s object (%dx%d) at %s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.x_size,
            len(self.data)/self.x_size,
            hex(id(self)),
        )
  def __init__(self, data, x_size):
    self.data = data
    self.x_size = x_size

  def solve(self):
    import copy

    input = self.data
    x_size = self.x_size
    _verify_input_integrity(input, x_size)

    #TODO: validate input
    #raise MalformedBoardException("{0} not a valid token".format(cell))

    # To make the script more space and time efficient, each cell can be
    # represented as an integer and we can use bitwise operations to indicate
    # which integers are allowed in the slot.  Unfortunately this also makes the
    # code somewhat harder to read. Set operations are a natural fit for
    # readability since we are talking about possibilities for each cell.
    self._cellwise = a =[Cell() if x==1 else x for x in input]

    def is_entry_square(cell):
      return isinstance(cell, Cell)

    constraints = self._constraints = _generate_constraints(a, x_size, is_entry_square)

    _first_run(constraints)
    self._initial_constraints = copy.deepcopy(constraints)

    for i in range(200):
      old = str(constraints)
      _iterate(constraints)
      if _is_solved(constraints):
        data = [x.set.copy().pop() if isinstance(x, Cell)  else x for x in a]
        self.data = data
        return
      if old == str(constraints):
        for c in constraints:
          for x in c[1:]:
            if len(x.set) == 0:
              raise Exception("Failure in heuristic stage: unable to solve")

        logging.debug("Begining speculative evaluation")
        unsatisfied = self._unsatisfied = [c for c in constraints if any(len(x.set) > 1 for x in c[1:])]
        space = 1
        for c in unsatisfied:
          for x in c[1:]:
            if len(x.set) > 0:
              space *= len(x.set)
        logging.debug("Search size: %d" % space)

        cells = []

        # set .tests
        for c in constraints:
          for x in c[1:]:
            if len(x.set) == 1:
              x.test = x.set.pop()


        for c in unsatisfied:
          for x in c[1:]:
            if len(x.set) > 1:
              cells.append(x)

        try:
          _recursive_cell_test(constraints, cells, 0)
        except Success:
          data = [x.test if isinstance(x, Cell)  else x for x in a]
          self.data = data
        else:
          raise Exception("Unable to solve")


  def unsolve(self):
    d = self.data
    for i in range(len(d)):
      if d[i] and type(d[i]) != type(()):
        d[i] = 1

def _verify_input_integrity(data, x_size):
  if len(data) % x_size != 0:
    raise MalformedBoardException("The input data must be square in shape.")

  for x in data:
    if (type(x) != type(0)) and (type(x) != type(())):
      raise MalformedBoardException("Only tuples and integers are allowed in "
                                    "the input.")


def data_to_grid(data, x_size):
  """Quick util func to draw prettier version of puzzle strings"""
  _verify_input_integrity(data, x_size)

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

def _is_solved(constraints):
    return all(all(len(x.set) == 1 for x in c[1:]) for c in constraints)

class Success(Exception): pass

def _recursive_cell_test(constraints, cells, n):
  try:
    for i in cells[n].set:
      cells[n].test = i
      _recursive_cell_test(constraints, cells, n+1)
  except IndexError:
    if _are_constraints_satisfied(constraints):
      raise Success

def verify_solution(input, x_size):
  _verify_input_integrity(input, x_size)

  def is_entry_square(cell):
    return cell != 0 and type(cell) == type(1)

  constraints = _generate_constraints(input, x_size, is_entry_square)

  print constraints

  s=all(x[0] == sum(y for y in x[1:]) for x in constraints)
  if s:
    print "Valid Solution"
    return True
  else:
    print "Invalid Solution"
    return False

def rows_from_list(list, x_size):
  return [list[z:z+x_size] for z in range(0,len(list)-x_size+1,x_size)]

def cols_from_list(list, x_size):
  return [list[z::x_size] for z in range(x_size)]

def _generate_constraints(input, x_size, is_entry_square):
  """
  Creates a list of constraints based on given input. If the input contains
  objects, the objects will be multiply referenced in the output list where
  constraints overlap.

  is_entry_square - a function provided by the caller that returns true if a
  cell provided to the function is a square where a number needs to go. (This
  allows this function to be agnostic of whether objects or simple numbers are
  used in the list.)
  """
  rows = rows_from_list(input, x_size)
  cols = cols_from_list(input, x_size)

  constraints = []
  ACROSS = 0
  DOWN = 1

  for row in rows:
    constraints.extend(_process_row_or_col(row, ACROSS, is_entry_square))

  for col in cols:
    constraints.extend(_process_row_or_col(col, DOWN, is_entry_square))

  return constraints


def row(a, x_size, n):
  return a[x_size*n:(x_size+1)*n]

def col(a, x_size, n):
  return a[n:len(a):x_size]

def new_puzzle(x_size, y_size, seed=None):
  import random
  random.seed(seed)

  #s = random.sample(range(1,10),9)

  a=[0]*x_size*y_size
  for i in range(x_size*y_size):
    if random.random() > 0.6:
      j = None
      for x in range(20):
        j = random.randint(1,9)
        # TODO: ok for small boards, but not for big
        if (j not in row(a, x_size, i/y_size) and
            j not in col(a, x_size, i%x_size)):
          a[i] = j
          break

  # 0-out top and left
  a[0:x_size] = (0,)*x_size
  a[0::x_size] = (0,)*y_size

  # add tuples and right rules
  sum = 0
  for y in range(0, y_size):
    for i in range(x_size + y*x_size-1, y*x_size-1, -1):
      if a[i]:
        sum += a[i]
      elif sum:
        a[i] = (sum, 0)
        sum = 0

  # add tuples and down rules, modify existing tuples if necessary
  sum = 0
  for x in range(0, x_size):
    for i in range(len(a) - x_size + x, -1, -x_size):
      if a[i] and type(a[i]) != type(()):
        sum += a[i]
      elif sum:
        if type(a[i]) == type(()):
          a[i] = (a[i][0], sum)
        else:
          a[i] = (0, sum)
        sum = 0


  return Kakuro(data=a, x_size=x_size)




def _are_constraints_satisfied(constraints):
  return all(x[0] == sum(y.test for y in x[1:]) for x in constraints)

class MalformedBoardException(Exception): pass

def _process_row_or_col(record, row_or_col, is_entry_square):
  constraints = []

  record.reverse()
  while record:
    cell = record.pop()
    if type(cell) == type(()):
      sum_val = cell[row_or_col]
      if sum_val != 0:
        constraint = [sum_val]
        cell = record.pop()
        if not is_entry_square(cell):
          raise MalformedBoardException("Constraint without adjacent '1'")
        constraint.append(cell)
        try:
          while True:
            cell = record.pop()
            if not is_entry_square(cell):
              record.append(cell) #unpop
              break
            constraint.append(cell)
        except IndexError: pass
        constraints.append(constraint)

  return constraints

from itertools import combinations
from itertools import chain

def get_vals(sum_val, n):
  """
  Returns a list of tuples of all the combinations of n integers that sum to
  sum_val.

  >>> get_vals(10, 3)
  [(1, 2, 7), (1, 3, 6), (1, 4, 5), (2, 3, 5)]

  >>> get_vals(7, 3)
  [(1, 2, 4)]
  """ 
  return [x for x in combinations(range(1, sum_val),n) if
          sum(x) == sum_val and all(y<10 for y in x)]

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
def get_set(sum_val, n):
  """
  Returns the set of integers present in all the combinations of n integers
  that sum to sum_val.

  For a nice colorful table of these results, try:
    http://www.kevinpluck.net/kakuro/KakuroCombinations.html

  >>> get_set(10, 3)
  set(1, 2, 3, 4, 5, 6, 7)

  >>> get_set(7, 3)
  set(1, 2, 4)
  """ 
  if n == 1: return set((sum_val,))

  def flatten(listOfLists):
    return list(chain.from_iterable(listOfLists))
  return set(flatten(get_vals(sum_val, n)))

def _first_run(constraints):
  """
  Assigns set of possible values to each cell based on analysis of constraint
  value and number of cells.
  """
  for c in constraints:
    sum_val = c[0]
    num_boxes = len(c) - 1
    for x in c[1:]:
      x.set &= get_set(sum_val, num_boxes)

def _remove_duplicates(cells):
  """Given a set of cells, if any cells have only 1 possibility, this
  possibility will be removed from the other cells."""
  for cell1 in cells:
    if len(cell1.set) == 1:
      for cell2 in cells:
        if cell1 is not cell2:
          cell2.set -= cell1.set;

def _remove_invalid_sums(cells, sum_val):
  """Adds up all combinations of the integers in the cells and checks which
  ones sum to sum_val. Removes any integers for which it is impossible to sum
  to sum_val using that integer in that cell.

  Possibly a bit too clever (and slow) for its own good."""
  from itertools import product

  sets = (cell.set for cell in cells)
  new_sets = zip(*(seq for seq in product(*sets) if sum(seq)==sum_val))
  for old, new in zip(cells, new_sets):
    old.set &= set(new)

def _iterate(constraints):
  """The strategy is to run this repeatedly until it stops making progress.
  Sloppy, but effective."""
  for c in constraints:
    sum_val, cells = c[0], c[1:]
    if IDENTICAL_EXCLUSION:
      _remove_duplicates(cells)
    _remove_invalid_sums(cells, sum_val)


# Sum=3, Boxes=2: 12
# Sum=4, Boxes=2: 13
# Sum=5, Boxes=2: 14, 23
# Sum=5, Boxes=2: 15, 24
# Sum=5, Boxes=3: 123


# To solve the puzzle, we call solve(sample_puzzle, constraints=False)
