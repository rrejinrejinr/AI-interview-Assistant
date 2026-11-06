# Data Structures and Algorithms (DSA)

## Binary Search Algorithm
Binary Search is an efficient divide-and-conquer search algorithm for sorted arrays.
Instead of scanning every element in linear time O(n), binary search compares the target element with the middle element `arr[mid]`.
If the target equals `arr[mid]`, the search succeeds.
If the target is smaller than `arr[mid]`, the search continues in the left subarray (`right = mid - 1`).
If the target is larger than `arr[mid]`, the search continues in the right subarray (`left = mid + 1`).

Time Complexity:
- Best Case: O(1) when the target is at the middle.
- Worst Case: O(log n) because the search space is divided in half with every comparison (`n / 2^k = 1 => k = log2(n)`).
- Space Complexity: O(1) iterative, O(log n) recursive call stack.
Requirement: The array must be sorted.

## Recursion and Call Stack Space Complexity
Recursion is a programming paradigm where a function solves a problem by calling itself with smaller inputs.
Every recursive function requires:
1. Base Case: The stopping condition that prevents infinite recursion.
2. Recursive Step: The logic that breaks down the problem and makes recursive calls.

Space Complexity of Recursion:
Determined by the maximum depth of the call stack (memory frames pushed for each call).
Linear recursion (e.g. factorial) has depth n and O(n) auxiliary space.
Divide-and-conquer recursion (e.g. binary search, merge sort) has depth log2(n) and O(log n) auxiliary stack space.

## Stack and Queue Data Structures
A Stack is a Last-In First-Out (LIFO) linear data structure.
Core operations: `push(x)` to insert on top, `pop()` to remove from top, `peek()` to inspect top. All execute in O(1) time.
Applications: Function call stack, undo/redo mechanisms, balanced parentheses parsing.

A Queue is a First-In First-Out (FIFO) linear data structure.
Core operations: `enqueue(x)` at the rear, `dequeue()` from the front. All execute in O(1) time.

## Sorting Algorithms: QuickSort vs MergeSort
MergeSort:
- Divide-and-conquer algorithm that splits the array into two halves, recursively sorts them, and merges the sorted halves.
- Time Complexity: Guaranteed O(n log n) in best, average, and worst cases.
- Space Complexity: O(n) auxiliary memory for merging.
- Stability: Stable sort.

QuickSort:
- Selects a pivot element, partitions array such that elements smaller than pivot are on left and larger on right, then recursively sorts partitions.
- Time Complexity: O(n log n) average case, O(n^2) worst case (unbalanced pivot).
- Space Complexity: O(log n) auxiliary stack space. In-place sorting.
- Stability: Unstable sort.
