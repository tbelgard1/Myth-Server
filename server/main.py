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

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import os
import sys
import socket
import select
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import struct
from datetime import datetime
import argparse

from core.utils.environment import Environment
from core.models.metaserver_common_structs import MetaserverCommonStructs
from core.models.stats import Stats
from core.auth.auth import Authentication
from core.models.bungie_net_player import BungieNetPlayerDatum
from core.models.bungie_net_order import BungieNetOrderDatum
from core.services.user_service import UserService
from core.services.order_service import OrderService
from core.services.room_list_service import RoomListService
from core.networking.byte_swapping import ByteSwapping
from core.services.game_service import GameService
from core.services.rank_service import RankService
from core.networking.packets.metaserver import MetaserverPackets
from core.models.metaserver_codes import MetaserverCodes
from core.networking.packets.room import RoomPackets
from core.networking.packets.web import WebServerPackets
from core.networking.queues import NetworkQueues
from core.networking.encode import EncodePackets

# Constants
MAXIMUM_OUTSTANDING_REQUESTS = 16
MAXIMUM_BAD_LOGIN_ATTEMPTS = 1
NEW_USER_LOGIN_KEY_SIZE = 16
NEW_ORDER_KEY_SIZE = 12
PASSWORD_CHANGE_LOGIN_KEY_SIZE = 8
STDIN_SOCKET = 0
INCOMING_QUEUE_SIZE = 65536
OUTGOING_QUEUE_SIZE = 65536
MAXIMUM_PACKET_LENGTH = 32767
TICKS_BEFORE_UPDATING_ROOM_LIST = 45 * Environment.MACHINE_TICKS_PER_SECOND
SECONDS_TO_WAIT_ON_SELECT = 60
CLASS_C_NETMASK = 0xffffff00
MINIMUM_NUMBER_OF_PLAYERS_IN_ORDER = 3
TIME_TO_EXPIRE_ORDER = 60 * 60 * 24 * 10
MINIMUM_PATCH_VERSION_REQUIRED = 3

# Time constants
STATS_EXPORT_PERIOD_IN_SECONDS = 4 * 60 * 60  # 4 hours
RERANK_PERIOD_IN_SECONDS = 2 * 60 * 60  # 2 hours
ONE_DAY = 60 * 60 * 24
ONE_MINUTE = 60

# Client types
CLIENT_TYPE_PLAYER = 0
CLIENT_TYPE_ROOM = 1
CLIENT_TYPE_WEB = 2
CLIENT_TYPE_UNUSED = 3
NUMBER_OF_CLIENT_TYPES = 4

@dataclass
class UserParameters:
    """Configuration parameters for the user server."""
    userd_port: int = 0
    web_port: int = 0
    room_port: int = 0
    rooms: List[Any] = field(default_factory=list)
    new_user_login: str = ""
    room_login: str = ""
    clients: List[Any] = field(default_factory=list)
    motd: str = ""
    stats_mail_address: str = ""

@dataclass
class ServerGlobals:
    """Global server state."""
    server_socket: socket.socket = None
    room_socket: socket.socket = None
    web_socket: socket.socket = None
    set_size: int = 0
    server_address: Tuple[str, int] = None
    read_fds: List[socket.socket] = field(default_factory=list)
    write_fds: List[socket.socket] = field(default_factory=list)

