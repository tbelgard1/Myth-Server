"""
Red-black tree implementation for the Myth metaserver.
A self-balancing binary search tree with guaranteed O(log n) operations.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Generic, Optional, TypeVar

import logging

logger = logging.getLogger(__name__)

MAX_TREE_NAME_LENGTH = 64

class Color(IntEnum):
    """Node colors for red-black tree"""
    BLACK = 0
    RED = 1

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

@dataclass
class Node(Generic[K, V]):
    """Red-black tree node"""
    key: K
    data: V
    color: Color = Color.RED
    parent: Optional['Node[K, V]'] = None
    left: Optional['Node[K, V]'] = None
    right: Optional['Node[K, V]'] = None

class RBTree(Generic[K, V]):
    """A self-balancing red-black tree implementation"""
    def __init__(self, name: str, comp_func: Callable[[K, K], int]):
        """Initialize red-black tree
        
        Args:
            name: Tree name (for debugging)
            comp_func: Comparison function that returns:
                      negative if a < b
                      0 if a == b
                      positive if a > b
        """
        if not name or len(name) > MAX_TREE_NAME_LENGTH:
            raise ValueError("Invalid tree name")
        if not comp_func:
            raise ValueError("Must provide comparison function")
            
        self.name = name
        self.comp_func = comp_func
        self.root: Optional[Node[K, V]] = None

    def search(self, key: K) -> Optional[Node[K, V]]:
        """Search for a node with the given key"""
        if not key:
            raise ValueError("Key cannot be None")

        current = self.root
        while current:
            cmp = self.comp_func(key, current.key)
            if cmp == 0:
                return current
            current = current.left if cmp < 0 else current.right
        return None

    def find_minimum(self, start_node: Optional[Node[K, V]] = None) -> Optional[Node[K, V]]:
        """Find node with minimum key in subtree"""
        if not start_node:
            start_node = self.root
        if not start_node:
            return None
            
        current = start_node
        while current.left:
            current = current.left
        return current

    def find_maximum(self, start_node: Optional[Node[K, V]] = None) -> Optional[Node[K, V]]:
        """Find node with maximum key in subtree"""
        if not start_node:
            start_node = self.root
        if not start_node:
            return None
            
        current = start_node
        while current.right:
            current = current.right
        return current

    def find_predecessor(self, node: Node[K, V]) -> Optional[Node[K, V]]:
        """Find predecessor of given node"""
        if not node:
            return None

        # If left subtree exists, find maximum in it
        if node.left:
            return self.find_maximum(node.left)

        # Otherwise, walk up until we find first right child
        current = node
        parent = node.parent
        while parent and current == parent.left:
            current = parent
            parent = parent.parent
        return parent

    def find_successor(self, node: Node[K, V]) -> Optional[Node[K, V]]:
        """Find successor of given node"""
        if not node:
            return None

        # If right subtree exists, find minimum in it
        if node.right:
            return self.find_minimum(node.right)

        # Otherwise, walk up until we find first left child
        current = node
        parent = node.parent
        while parent and current == parent.right:
            current = parent
            parent = parent.parent
        return parent

    def insert(self, key: K, data: V) -> Node[K, V]:
        """Insert new node with key and data"""
        node = Node(key=key, data=data)
        
        # Do standard BST insert
        parent = None
        current = self.root
        while current:
            parent = current
            cmp = self.comp_func(node.key, current.key)
            if cmp < 0:
                current = current.left
            else:
                current = current.right
                
        node.parent = parent
        if not parent:
            self.root = node
        else:
            if self.comp_func(node.key, parent.key) < 0:
                parent.left = node
            else:
                parent.right = node
                
        # Fix red-black properties
        self._fix_insert(node)
        return node

    def remove(self, node: Node[K, V]) -> None:
        """Remove node from tree"""
        if not node:
            return
            
        # If node has two children, replace with successor
        if node.left and node.right:
            successor = self.find_successor(node)
            if successor:
                node.key = successor.key
                node.data = successor.data
                node = successor

        # Get child (at most one) and parent
        child = node.left if node.left else node.right
        parent = node.parent
        
        # Replace node with child
        if child:
            child.parent = parent
        if not parent:
            self.root = child
        elif node == parent.left:
            parent.left = child
        else:
            parent.right = child
            
        # If we removed a black node, fix properties
        if node.color == Color.BLACK:
            self._fix_remove(child, parent)

    def _fix_insert(self, node: Node[K, V]) -> None:
        """Fix red-black tree properties after insertion"""
        while node != self.root and node.parent and node.parent.color == Color.RED:
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                if uncle and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._rotate_left(node)
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._rotate_right(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                if uncle and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._rotate_right(node)
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._rotate_left(node.parent.parent)
                    
        self.root.color = Color.BLACK

    def _fix_remove(self, node: Optional[Node[K, V]], parent: Optional[Node[K, V]]) -> None:
        """Fix red-black tree properties after removal"""
        while (node != self.root and 
               (not node or node.color == Color.BLACK)):
            if not parent:
                break
                
            if node == parent.left:
                sibling = parent.right
                if sibling and sibling.color == Color.RED:
                    sibling.color = Color.BLACK
                    parent.color = Color.RED
                    self._rotate_left(parent)
                    sibling = parent.right

                if (not sibling or
                    (not sibling.left or sibling.left.color == Color.BLACK) and
                    (not sibling.right or sibling.right.color == Color.BLACK)):
                    if sibling:
                        sibling.color = Color.RED
                    node = parent
                    parent = node.parent
                else:
                    if not sibling.right or sibling.right.color == Color.BLACK:
                        if sibling.left:
                            sibling.left.color = Color.BLACK
                        sibling.color = Color.RED
                        self._rotate_right(sibling)
                        sibling = parent.right

                    if sibling:
                        sibling.color = parent.color
                    parent.color = Color.BLACK
                    if sibling and sibling.right:
                        sibling.right.color = Color.BLACK
                    self._rotate_left(parent)
                    node = self.root
                    break
            else:
                sibling = parent.left
                if sibling and sibling.color == Color.RED:
                    sibling.color = Color.BLACK
                    parent.color = Color.RED
                    self._rotate_right(parent)
                    sibling = parent.left

                if (not sibling or
                    (not sibling.right or sibling.right.color == Color.BLACK) and
                    (not sibling.left or sibling.left.color == Color.BLACK)):
                    if sibling:
                        sibling.color = Color.RED
                    node = parent
                    parent = node.parent
                else:
                    if not sibling.left or sibling.left.color == Color.BLACK:
                        if sibling.right:
                            sibling.right.color = Color.BLACK
                        sibling.color = Color.RED
                        self._rotate_left(sibling)
                        sibling = parent.left

                    if sibling:
                        sibling.color = parent.color
                    parent.color = Color.BLACK
                    if sibling and sibling.left:
                        sibling.left.color = Color.BLACK
                    self._rotate_right(parent)
                    node = self.root
                    break

        if node:
            node.color = Color.BLACK

    def _rotate_left(self, node: Node[K, V]) -> None:
        """Rotate subtree left around node"""
        if not node or not node.right:
            return
            
        y = node.right
        node.right = y.left
        if y.left:
            y.left.parent = node
            
        y.parent = node.parent
        if not node.parent:
            self.root = y
        elif node == node.parent.left:
            node.parent.left = y
        else:
            node.parent.right = y
            
        y.left = node
        node.parent = y

    def _rotate_right(self, node: Node[K, V]) -> None:
        """Rotate subtree right around node"""
        if not node or not node.left:
            return
            
        y = node.left
        node.left = y.right
        if y.right:
            y.right.parent = node
            
        y.parent = node.parent
        if not node.parent:
            self.root = y
        elif node == node.parent.left:
            node.parent.left = y
        else:
            node.parent.right = y
            
        y.right = node
        node.parent = y

    def validate(self) -> bool:
        """Validate red-black tree properties"""
        if not self.root:
            return True
            
        # Property 1: Root must be black
        if self.root.color != Color.BLACK:
            return False
            
        # Property 2: No red node has red child
        # Property 3: All paths have same number of black nodes
        black_height = self._validate_properties(self.root)
        return black_height >= 0

    def _validate_properties(self, node: Optional[Node[K, V]]) -> int:
        """Helper for validate(), returns black-height if valid, -1 if invalid"""
        if not node:
            return 0
            
        # Check red property
        if node.color == Color.RED:
            if (node.left and node.left.color == Color.RED) or \
               (node.right and node.right.color == Color.RED):
                return -1
                
        # Check recursive properties
        left_height = self._validate_properties(node.left)
        if left_height < 0:
            return -1
            
        right_height = self._validate_properties(node.right)
        if right_height < 0:
            return -1
            
        # Heights must match
        if left_height != right_height:
            return -1
            
        # Return black-height
        return left_height + (1 if node.color == Color.BLACK else 0)
