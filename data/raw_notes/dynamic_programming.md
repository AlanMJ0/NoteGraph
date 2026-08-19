# Dynamic Programming

## What is Dynamic Programming?

Dynamic Programming (DP) is an algorithmic technique for solving problems by breaking them into overlapping subproblems and storing the results (memoization or tabulation) to avoid redundant computation.

DP requires understanding of Recursion, because most DP solutions start as a recursive solution before being optimized.

## Key Concepts

### Memoization (Top-Down)

Store results of recursive calls in a cache (usually a dictionary or array). Before computing a subproblem, check if it was already solved.

```python
def fib(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]
```

### Tabulation (Bottom-Up)

Fill a table starting from base cases, building up to the full solution without recursion.

```python
def fib(n):
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

## Prerequisites

To learn Dynamic Programming you must first understand:
- **Recursion** — DP solutions are recursive solutions with caching.
- **Function Calls and the Call Stack** — understanding recursion depth.
- **Array and Dictionary operations** — for building the memo/table.
