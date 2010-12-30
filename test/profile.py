#!/usr/bin/env python2.7
import cProfile
import pstats
import sys
import os

# Allow to run from / or /test/
for relpath in ['../','./']:
  sys.path.append(os.path.abspath(relpath))

import kakuro
import puzzles

#k=kakuro.gen_random(is_solved=False,seed=5)
k=puzzles.killer2

cProfile.run('k.solve()', 'prof')
p = pstats.Stats('prof')
p.strip_dirs().sort_stats('cumulative').print_stats(40)

#print len(k.solutions);
