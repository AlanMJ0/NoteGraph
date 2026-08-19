# Sorting Algorithms

## QuickSort

QuickSort is a divide-and-conquer sorting algorithm with average time complexity O(n log n) and worst-case O(n²).

It works by selecting a pivot element, then partitioning the array so all elements less than the pivot come before it and all greater elements come after it.

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

QuickSort performs poorly on already-sorted input without randomization. A randomized pivot selection avoids the O(n²) worst case in practice.

## MergeSort

MergeSort always runs in O(n log n) regardless of input order. It splits the array in half recursively, sorts each half, then merges them.

```python
def mergesort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return merge(left, right)
```

MergeSort is stable (equal elements keep their original order) and is preferred when stability matters.

## BubbleSort

BubbleSort has O(n²) time complexity in average and worst cases. It repeatedly steps through the list, compares adjacent elements, and swaps them if they are in the wrong order. It is simple but inefficient for large datasets.
