#!/usr/bin/env python2.7
import kakuro
import cProfile
import pstats

k=kakuro.gen_random(is_solved=False,seed=5)

cProfile.run('k.solve()', 'prof')
p = pstats.Stats('prof')
p.strip_dirs().sort_stats('cumulative').print_stats(40)

#print len(k.solutions);
