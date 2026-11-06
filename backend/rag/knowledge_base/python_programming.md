# Python Programming & Best Practices

## What is Python
Python is a high-level, interpreted, dynamically typed, multi-paradigm programming language emphasizing code readability and simplicity ("The Zen of Python").
Python supports object-oriented, functional, and procedural programming styles.

Key Python Features:
1. Interpreted Language: Code executes line-by-line via the CPython interpreter without separate compilation steps.
2. Dynamic Typing: Variable types are determined at runtime.
3. Rich Standard Library: "Batteries included" with built-in modules for JSON, math, networking, threading, and asyncio.
4. Extensive Ecosystem: Dominates Data Science, Machine Learning (PyTorch, TensorFlow, Scikit-learn), and Web Backend Development (FastAPI, Django, Flask).

## Memory Management & GIL
Python uses automatic memory management with reference counting and a generational garbage collector (cyclic garbage collection).
CPython uses the Global Interpreter Lock (GIL), a mutex that prevents multiple native threads from executing Python bytecodes simultaneously.
For CPU-bound concurrency, use the `multiprocessing` module or native C extensions (NumPy, PyTorch) that release the GIL.
For I/O-bound concurrency (network requests, DB queries, file operations), use `asyncio` with `async`/`await` or thread pools.

## Generators, Iterators & Context Managers
Generators yield values one at a time using the `yield` keyword, conserving memory for large sequences.
Context managers implement `__enter__` and `__exit__` magic methods, ensuring deterministic resource cleanup (e.g. file handlers, DB locks, network sockets) via the `with` statement.

## Decorators & Metaprogramming
Decorators are higher-order functions that wrap another function or class to alter its behavior without modifying its source code.
Common standard decorators include `@property`, `@classmethod`, `@staticmethod`, and `@functools.wraps`.
