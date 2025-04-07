"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details

The metaserver code changes that fall outside the original Bungie.net metaserver code 
license were written and are copyright 2002, 2003 of the following individuals:

Copyright (c) 2002, 2003 Alan Wagner
Copyright (c) 2002 Vishvananda Ishaya
Copyright (c) 2003 Bill Keirstead
All rights reserved.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

from ..utils.environment import Environment
from ..models.metaserver_common_structs import MetaserverCommonStructs
from ..utils.rb_tree import RBTree, RBNode
from ..models.stats import Stats
from ..models.bungie_net_player import BungieNetPlayerDatum
from ..models.bungie_net_order import BungieNetOrderDatum

# Constants
BUNGIE_NET_ORDER_DB_SIGNATURE = 0x4f524452  # 'ORDR'
UNUSED_ORDER_ID = 0xFFFFFFFF
MAXIMUM_ORDER_NAME_LENGTH = 32

@dataclass
class OrderDatabaseHeader:
    """Header structure for the order database."""
    order_count: int = 0
    unused: List[int] = field(default_factory=lambda: [0] * 40)

@dataclass
class OrderDatabaseEntry:
    """Entry structure for the order database."""
    signature: int = BUNGIE_NET_ORDER_DB_SIGNATURE
    order: BungieNetOrderDatum = field(default_factory=BungieNetOrderDatum)

@dataclass
class OrderNameTreeData:
    """Data structure for order name tree nodes."""
    order_name: str = ""
    file_position: int = 0

