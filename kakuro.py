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
#
##############################################################################
#
# Various options affect the solving routines:

BRUTE_FORCE_WARN_LIMIT = 10**11

#############################################################################

import logging
import copy
import random
import threading
import thread

import itertools

#logging.basicConfig(level=logging.DEBUG)

class MalformedPuzzleException(Exception):
  """The puzzle was not a valid Kakuro puzzle."""

class ConstraintWithoutEntryCellException(MalformedPuzzleException):
  """If there's a constraint in a particular direction, there must be at least
  one entry cell immediately following the constraint in that direction."""

class InvalidPuzzleDataException(MalformedPuzzleException):
  """Found an unexpected object in the puzzle data. Puzzle data should be a
  list consisting of either integers or tuples of two integers."""

class InvalidPuzzleDataLengthException(MalformedPuzzleException):
  """Kakuro puzzles must be square, but the puzzle was not square."""

class SolutionInvalidException(Exception):
  """Raised by check_solution() if the solution is invalid."""

class SolutionInvalidSumException(SolutionInvalidException):
  """Raised by check_solution() if a sum is invalid."""

class SolutionUnsolvedException(SolutionInvalidException):
  """Raised by check_solution() if no attempt was made to solve the puzzle."""

class SolutionNonUniqueException(SolutionInvalidException):
  """Raised by check_solution() if a row/col has the correct sum but the
  numbers are not unique and the puzzle was specified as an exclusive
  puzzle."""

class SolutionRangeException(SolutionInvalidException):
  """Raised by check_solution() if a solution value was outside the range
  allowed by the puzzle (the default range is 1 to 9)."""

class SearchTimeExceeded(Exception):
  """Raised by the solver if the puzzle is taking too long to solve."""

class Cell(object):
  """Represents a single cell inside a Kakuro puzzle.

  Generally we only use these when we want to repesent a cell with an unknown
  state during the solving process. After the puzzle has been completely solved
  we only care about the value of the cell."""
  def __init__(self, start=None):
    if start == None:
      start = [1,2,3,4,5,6,7,8,9]
    if type(start) == type(0):
      start = [start]
    self.set = set(start)
    self.test = 0

  def __repr__(self):
    if len(self.set) == 1:
      for x in self.set:
        return "Cell(%d)" % x

    return "Cell(%s)" % list(self.set)

