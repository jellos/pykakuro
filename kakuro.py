#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Kakuro Solver
# Copyright (c) 2010 Brandon Thomson <brandon.j.thomson@gmail.com>
# Made available under an MIT license, terms at bottom of file

# Kakuro boards don't really lend themselves to being drawn in ASCII, but we'll
# give it a shot. Here's a board the way you might see it drawn in a puzzle
# book:
#
#      |\ |\
#      |7\|6\
#   |\4|  |  |
#   |4\|--|--|
# \7|  |  |  |
#  \|--|--|--|
# \6|  |  |  |
#  \|--|--|--|
#
# To represent the board, we use a 0 for the cells that don't take a number and
# a 1 for the cells that do. Constraint squares are a tuple of two integers,
# with the first being the constraint across and the second being the
# constraint down. If no constraint is specified for a particular direction,
# the integer should be 0. Here is the puzzle shown above in this format:
#
#  0 | 0 |0,7|0,6|
# ---|---|---|---|
#  0 |4,4| 1 | 1 |
# ---|---|---|---|
# 7,0| 1 | 1 | 1 |
# ---|---|---|---|
# 6,0| 1 | 1 | 1 |
# ---|---|---|---|
#
# And here is the same puzzle encoded in the input format this program uses:

sample_puzzle = (   0 ,   0 ,(0,7),(0,6),
                    0 ,(4,4),   1 ,   1 ,
                 (7,0),   1 ,   1 ,   1 ,
                 (6,0),   1 ,   1 ,   1 ,
                )
x_size = 4

###

ACROSS = 0
DOWN = 1

y_size = len(sample_puzzle) / x_size

a=[set() if x==1 else x for x in sample_puzzle]

rows = [a[z:z+x_size] for z in range(0,len(a)-x_size+1,x_size)]
cols = [a[z::x_size] for z in range(4)]

constraints = []

class MalformedBoardException(Exception): pass

def process_row_or_col(row, row_or_col):
  constraints = []

  row.reverse()
  while row:
    cell = row.pop()
    if cell == 0:
      pass
    elif cell == set():
      raise MalformedBoardException("'1' without adjacent constraint")
    elif type(cell) == type(()):
      if cell[row_or_col]:
        constraint = [cell[row_or_col]]
        cell = row.pop()
        if cell != set():
          raise MalformedBoardException("Constraint without adjacent '1'")
        constraint.append(cell)
        try:
          while cell == set():
            cell = row.pop()
            constraint.append(cell)
        except IndexError: pass
        constraints.append(constraint)
    else:
      raise MalformedBoardException("{0} not a valid token".format(cell))

  return constraints

for row in rows:
  constraints.extend(process_row_or_col(row, ACROSS))

for col in cols:
  constraints.extend(process_row_or_col(col, DOWN))

for c in constraints:
  for x in range(1,len(c)):
    c[x].update(set(range(1, c[0])))

for c in constraints:
  for x in range(1,len(c)):
    c[x].intersection_update(set(range(1, c[0])))


# To solve the puzzle, we call solve(sample_puzzle, constraints=False)

# Copyright (c) 2010 Brandon Thomson
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
