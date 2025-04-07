#!/usr/bin/env python3
"""
Myth Server Management Script
Handles starting and stopping Myth server components
"""

import argparse
import asyncio
import os
import signal
import sys
from typing import List, Optional
import psutil

# Import server modules
from core.server.main import start_user_server
from core.services.room_service import start_room_server
from core.services.game_search_service import start_game_search_server

class MythServer:
    def __init__(self):
        self.processes: List[asyncio.subprocess.Process] = []
        
    async def start_servers(self):
        """Start all server components"""
        print("Starting Myth server components...")
        
        # Start user server
        print("Starting user server...")
        await start_user_server()
        
        # Start room servers
        print("Starting room servers...")
        rooms_file = "rooms.lst"
        if not os.path.exists(rooms_file):
            print(f"Error: {rooms_file} not found!")
            return
            
        with open(rooms_file, 'r') as f:
            num_rooms = sum(1 for line in f if line.strip())
            
        print(f"Starting {num_rooms} room servers...")
        for i in range(num_rooms):
            await start_room_server()
            
        # Start game search server
        print("Starting game search server...")
        await start_game_search_server()
        
        print("All servers started successfully!")
        
    def stop_servers(self):
        """Stop all server components"""
        print("Stopping Myth server components...")
        
        # Find and stop Python processes running our servers
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(x in str(proc.info['cmdline']) for x in 
                    ['roomd_new.py', 'main.py', 'game_search_server.py']):
                    print(f"Stopping process {proc.info['pid']}")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        print("All servers stopped!")

def main():
    parser = argparse.ArgumentParser(description="Myth Server Management")
    parser.add_argument('action', choices=['start', 'stop'], 
                      help='Action to perform (start or stop servers)')
    args = parser.parse_args()
    
    server = MythServer()
    
    if args.action == 'start':
        asyncio.run(server.start_servers())
    else:  # stop
        server.stop_servers()

if __name__ == "__main__":
    main()
