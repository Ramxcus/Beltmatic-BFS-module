Beltmatic Minimum Integer Search

This is a Python-based graphical user interface (GUI) application that solves a number puzzle. The goal is to find an arithmetic expression using single-digit integers (1-9, which can be reused) and a selected set of mathematical operators to reach a specified target number, using the minimum possible number of integers.

Features

  Target Number Input: Easily specify the target number you want to reach.

  Selectable Operators: Choose which mathematical operations (+, -, *, /, ^) the solver can use, mimicking a "gradual release" game mechanic. Options include:

  Addition Only

  Addition & Subtraction

  Add, Sub, & Multiply

  All Basic Operations (+, -, *, /)

  All Operations (Including Exponent)

  Progress Tracking: Real-time updates on elapsed time, states visited per second, total unique states explored, and the current "depth" (number of integers in expressions being explored).

  Solution Display: Clearly shows the found expression and the number of integers used.

  Comprehensive Logging: A detailed log of the solver's progress, found solutions, and final status.

  Stop Functionality: Ability to stop a long-running search at any time.

How it Works (The Algorithm)

The solver employs a Breadth-First Search (BFS) like approach combined with powerful optimizations to efficiently explore the vast search space of possible arithmetic expressions.

Core Idea: Iterative Pairwise Combination

Instead of building expressions one digit at a time, the solver builds expressions iteratively by combining pairs of already valid expressions.

Initialization (Depth 1):

  All single digits (1-9) are considered as initial expressions.

  For each digit, its value, string representation (e.g., "7"), and a unique identifier (mask) are stored.

  A critical min_count_for_value dictionary is updated: value: minimum_integers_used_to_get_this_value.

Iterative Combination (Depth k):

  The solver proceeds depth by depth, where k represents the total number of integers used in an expression. It starts from k=2 and goes up to MAX_DEPTH (default 9).

  For each k, it considers all possible ways to combine two smaller expressions (e.g., an expression with i integers and another with j integers, where i + j = k).

  It iterates through every stored expression for i integers (val_A, expr_A) and every stored expression for j integers (val_B, expr_B).

Operator Application:

  For each pair (val_A, expr_A) and (val_B, expr_B), the solver attempts to apply all allowed mathematical operations (+, -, *, /, ^).

  It generates new values and their corresponding string expressions (e.g., (expr_A + expr_B)).

  Important Note on Digits: Unlike some Countdown-style puzzles, this solver assumes digits 1-9 can be reused. Therefore, the "mask" is primarily for tracking digits present in the string for debugging/informational purposes, not for preventing digit reuse.

Pruning (Optimizations for Efficiency):

  "Shorter Path for Value" (Crucial!): Before adding any newly generated expression, the solver checks if the new_val has already been found with an equal or lesser number of integers than the current_k (the current depth being explored). If so, this new path is redundant and discarded, as we are looking for the minimum integer count. This significantly cuts down the search space.

  Intermediate Value Limits: Intermediate calculation results are capped (MAX_INTERMEDIATE_VALUE) to prevent excessively large numbers that don't lead to the target or cause overflow errors.

  Integer Division: Division (/) only considers cases that result in an integer (no remainders).

  Exponent Limits: Exponentiation (^) is carefully capped for both base and exponent values to prevent unmanageably large numbers or extremely long computation times.

  Negative Result Filtering: Only positive results are considered.

Solution Found:

  If a generated new_val matches the target and uses fewer integers (current_k) than any previously found solution, it becomes the best_expression and min_integer_count is updated. The search continues for the current k to ensure the shortest path is found for any target value.

Termination:

  The search stops if a solution is found and the current k exceeds the min_integer_count, or if MAX_DEPTH is reached, or if the user explicitly stops the search.

Data Structures

  results_by_count[k] (List of Sets): A list where results_by_count[k] is a set of (value, expression_string, mask) tuples. This efficiently stores all unique expressions found for k integers and prevents duplicate expressions from being processed multiple times.

  min_count_for_value (Dictionary): value: integer_count. This dictionary allows for quick lookups of the minimum number of integers required to achieve a particular value discovered so far, enabling the "shorter path" pruning.
