import kakuro

puzzle = kakuro.new_puzzle(5, 5, seed=24)
puzzle.unsolve()
print(puzzle.get_txt())