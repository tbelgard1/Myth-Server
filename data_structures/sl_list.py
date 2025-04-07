"""
Singly-linked list implementation for Myth metaserver.

A singly-linked list implementation with search capabilities.
Each element has a key for searching/sorting and associated data.
This is a modern Python implementation using generics and best practices.

Features:
- Generic type parameters for keys and data
- O(1) insertion at end
- O(n) search by key
- Iterator support
- Debug dumping
"""

from typing import TypeVar, Generic, Optional, Callable, Any
import dataclasses
import logging

logger = logging.getLogger(__name__)

# Constants
MAX_SL_LIST_NAME_LENGTH = 31

# Type variables for generics
T = TypeVar('T')  # Type of data
K = TypeVar('K')  # Type of key

@dataclasses.dataclass
class ListElement(Generic[T, K]):
    """A single element in a singly-linked list"""
    data: T
    key: K
    next: Optional['ListElement[T, K]'] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ListElement):
            return NotImplemented
        return self.data == other.data and self.key == other.key

class SinglyLinkedList(Generic[T, K]):
    """A singly-linked list implementation with search capabilities
    
    This is a modern Python implementation of the original C sl_list.
    It uses generics for type safety and implements Python best practices.
    """

    def __init__(self, name: str, comp_func: Callable[[K, K], int]):
        """Initialize a new singly-linked list
        
        Args:
            name: Name of the list (max 31 chars)
            comp_func: Comparison function for keys, should return:
                      - negative if a < b
                      - 0 if a == b
                      - positive if a > b
        """
        if not name or len(name) > MAX_SL_LIST_NAME_LENGTH:
            raise ValueError(f"Name must be 1-{MAX_SL_LIST_NAME_LENGTH} characters")
        if not comp_func:
            raise ValueError("Must provide comparison function")
            
        self.name = name[:MAX_SL_LIST_NAME_LENGTH]
        self.comp_func = comp_func
        self.head: Optional[ListElement[T, K]] = None

    def new_element(self, data: T, key: K) -> ListElement[T, K]:
        """Create a new list element
        
        Args:
            data: Data to store in element
            key: Key for searching/sorting
            
        Returns:
            New list element
        """
        if data is None or key is None:
            raise ValueError("Data and key must not be None")
        return ListElement(data, key)

    def get_head(self) -> Optional[ListElement[T, K]]:
        """Get the first element
        
        Returns:
            Head element or None if list is empty
        """
        return self.head

    def search(self, key: K) -> Optional[ListElement[T, K]]:
        """Search for an element by key
        
        Args:
            key: Key to search for
            
        Returns:
            Matching element or None if not found
        """
        current = self.head
        while current:
            if self.comp_func(current.key, key) == 0:
                return current
            current = current.next
        return None

    def get_next(self, element: ListElement[T, K]) -> Optional[ListElement[T, K]]:
        """Get next element after the given one
        
        Args:
            element: Current element
            
        Returns:
            Next element or None if at end
        """
        if not isinstance(element, ListElement):
            raise TypeError("element must be a ListElement")
        return element.next

    def insert(self, element: ListElement[T, K]) -> None:
        """Insert element at end of list
        
        Args:
            element: Element to insert
        """
        if not isinstance(element, ListElement):
            raise TypeError("element must be a ListElement")
        if element.next is not None:
            raise ValueError("Element must not already be in a list")

        if not self.head:
            self.head = element
            return

        # Find last element
        current = self.head
        while current.next:
            current = current.next
        current.next = element

    def remove(self, element: ListElement[T, K]) -> None:
        """Remove element from list
        
        Args:
            element: Element to remove
            
        Raises:
            ValueError: If element not in list
        """
        if not isinstance(element, ListElement):
            raise TypeError("element must be a ListElement")

        if self.head == element:
            self.head = element.next
            element.next = None
            return

        # Find element
        current = self.head
        while current and current.next != element:
            current = current.next

        if not current:
            raise ValueError("Element not in list")

        current.next = element.next
        element.next = None

    def __iter__(self):
        """Iterate through list elements"""
        current = self.head
        while current:
            yield current
            current = current.next

    def __len__(self) -> int:
        """Get number of elements in list"""
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

    def dump(self) -> None:
        """Debug dump of list contents"""
        logger.debug(f"List {self.name}:")
        for i, element in enumerate(self):
            logger.debug(f"Element {i}: data={element.data}, key={element.key}")