class MetaServer:
    def __init__(self):
        self.user_parameters = UserParameters()
        self.server_globals = ServerGlobals()
        self.local_area_network = 0
        self.logger = logging.getLogger("MetaServer")
        self.b_send_mail = True
        
    def parse_command_arguments(self, args: List[str]) -> None:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description="Myth II Metaserver")
        parser.add_argument("--userd-port", type=int, default=3453,
                          help="Port for user daemon")
        parser.add_argument("--web-port", type=int, default=3454,
                          help="Port for web interface")
        parser.add_argument("--room-port", type=int, default=3455,
                          help="Port for game rooms")
        parser.add_argument("--no-mail", action="store_true",
                          help="Disable mail notifications")
        
        parsed_args = parser.parse_args(args)
        self.user_parameters.userd_port = parsed_args.userd_port
        self.user_parameters.web_port = parsed_args.web_port
        self.user_parameters.room_port = parsed_args.room_port
        self.b_send_mail = not parsed_args.no_mail

    def init_server(self) -> None:
        """Initialize the server sockets and configuration."""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create server sockets
        try:
            self.server_globals.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_globals.server_socket.setblocking(False)
            self.server_globals.server_socket.bind(('', self.user_parameters.userd_port))
            self.server_globals.server_socket.listen(5)
            
            self.server_globals.room_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_globals.room_socket.setblocking(False)
            self.server_globals.room_socket.bind(('', self.user_parameters.room_port))
            self.server_globals.room_socket.listen(5)
            
            self.server_globals.web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_globals.web_socket.setblocking(False)
            self.server_globals.web_socket.bind(('', self.user_parameters.web_port))
            self.server_globals.web_socket.listen(5)
            
        except socket.error as e:
            self.logger.error(f"Socket error: {e}")
            sys.exit(1)
        
        # Get local network address
        hostname = socket.gethostname()
        try:
            host_info = socket.gethostbyname_ex(hostname)
            address = socket.inet_aton(host_info[2][0])
            self.local_area_network = struct.unpack("!L", address)[0] & 0xFFFFFF00
            self.logger.info(f"LAN: 0x{self.local_area_network:X} - ({host_info[0]})")
        except socket.error as e:
            self.logger.error(f"LAN Error: {e}")
            sys.exit(1)

    def handle_incoming_connections(self, fd: socket.socket) -> None:
        """Handle new incoming client connections."""
        try:
            client_socket, client_address = fd.accept()
            client_socket.setblocking(False)
            
            client_type = CLIENT_TYPE_PLAYER
            if fd == self.server_globals.room_socket:
                client_type = CLIENT_TYPE_ROOM
            elif fd == self.server_globals.web_socket:
                client_type = CLIENT_TYPE_WEB
                
            if self.valid_remote_host(client_address[0], client_type):
                self.add_client(client_socket, client_address[0], client_address[1], client_type)
            else:
                client_socket.close()
                
        except socket.error as e:
            self.logger.error(f"Error accepting connection: {e}")

    def valid_remote_host(self, host: str, client_type: int) -> bool:
        """Check if a remote host is allowed to connect."""
        try:
            host_bytes = socket.inet_aton(host)
            host_int = struct.unpack("!L", host_bytes)[0]
            
            # Allow local network connections
            if (host_int & CLASS_C_NETMASK) == self.local_area_network:
                return True
                
            # Additional validation logic here
            # For now, accept all connections
            return True
            
        except socket.error:
            return False

    def run_server(self) -> None:
        """Main server loop."""
        while True:
            # Prepare file descriptor sets
            read_fds = [
                self.server_globals.server_socket,
                self.server_globals.room_socket,
                self.server_globals.web_socket
            ]
            write_fds = []
            
            # Add client sockets
            for client in self.user_parameters.clients:
                read_fds.append(client.socket)
                if client.outgoing.size > 0:
                    write_fds.append(client.socket)
            
            try:
                readable, writable, _ = select.select(
                    read_fds,
                    write_fds,
                    [],
                    SECONDS_TO_WAIT_ON_SELECT
                )
                
                # Handle readable sockets
                for fd in readable:
                    if fd in (self.server_globals.server_socket,
                             self.server_globals.room_socket,
                             self.server_globals.web_socket):
                        self.handle_incoming_connections(fd)
                    else:
                        self.handle_client_connections(fd)
                
                # Handle writable sockets
                for fd in writable:
                    self.handle_write_sockets(fd)
                    
            except select.error as e:
                self.logger.error(f"Select error: {e}")
                continue
            
            # Periodic tasks
            self.update_server_state()

    def main(self, argv: List[str]) -> int:
        """Main entry point for the server."""
        try:
            self.parse_command_arguments(argv[1:])
            self.init_server()
            self.run_server()
            return 0
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            return 1

def main():
    """Entry point when run as a script."""
    server = MetaServer()
    sys.exit(server.main(sys.argv))

if __name__ == "__main__":
    main()
