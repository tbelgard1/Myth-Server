"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details

The metaserver code changes that fall outside the original Bungie.net metaserver code 
license were written and are copyright 2002, 2003 of the following individuals:

Copyright (c) 2002, 2003 Alan Wagner
Copyright (c) 2002 Vishvananda Ishaya
Copyright (c) 2003 Bill Keirstead
"""

import os
import struct
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import IntEnum

from ..models.bungie_net_player import BungieNetPlayerDatum, BungieNetOnlinePlayerData
from ..models.stats import PlayerStats
from ..utils.constants import MAXIMUM_PLAYER_NAME_LENGTH, MAXIMUM_BUDDIES, MAXIMUM_PACKED_PLAYER_DATA_LENGTH
from ..utils.rb_tree import RBTree
from ..utils.sl_list import SLList, SLListElement

logger = logging.getLogger(__name__)

# Constants
BUNGIE_NET_USER_DB_SIGNATURE = 0x504c4159
MAXIMUM_PLAYER_SEARCH_RESPONSES = 50

@dataclass
class UserQuery:
    """User query structure for searching players"""
    string: str = field(default="")
    buddy_ids: List[int] = field(default_factory=lambda: [0] * MAXIMUM_BUDDIES)
    order: int = 0

@dataclass
class UserQueryResponse:
    """Response structure for user queries"""
    match_score: int = 0
    aux_data: Any = None  # MetaserverPlayerAuxData
    player_data: bytes = field(default_factory=lambda: bytearray(MAXIMUM_PACKED_PLAYER_DATA_LENGTH))

@dataclass
class OrderMemberListData:
    """Data structure for order member list"""
    player_id: int = 0

@dataclass
class OrderListData:
    """Data structure for order list"""
    order_index: int = 0
    member_list: SLList = field(default_factory=SLList)

@dataclass
class BungieNetUserDBHeader:
    """Header structure for user database"""
    player_count: int = 0
    unused: List[int] = field(default_factory=lambda: [0] * 40)

@dataclass
class BungieNetUserDBEntry:
    """Entry structure for user database"""
    signature: int = BUNGIE_NET_USER_DB_SIGNATURE
    player: BungieNetPlayerDatum = field(default_factory=BungieNetPlayerDatum)

@dataclass
class BungieNetLoginTreeData:
    """Data structure for login tree"""
    login: str = ""
    online_data_index: int = 0
    fpos: int = 0

class UserDatabase:
    """User database management class"""
    def __init__(self):
        self.order_list: Optional[SLList] = None
        self.online_player_data: List[BungieNetOnlinePlayerData] = []
        self.fd_user_db: int = -1
        self.total_players: int = 0
        self.response_list: List[UserQueryResponse] = [UserQueryResponse() for _ in range(MAXIMUM_PLAYER_SEARCH_RESPONSES)]
        self.present_order_list: Optional[SLListElement] = None
        self.search_player_id: int = -1
        self.login_tree = RBTree(self._login_tree_comp_func)

    def create_user_database(self) -> bool:
        """Create a new user database"""
        try:
            self.fd_user_db = os.open("users.db", os.O_CREAT | os.O_RDWR)
            header = BungieNetUserDBHeader()
            os.write(self.fd_user_db, struct.pack("I40I", header.player_count, *header.unused))
            return True
        except OSError as e:
            logger.error(f"Failed to create user database: {e}")
            return False

    def initialize_user_database(self) -> bool:
        """Initialize the user database"""
        try:
            if not self.order_list_new():
                return False

            self.fd_user_db = os.open("users.db", os.O_RDWR)
            header = BungieNetUserDBHeader()
            header_data = os.read(self.fd_user_db, struct.calcsize("I40I"))
            header.player_count = struct.unpack("I", header_data[:4])[0]

            self.total_players = header.player_count
            self.online_player_data = [BungieNetOnlinePlayerData() for _ in range(self.total_players)]

            # Read and initialize all player data
            for i in range(self.total_players):
                entry_pos = os.lseek(self.fd_user_db, 0, os.SEEK_CUR)
                signature = struct.unpack("I", os.read(self.fd_user_db, 4))[0]
                
                if signature == BUNGIE_NET_USER_DB_SIGNATURE:
                    player_data = os.read(self.fd_user_db, BungieNetPlayerDatum.size())
                    player = BungieNetPlayerDatum.from_bytes(player_data)
                    self.add_entry_to_login_tree(player, entry_pos)
                    
            return True
            
        except OSError as e:
            logger.error(f"Failed to initialize user database: {e}")
            return False

    def shutdown_user_database(self) -> None:
        """Shutdown and cleanup the user database"""
        if self.fd_user_db != -1:
            os.close(self.fd_user_db)
            self.fd_user_db = -1

    def get_first_player_in_order(self, order_index: int) -> Optional[BungieNetPlayerDatum]:
        """Get the first player in a specific order"""
        if not self.order_list:
            return None
            
        element = self.order_list.head
        while element:
            data = element.data
            if data.order_index == order_index and data.member_list:
                member = data.member_list.head
                if member:
                    player = BungieNetPlayerDatum()
                    if self.get_player_information(None, member.data.player_id, player):
                        self.present_order_list = member
                        return player
            element = element.next
            
        return None

    def get_next_player_in_order(self, key: Any) -> Optional[BungieNetPlayerDatum]:
        """Get the next player in the order"""
        if not self.present_order_list or not self.present_order_list.next:
            return None
            
        self.present_order_list = self.present_order_list.next
        player = BungieNetPlayerDatum()
        if self.get_player_information(None, self.present_order_list.data.player_id, player):
            return player
            
        return None

    def get_user_count(self) -> int:
        """Get total number of users"""
        return self.total_players

    def get_online_player_information(self, player_id: int) -> Optional[BungieNetOnlinePlayerData]:
        """Get online player information"""
        if 0 < player_id <= self.total_players:
            return self.online_player_data[player_id - 1]
        return None

    def get_player_information(self, login_name: Optional[str], player_id: int, 
                             player: BungieNetPlayerDatum) -> bool:
        """Get player information by login name or ID"""
        try:
            if login_name:
                data = BungieNetLoginTreeData(login=login_name)
                node = self.login_tree.search(data)
                if node:
                    os.lseek(self.fd_user_db, node.data.fpos, os.SEEK_SET)
                    signature = struct.unpack("I", os.read(self.fd_user_db, 4))[0]
                    if signature == BUNGIE_NET_USER_DB_SIGNATURE:
                        player_data = os.read(self.fd_user_db, BungieNetPlayerDatum.size())
                        player.__dict__.update(BungieNetPlayerDatum.from_bytes(player_data).__dict__)
                        return True
            elif player_id > 0 and player_id <= self.total_players:
                offset = (player_id - 1) * (4 + BungieNetPlayerDatum.size()) + struct.calcsize("I41I")
                os.lseek(self.fd_user_db, offset, os.SEEK_SET)
                signature = struct.unpack("I", os.read(self.fd_user_db, 4))[0]
                if signature == BUNGIE_NET_USER_DB_SIGNATURE:
                    player_data = os.read(self.fd_user_db, BungieNetPlayerDatum.size())
                    player.__dict__.update(BungieNetPlayerDatum.from_bytes(player_data).__dict__)
                    return True
                    
            return False
            
        except OSError as e:
            logger.error(f"Failed to get player information: {e}")
            return False

    def update_player_information(self, login_name: Optional[str], player_id: int, 
                                logged_in_flag: bool, player: BungieNetPlayerDatum) -> bool:
        """Update player information"""
        try:
            if login_name:
                data = BungieNetLoginTreeData(login=login_name)
                node = self.login_tree.search(data)
                if node:
                    os.lseek(self.fd_user_db, node.data.fpos, os.SEEK_SET)
                    os.write(self.fd_user_db, struct.pack("I", BUNGIE_NET_USER_DB_SIGNATURE))
                    os.write(self.fd_user_db, player.to_bytes())
                    if logged_in_flag:
                        self.online_player_data[node.data.online_data_index].logged_in_flag = True
                        self.online_player_data[node.data.online_data_index].name = player.name
                        self.online_player_data[node.data.online_data_index].aux_data = player.aux_data
                    return True
            elif player_id > 0 and player_id <= self.total_players:
                offset = (player_id - 1) * (4 + BungieNetPlayerDatum.size()) + struct.calcsize("I41I")
                os.lseek(self.fd_user_db, offset, os.SEEK_SET)
                os.write(self.fd_user_db, struct.pack("I", BUNGIE_NET_USER_DB_SIGNATURE))
                os.write(self.fd_user_db, player.to_bytes())
                if logged_in_flag:
                    self.online_player_data[player_id - 1].logged_in_flag = True
                    self.online_player_data[player_id - 1].name = player.name
                    self.online_player_data[player_id - 1].aux_data = player.aux_data
                return True
        except OSError as e:
            logger.error(f"Failed to update player information: {e}")
        return False

    def new_user(self, player: BungieNetPlayerDatum) -> bool:
        """Create a new user"""
        try:
            self.total_players += 1
            offset = (self.total_players - 1) * (struct.calcsize("I") + BungieNetPlayerDatum.size()) + struct.calcsize("I41I")
            
            # Update header
            os.lseek(self.fd_user_db, 0, os.SEEK_SET)
            os.write(self.fd_user_db, struct.pack("I", self.total_players))
            
            # Write new user
            os.lseek(self.fd_user_db, offset, os.SEEK_SET)
            data = struct.pack("I", BUNGIE_NET_USER_DB_SIGNATURE) + player.to_bytes()
            os.write(self.fd_user_db, data)
            
            # Update login tree
            self.add_entry_to_login_tree(player, offset)
            
            # Extend online player data array
            self.online_player_data.append(BungieNetOnlinePlayerData())
            return True
        except OSError as e:
            logger.error(f"Failed to create new user: {e}")
            self.total_players -= 1
            return False

    def query_user_database(self, query: UserQuery) -> List[UserQueryResponse]:
        """Query the user database"""
        responses: List[UserQueryResponse] = []
        
        for i in range(self.total_players):
            player = BungieNetPlayerDatum()
            if not self.get_player_information(None, i + 1, player):
                continue
                
            # Match by name
            if query.string.lower() in player.name.lower():
                response = UserQueryResponse()
                response.match_score = len(query.string)
                response.aux_data = player.aux_data
                responses.append(response)
                
            # Match by buddy list
            if player.player_id in query.buddy_ids:
                response = UserQueryResponse()
                response.match_score = MAXIMUM_PLAYER_NAME_LENGTH + 1
                response.aux_data = player.aux_data
                responses.append(response)
                
            if len(responses) >= MAXIMUM_PLAYER_SEARCH_RESPONSES:
                break
                
        return sorted(responses, key=lambda x: x.match_score, reverse=True)

    def is_player_online(self, player_id: int) -> bool:
        """Check if a player is online"""
        if 0 < player_id <= self.total_players:
            return self.online_player_data[player_id - 1].logged_in_flag
        return False

    def get_player_count_in_order(self, order_index: int) -> int:
        """Get number of players in an order"""
        count = 0
        if self.order_list:
            element = self.order_list.head
            while element:
                data = element.data
                if data.order_index == order_index and data.member_list:
                    member = data.member_list.head
                    while member:
                        count += 1
                        member = member.next
                element = element.next
        return count

    def _login_tree_comp_func(self, k0: Any, k1: Any) -> int:
        """Comparison function for login tree"""
        return (k0.login > k1.login) - (k0.login < k1.login)

    def add_entry_to_login_tree(self, player: BungieNetPlayerDatum, fpos: int) -> bool:
        """Add an entry to the login tree"""
        data = BungieNetLoginTreeData(
            login=player.login,
            online_data_index=player.player_id - 1,
            fpos=fpos
        )
        return self.login_tree.insert(data)

    def order_list_new(self) -> bool:
        """Create a new order list"""
        self.order_list = SLList()
        return True

# Global instance
user_database = UserDatabase()
