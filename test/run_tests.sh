#!/bin/sh
# This should be run from main directory like: % test/run_tests.sh

python2.7 -m unittest discover -v -s test