class Kakuro(object):
  """Creates a new Kakuro puzzle.

  Parameters (max_val, is_exclusive, etc) should not change after a puzzle is
  created."""
  def __str__(self):
    return pretty_print(self.data, self.x_size)

  def __repr__(self):
    return '<%dx%d Kakuro puzzle, %s, at %s>' % (
            self.x_size,
            len(self.data)/self.x_size,
            "solved" if self._is_solved else "unsolved",
            hex(id(self)),
        )
  def __init__(self, x_size, data, min_val=1, max_val=9, is_exclusive=True):
    self.data = data

    if x_size < 1:
      raise ValueError("x_size must be greater than 0.")

    self.x_size = x_size

    if max_val < min_val:
      raise ValueError("max_val must be greater than or equal to min_val.")

    self.min_val = min_val

    self.max_val = max_val

    self.is_exclusive = is_exclusive

    self._is_solved = False

    self.num_entry_squares = (
      sum(1 for c in self.data if type(c) == type(0) and c > 0)
    )
    """Total number of entry squares in this puzzle."""

    val_size = self.max_val - self.min_val + 1
    self.search_space_size = val_size**self.num_entry_squares

  def solve(self, timeout=None, timeout_exception=True):
    """Attempts to solve this puzzle.

    If a timeout (number of seconds) is provided, will raise an exception if
    the puzzle is not yet solved after that amount of time. If
    timeout_exception is set to False, will return False instead of raising an
    exception.

    If a timeout occurs, the puzzle will be the same as it was before solving.
    TODO: Make this true!
    """
    if timeout:
      def interrupt():
        if not t.done:
          thread.interrupt_main()
      t = threading.Timer(timeout, interrupt)
      t.daemon = True
      t.done = False
      t.start()

    try:
      self._solve(bool(timeout))
      self._is_solved = True
      if timeout:
        t.done = True
      return True
    except KeyboardInterrupt:
      # Usually we would prefer to raise an exception, but for the
      # multiprocessing module we need to always return a value or the chain
      # will get stuck.
      if timeout_exception:
        raise SearchTimeExceeded()
      else:
        return False

  def _solve(self, has_timeout):
    # TODO: not solving is_exclusive=False puzzles correctly

    if self._is_solved:
      raise Exception("Already solved")

    input = self.data
    x_size = self.x_size

    # To make the script more space efficient, each cell can be represented as
    # an integer and we can use bitwise operations to indicate which integers
    # are allowed in the slot.  Unfortunately this also makes the code
    # somewhat harder to read. Set operations are a natural fit for
    # readability since we are talking about possibilities for each cell.
    #
    # The faster method is used in the C speedups.
    self._cellwise = a = [Cell() if x==1 else x for x in input]

    def is_entry_square(cell):
      return isinstance(cell, Cell)

    constraints = _generate_constraints(a, x_size, is_entry_square)
    self._constraints = constraints

    _first_run(constraints)
    self._initial_constraints = copy.deepcopy(constraints)

    for i in range(200):
      old = str(constraints)
      _iterate(constraints, self.is_exclusive)

      if _is_solved(constraints):
        logging.debug("Solved in constraint eval phase after %d passes" % i)
        data = [x.set.copy().pop() if isinstance(x, Cell)  else x for x in a]
        self.data = data
        return

      if old == str(constraints):
        # Was unable to improve constraints any further; must brute force now.
        for c in constraints:
          for x in c[1:]:
            if len(x.set) == 0:
              raise Exception("Failure in constraint eval stage: cell has no possible values")

        logging.debug("Begining speculative evaluation")
        unsatisfied = self._unsatisfied = [c for c in constraints if any(len(x.set) > 1 for x in c[1:])]

        brute_force_size = 1
        for c in unsatisfied:
          for x in c[1:]:
            if len(x.set) > 0:
              brute_force_size *= len(x.set)
        logging.debug("Search size: %d" % brute_force_size)

        self.brute_force_size = brute_force_size
        self.speedup = self.search_space_size / brute_force_size

        if brute_force_size > BRUTE_FORCE_WARN_LIMIT and not has_timeout:
          logging.warning("Brute force size of %d is very high", brute_force_size)

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
          _recursive_cell_test(constraints, cells, 0, self.is_exclusive)
        except Success:
          data = [x.test if isinstance(x, Cell)  else x for x in a]
          logging.debug("Solved in speculative eval phase after %d passes" % i)
          self.data = data
          return
        else:
          raise Exception("Unable to solve")

  def unsolve(self):
    """Removes the solution data from this puzzle leaving the constraints
    intact."""
    self._is_solved = False

    d = self.data
    for i in range(len(d)):
      if d[i] and type(d[i]) != type(()):
        d[i] = 1

  def check_solution(self):
    """Raises an exception if this puzzle is unsolved or has an invalid
    solution.

    This function algorithmically verifies the solution is correct, so it may
    raise an exception after solve() returned successfully if there is a bug
    in the solving algorithm."""
    if not self._is_solved:
      raise SolutionUnsolvedException()

    def is_entry_square(cell):
      return cell != 0 and type(cell) == type(1)

    def fail_debug():
      logging.debug("failed puzzle data:\n" + str(self))

    constraints = _generate_constraints(self.data, self.x_size, is_entry_square)

    # TODO: better error reporting for all of these
    if not all(x[0] == sum(y for y in x[1:]) for x in constraints):
      raise SolutionInvalidSumException()

    if self.is_exclusive:
      if not all(len(x[1:]) == len(set(x[1:])) for x in constraints):
        fail_debug()
        raise SolutionNonUniqueException()

    if any(any(val > self.max_val for val in x[1:]) for x in constraints):
      fail_debug()
      raise SolutionRangeException()

    if any(any(val < self.min_val for val in x[1:]) for x in constraints):
      fail_debug()
      raise SolutionRangeException()

  def check_puzzle(self):
    """Raises an exception if puzzle is not valid."""
    if len(self.data) % self.x_size != 0:
      raise InvalidPuzzleDataLengthException("The input data must be square in shape.")

    for x in self.data:
      if (type(x) != type(0)) and (type(x) != type(())):
        raise InvalidPuzzleDataException("Only tuples and integers are allowed in "
                                         "the input.")

    def is_entry_square(cell):
      return cell != 0

    # TODO: for some reason this function modifies the first arg passed; fix
    # it so it doesn't and then the deepcopy can be removed.
    constraints = _generate_constraints(copy.deepcopy(self.data), self.x_size, is_entry_square)

    if any(len(c) < 2 for c in constraints):
      raise ConstraintWithoutEntryCellException("Constraint without entry square.")

