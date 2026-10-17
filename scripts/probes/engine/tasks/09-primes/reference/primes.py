def primes_below(n):
    return [k for k in range(2, n) if all(k % d for d in range(2, int(k**0.5) + 1))]
