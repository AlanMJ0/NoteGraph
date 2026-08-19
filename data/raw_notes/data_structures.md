# Data Structures

## Hash Tables

A hash table stores key-value pairs for O(1) average-time lookup. It uses a hash function to map keys to bucket indices.

Hash tables are widely used in caching because they allow near-instant retrieval of cached values by key.

### Collision Resolution

When two keys hash to the same bucket, a collision occurs. The two main strategies are:

- **Chaining**: Each bucket holds a linked list of all entries that hash there.
- **Open Addressing**: On collision, probe the next available slot (linear probing, quadratic probing, or double hashing).

## Linked Lists

A linked list is a linear data structure where each element (node) contains a value and a pointer to the next node. Insertion and deletion at the head are O(1), but random access is O(n).

Linked lists are the backbone of chaining in hash tables.

## Trees

### Binary Search Tree (BST)

A BST stores elements such that for each node, all left descendants are smaller and all right descendants are larger. Search, insert, and delete are O(log n) on average but O(n) in the worst case (unbalanced tree).

### AVL Tree

An AVL tree is a self-balancing BST. It maintains a balance factor (difference in heights of left and right subtrees) of at most 1, guaranteeing O(log n) for all operations.
