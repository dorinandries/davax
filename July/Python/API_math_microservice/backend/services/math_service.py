# math_service.py
from fastapi import HTTPException
from cachetools import cached, LRUCache, cachedmethod

# Create a cache with a max size (number of items)
pow_cache = LRUCache(maxsize=128)
fibo_cache = LRUCache(maxsize=128)
fact_cache = LRUCache(maxsize=128)
prime_cache = LRUCache(maxsize=128)

class MathService:
    @cached(pow_cache)
    def pow(self, x: float, y: float) -> float:
        """x pow y"""
        return x ** y

    @cached(fibo_cache)
    def fibo(self, n: int) -> int:
        """Compute the nth Fibonacci number."""
        if n < 0:
            raise HTTPException(status_code=400, detail="n ≥ 0")
        if n < 2:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @cached(fact_cache)
    def factorial(self, n: int) -> int:
        """Compute n! iteratively."""
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @cachedmethod(lambda self: prime_cache)
    def is_prime_service(self, n: int) -> dict:
        """Check if a number is prime and return a response."""
        if n < 2:
            return {"operation": "prime", "input": n, "is_prime": False}
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return {"operation": "prime", "input": n, "is_prime": False}
        return {"operation": "prime", "input": n, "is_prime": True}