class OrderDatabase:
    """Handles the order database operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("OrderDatabase")
        self.db_file = None
        self.total_orders = 0
        self.order_name_tree = RBTree("order name tree")
        self.order_id_indexes: Dict[int, int] = {}  # Maps order_id to file position
        self.search_order_id = -1

    def get_orders_db_file_name(self) -> str:
        """Get the path to the orders database file."""
        return str(Path(Environment.get_data_dir()) / "orders.db")

    def create_order_database(self) -> bool:
        """Create a new order database file."""
        try:
            header = OrderDatabaseHeader()
            file_name = self.get_orders_db_file_name()
            
            with open(file_name, "wb") as f:
                # Write header
                f.write(header.order_count.to_bytes(4, 'little'))
                for unused in header.unused:
                    f.write(unused.to_bytes(4, 'little'))
                    
            self.db_file = open(file_name, "r+b")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create order database: {e}")
            return False

    def initialize_order_database(self) -> bool:
        """Initialize the order database and load existing entries."""
        try:
            file_name = self.get_orders_db_file_name()
            self.db_file = open(file_name, "r+b")
            
            # Read header
            self.db_file.seek(0)
            header_bytes = self.db_file.read(4)  # Read order count
            order_count = int.from_bytes(header_bytes, 'little')
            
            # Skip unused header space
            self.db_file.seek(4 + 40 * 4)  # Move past header
            
            # Read all entries
            for i in range(order_count):
                entry_pos = self.db_file.tell()
                signature = int.from_bytes(self.db_file.read(4), 'little')
                
                if signature == BUNGIE_NET_ORDER_DB_SIGNATURE:
                    order = BungieNetOrderDatum.from_bytes(self.db_file.read())
                    if order.order_id != UNUSED_ORDER_ID:
                        self.order_id_indexes[order.order_id] = entry_pos
                        self._add_entry_to_order_name_tree(order, entry_pos)
                        
            self.total_orders = order_count
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize order database: {e}")
            return False

    def shutdown_order_database(self) -> None:
        """Close the order database."""
        if self.db_file:
            self.db_file.close()
            self.db_file = None

    def get_order_count(self) -> int:
        """Get the total number of orders in the database."""
        return self.total_orders

    def get_first_order_information(self, order: BungieNetOrderDatum) -> bool:
        """Get information about the first order in the database."""
        self.search_order_id = 1
        return self.get_next_order_information(order)

    def get_next_order_information(self, order: BungieNetOrderDatum) -> bool:
        """Get information about the next order in the database."""
        while self.search_order_id <= self.total_orders:
            if self.get_order_information(None, self.search_order_id, order):
                self.search_order_id += 1
                return True
            self.search_order_id += 1
        return False

    def get_order_information(self, order_name: Optional[str], order_id: int, 
                            order: BungieNetOrderDatum) -> bool:
        """Get order information by name or ID."""
        try:
            if order_id and order_id in self.order_id_indexes:
                file_pos = self.order_id_indexes[order_id]
                self.db_file.seek(file_pos)
                signature = int.from_bytes(self.db_file.read(4), 'little')
                if signature == BUNGIE_NET_ORDER_DB_SIGNATURE:
                    order_data = BungieNetOrderDatum.from_bytes(self.db_file.read())
                    if order_data.order_id != UNUSED_ORDER_ID:
                        order.__dict__.update(order_data.__dict__)
                        return True
                        
            elif order_name:
                node = self.order_name_tree.search(order_name)
                if node:
                    data: OrderNameTreeData = node.data
                    self.db_file.seek(data.file_position)
                    signature = int.from_bytes(self.db_file.read(4), 'little')
                    if signature == BUNGIE_NET_ORDER_DB_SIGNATURE:
                        order_data = BungieNetOrderDatum.from_bytes(self.db_file.read())
                        if order_data.order_id != UNUSED_ORDER_ID:
                            order.__dict__.update(order_data.__dict__)
                            return True
                            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to get order information: {e}")
            return False

    def update_order_information(self, order_name: Optional[str], order_id: int, 
                               order: BungieNetOrderDatum) -> bool:
        """Update order information in the database."""
        try:
            if order_id and order_id in self.order_id_indexes:
                file_pos = self.order_id_indexes[order_id]
                self.db_file.seek(file_pos)
                self.db_file.write(BUNGIE_NET_ORDER_DB_SIGNATURE.to_bytes(4, 'little'))
                self.db_file.write(order.to_bytes())
                return True
                
            elif order_name:
                node = self.order_name_tree.search(order_name)
                if node:
                    data: OrderNameTreeData = node.data
                    self.db_file.seek(data.file_position)
                    self.db_file.write(BUNGIE_NET_ORDER_DB_SIGNATURE.to_bytes(4, 'little'))
                    self.db_file.write(order.to_bytes())
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update order information: {e}")
            return False

    def new_order(self, order: BungieNetOrderDatum) -> bool:
        """Create a new order in the database."""
        try:
            # Check if order name already exists
            if self.order_name_tree.search(order.name):
                return False

            # Update header
            self.db_file.seek(0)
            self.total_orders += 1
            self.db_file.write(self.total_orders.to_bytes(4, 'little'))

            # Write new order entry
            file_pos = 4 + 40 * 4 + (self.total_orders - 1) * (4 + BungieNetOrderDatum.size())
            self.db_file.seek(file_pos)
            
            order.order_id = self.total_orders
            order.founding_date = int(time.time())
            
            self.db_file.write(BUNGIE_NET_ORDER_DB_SIGNATURE.to_bytes(4, 'little'))
            self.db_file.write(order.to_bytes())
            
            # Update indexes
            self.order_id_indexes[order.order_id] = file_pos
            self._add_entry_to_order_name_tree(order, file_pos)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create new order: {e}")
            return False

    def mark_order_as_unused(self, order_id: int) -> None:
        """Mark an order as unused in the database."""
        order = BungieNetOrderDatum()
        if self.get_order_information(None, order_id, order):
            order.order_id = UNUSED_ORDER_ID
            self.update_order_information(None, order_id, order)

    def _add_entry_to_order_name_tree(self, order: BungieNetOrderDatum, file_pos: int) -> bool:
        """Add an entry to the order name tree."""
        try:
            data = OrderNameTreeData(order.name, file_pos)
            self.order_name_tree.insert(order.name.lower(), data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add entry to order name tree: {e}")
            return False

# Global instance
order_database = OrderDatabase()
