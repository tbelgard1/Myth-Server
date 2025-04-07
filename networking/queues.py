"""
Network queue implementation for Myth metaserver.
Provides queues for managing network packets and connections.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class NetworkQueueEntry:
    """Entry in a network queue
    
    Attributes:
        data: Packet data
        size: Size of data in bytes
        next: Next entry in queue
        prev: Previous entry in queue
    """
    data: bytes
    size: int
    next: Optional['NetworkQueueEntry'] = None
    prev: Optional['NetworkQueueEntry'] = None

class NetworkQueue:
    """Double-ended queue for network packets
    
    Attributes:
        head: First entry in queue
        tail: Last entry in queue
        size: Number of entries in queue
        total_bytes: Total bytes of data in queue
    """
    
    def __init__(self):
        """Initialize empty queue"""
        self.head: Optional[NetworkQueueEntry] = None
        self.tail: Optional[NetworkQueueEntry] = None
        self.size: int = 0
        self.total_bytes: int = 0
        self._lock = asyncio.Lock()
        
    async def push_front(self, data: bytes) -> None:
        """Add entry to front of queue
        
        Args:
            data: Packet data to add
        """
        async with self._lock:
            entry = NetworkQueueEntry(data, len(data))
            
            if self.head is None:
                # Empty queue
                self.head = self.tail = entry
            else:
                # Link new entry
                entry.next = self.head
                self.head.prev = entry
                self.head = entry
                
            self.size += 1
            self.total_bytes += entry.size
            
    async def push_back(self, data: bytes) -> None:
        """Add entry to back of queue
        
        Args:
            data: Packet data to add
        """
        async with self._lock:
            entry = NetworkQueueEntry(data, len(data))
            
            if self.tail is None:
                # Empty queue
                self.head = self.tail = entry
            else:
                # Link new entry
                entry.prev = self.tail
                self.tail.next = entry
                self.tail = entry
                
            self.size += 1
            self.total_bytes += entry.size
            
    async def pop_front(self) -> Optional[bytes]:
        """Remove and return entry from front of queue
        
        Returns:
            Packet data, or None if queue is empty
        """
        async with self._lock:
            if self.head is None:
                return None
                
            # Get data from head
            data = self.head.data
            
            # Update queue
            self.size -= 1
            self.total_bytes -= self.head.size
            
            # Update links
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            else:
                self.head.prev = None
                
            return data
            
    async def pop_back(self) -> Optional[bytes]:
        """Remove and return entry from back of queue
        
        Returns:
            Packet data, or None if queue is empty
        """
        async with self._lock:
            if self.tail is None:
                return None
                
            # Get data from tail
            data = self.tail.data
            
            # Update queue
            self.size -= 1
            self.total_bytes -= self.tail.size
            
            # Update links
            self.tail = self.tail.prev
            if self.tail is None:
                self.head = None
            else:
                self.tail.next = None
                
            return data
            
    def peek_front(self) -> Optional[bytes]:
        """Return data from front of queue without removing
        
        Returns:
            Packet data, or None if queue is empty
        """
        return self.head.data if self.head else None
        
    def peek_back(self) -> Optional[bytes]:
        """Return data from back of queue without removing
        
        Returns:
            Packet data, or None if queue is empty
        """
        return self.tail.data if self.tail else None
        
    def clear(self) -> None:
        """Remove all entries from queue"""
        self.head = self.tail = None
        self.size = self.total_bytes = 0
        
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.size == 0
        
    def __len__(self) -> int:
        """Return number of entries in queue"""
        return self.size
