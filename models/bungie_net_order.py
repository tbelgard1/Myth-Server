"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details

Converted to Python by Codeium
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from .bungie_net_structures import BungieNetPlayerScoreDatum

# Constants
MAXIMUM_ORDER_NAME_LENGTH = 31
MAXIMUM_ORDER_MOTTO_LENGTH = 511
MAXIMUM_ORDER_URL_LENGTH = 127
MAXIMUM_ORDER_CONTACT_EMAIL_LENGTH = 127
MAXIMUM_PASSWORD_LENGTH = 31  # From original codebase
MAXIMUM_NUMBER_OF_GAME_TYPES = 16  # From original codebase

@dataclass
class BungieNetOrderDatum:
    """Represents a Bungie.net order (clan/team) data structure"""
    order_id: int = 0
    founding_date: datetime = field(default_factory=datetime.now)
    initial_date_below_three_members: datetime = field(default_factory=datetime.now)
    
    name: str = field(
        default="",
        metadata={"max_length": MAXIMUM_ORDER_NAME_LENGTH}
    )
    
    maintenance_password: str = field(
        default="",
        metadata={"max_length": MAXIMUM_PASSWORD_LENGTH}
    )
    
    member_password: str = field(
        default="",
        metadata={"max_length": MAXIMUM_PASSWORD_LENGTH}
    )
    
    url: str = field(
        default="",
        metadata={"max_length": MAXIMUM_ORDER_URL_LENGTH}
    )
    
    contact_email: str = field(
        default="",
        metadata={"max_length": MAXIMUM_ORDER_CONTACT_EMAIL_LENGTH}
    )
    
    motto: str = field(
        default="",
        metadata={"max_length": MAXIMUM_ORDER_MOTTO_LENGTH}
    )
    
    # Score tracking
    unranked_score: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_score: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_scores_by_game_type: List[BungieNetPlayerScoreDatum] = field(
        default_factory=lambda: [BungieNetPlayerScoreDatum() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )

    def __post_init__(self):
        """Validate and truncate fields that exceed maximum lengths"""
        if len(self.name) > MAXIMUM_ORDER_NAME_LENGTH:
            self.name = self.name[:MAXIMUM_ORDER_NAME_LENGTH]
            
        if len(self.maintenance_password) > MAXIMUM_PASSWORD_LENGTH:
            self.maintenance_password = self.maintenance_password[:MAXIMUM_PASSWORD_LENGTH]
            
        if len(self.member_password) > MAXIMUM_PASSWORD_LENGTH:
            self.member_password = self.member_password[:MAXIMUM_PASSWORD_LENGTH]
            
        if len(self.url) > MAXIMUM_ORDER_URL_LENGTH:
            self.url = self.url[:MAXIMUM_ORDER_URL_LENGTH]
            
        if len(self.contact_email) > MAXIMUM_ORDER_CONTACT_EMAIL_LENGTH:
            self.contact_email = self.contact_email[:MAXIMUM_ORDER_CONTACT_EMAIL_LENGTH]
            
        if len(self.motto) > MAXIMUM_ORDER_MOTTO_LENGTH:
            self.motto = self.motto[:MAXIMUM_ORDER_MOTTO_LENGTH]

    def to_dict(self) -> dict:
        """Convert the order data to a dictionary for serialization"""
        return {
            'order_id': self.order_id,
            'founding_date': self.founding_date.isoformat(),
            'initial_date_below_three_members': self.initial_date_below_three_members.isoformat(),
            'name': self.name,
            'url': self.url,
            'contact_email': self.contact_email,
            'motto': self.motto,
            'unranked_score': self.unranked_score.to_dict(),
            'ranked_score': self.ranked_score.to_dict(),
            'ranked_scores_by_game_type': [score.to_dict() for score in self.ranked_scores_by_game_type]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BungieNetOrderDatum':
        """Create an order from a dictionary"""
        order = cls(
            order_id=data.get('order_id', 0),
            name=data.get('name', ''),
            url=data.get('url', ''),
            contact_email=data.get('contact_email', ''),
            motto=data.get('motto', '')
        )
        
        # Convert ISO format strings to datetime objects
        if 'founding_date' in data:
            order.founding_date = datetime.fromisoformat(data['founding_date'])
        if 'initial_date_below_three_members' in data:
            order.initial_date_below_three_members = datetime.fromisoformat(
                data['initial_date_below_three_members']
            )
            
        # Convert score data
        if 'unranked_score' in data:
            order.unranked_score = BungieNetPlayerScoreDatum.from_dict(data['unranked_score'])
        if 'ranked_score' in data:
            order.ranked_score = BungieNetPlayerScoreDatum.from_dict(data['ranked_score'])
            
        if 'ranked_scores_by_game_type' in data:
            order.ranked_scores_by_game_type = [
                BungieNetPlayerScoreDatum.from_dict(score_data)
                for score_data in data['ranked_scores_by_game_type']
            ]
            
        return order