def pretty_print(data, x_size):
  """Draws a prettier version of puzzle strings"""
  #_verify_input_integrity(data, x_size)

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

def _recursive_cell_test(constraints, cells, n, is_exclusive):
  try:
    for i in cells[n].set:
      cells[n].test = i
      _recursive_cell_test(constraints, cells, n+1, is_exclusive)
  except IndexError:
    if _are_constraints_satisfied(constraints, is_exclusive):
      raise Success

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
  ACROSS, DOWN = 0, 1

  for row in rows:
    constraints.extend(_process_row_or_col(row, ACROSS, is_entry_square))

  for col in cols:
    constraints.extend(_process_row_or_col(col, DOWN, is_entry_square))

  return constraints

def gen_random(x_size=10, y_size=10, is_solved=True, is_exclusive=True,
               min_val=1, max_val=9, seed=None):
  """Generates a new random Kakuro puzzle of the specified size.  If a
  ``seed`` is provided, output is deterministic when all other parameters are
  also the same. Providing a seed is recommended."""

  def row(a, x_size, n):
    return a[x_size*n:x_size*(n+1)]

  def col(a, x_size, n):
    return a[n:len(a):x_size]

  if seed:
    random.seed(seed)

  #s = random.sample(range(1,10),9)

  a=[0]*x_size*y_size

  for idx in range(x_size*y_size):
    row_idx = idx/x_size
    col_idx = idx%x_size
    if random.random() > 0.6:
      # TODO: This works OK for small boards, but not for big ones
      for _ in range(20):
        val = random.randint(min_val, max_val)
        if is_exclusive:
          if (val not in row(a, x_size, row_idx) and
              val not in col(a, x_size, col_idx)):
            a[idx] = val
            break
        else:
          a[idx] = val
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
        a[i] = sum, 0
        sum = 0

  # add tuples and down rules; modify existing tuples if necessary
  sum = 0
  for x in range(0, x_size):
    for i in range(len(a) - x_size + x, -1, -x_size):
      if a[i] and type(a[i]) != type(()):
        sum += a[i]
      elif sum:
        if type(a[i]) == type(()):
          a[i] = a[i][0], sum
        else:
          a[i] = 0, sum
        sum = 0

  k=Kakuro(x_size, a, min_val, max_val, is_exclusive)
  if not is_solved:
    k.unsolve()

  k._is_solved = is_solved
  return k

def _are_constraints_satisfied(constraints, check_uniq):
  return (_are_constraint_sums_valid(constraints) and
          (_are_vals_unique(constraints) if check_uniq else True))

def _are_constraint_sums_valid(constraints):
  return all(x[0] == sum(y.test for y in x[1:]) for x in constraints)

def _are_vals_unique(constraints):
  for c in constraints:
    vals = [x.test for x in c[1:]]
    if len(vals) != len(set(vals)):
      return False
  return True

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
          print record
          msg = "Found constraint '%d' without adjacent entry cell." % constraint[0]
          raise ConstraintWithoutEntryCellException(msg)
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

class _memoized(object):
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

@_memoized
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

def _iterate(constraints, is_exclusive):
  """The strategy is to run this repeatedly until it stops making progress.
  Sloppy, but effective."""
  for c in constraints:
    sum_val, cells = c[0], c[1:]
    if is_exclusive:
      _remove_duplicates(cells)
    _remove_invalid_sums(cells, sum_val)
