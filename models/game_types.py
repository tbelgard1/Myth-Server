"""
Game type definitions for the Myth metaserver.

Contains data structures for game parameters and descriptions.
"""

import dataclasses
from typing import List
import struct

@dataclasses.dataclass
class NewGameParameterData:
    """Parameters for creating a new game"""
    type: int
    scoring: int
    option_flags: int
    time_limit: int
    scenario_tag: int
    difficulty_level: int
    maximum_players: int
    initial_team_random_seed: int
    maximum_teams: int
    random_seed: int
    pregame_time_limit: int
    unused: List[int]  # Length 2
    unused_short: int
    plugin_count: int
    plugin_data: bytes  # Length 512

    def __init__(self):
        """Initialize with default values"""
        self.type = 0
        self.scoring = 0
        self.option_flags = 0
        self.time_limit = 0
        self.scenario_tag = 0
        self.difficulty_level = 0
        self.maximum_players = 0
        self.initial_team_random_seed = 0
        self.maximum_teams = 0
        self.random_seed = 0
        self.pregame_time_limit = 0
        self.unused = [0, 0]
        self.unused_short = 0
        self.plugin_count = 0
        self.plugin_data = bytes(512)

    def pack(self) -> bytes:
        """Pack parameters into bytes"""
        return struct.pack('<hhLlLhhhhlll2lhh512s',
            self.type,
            self.scoring,
            self.option_flags,
            self.time_limit,
            self.scenario_tag,
            self.difficulty_level,
            self.maximum_players,
            self.initial_team_random_seed,
            self.maximum_teams,
            self.random_seed,
            self.pregame_time_limit,
            *self.unused,
            self.unused_short,
            self.plugin_count,
            self.plugin_data
        )

    @classmethod
    def unpack(cls, data: bytes) -> 'NewGameParameterData':
        """Unpack parameters from bytes"""
        params = cls()
        (params.type,
         params.scoring,
         params.option_flags,
         params.time_limit,
         params.scenario_tag,
         params.difficulty_level,
         params.maximum_players,
         params.initial_team_random_seed,
         params.maximum_teams,
         params.random_seed,
         params.pregame_time_limit,
         unused1,
         unused2,
         params.unused_short,
         params.plugin_count,
         params.plugin_data) = struct.unpack('<hhLlLhhhhlll2lhh512s', data)
        params.unused = [unused1, unused2]
        return params

@dataclasses.dataclass
class MetaserverGameDescription:
    """Description of a game on the metaserver"""
    parameters: NewGameParameterData
    public_tags_checksum: int
    private_tags_checksum: int
    flags: int
    player_count: int

    def __init__(self):
        """Initialize with default values"""
        self.parameters = NewGameParameterData()
        self.public_tags_checksum = 0
        self.private_tags_checksum = 0
        self.flags = 0
        self.player_count = 0

    def pack(self) -> bytes:
        """Pack description into bytes"""
        return (
            self.parameters.pack() +
            struct.pack('<llHB',
                self.public_tags_checksum,
                self.private_tags_checksum,
                self.flags,
                self.player_count
            )
        )

    @classmethod
    def unpack(cls, data: bytes) -> 'MetaserverGameDescription':
        """Unpack description from bytes"""
        desc = cls()
        params_size = struct.calcsize('<hhLlLhhhhlll2lhh512s')
        desc.parameters = NewGameParameterData.unpack(data[:params_size])
        
        (desc.public_tags_checksum,
         desc.private_tags_checksum,
         desc.flags,
         desc.player_count) = struct.unpack('<llHB', data[params_size:])
        return desc
