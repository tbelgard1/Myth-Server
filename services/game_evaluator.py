"""
Game evaluation service for Myth metaserver.

This module handles evaluating game results and updating player statistics.
It provides functions for finding reliable game standings and adjusting
player scores based on game outcomes.

Copyright (c) 1997-2002 Bungie Studios
Copyright (c) 2002, 2003 Alan Wagner
Copyright (c) 2002 Vishvananda Ishaya
Copyright (c) 2003 Bill Keirstead
"""

from typing import List, Optional
from dataclasses import dataclass
import logging

from ..models.player import BungieNetPlayerDatum
from ..models.order import BungieNetOrderDatum
from ..models.game import BungieNetGameStandings, GameType
from .game_service import game_service

# Game classification constants
RANKED_NORMAL = 1
UNRANKED_NORMAL = 2

logger = logging.getLogger(__name__)

def find_player_struct_by_pid(
    player_id: int,
    player_count: int,
    players: List[BungieNetPlayerDatum]
) -> Optional[BungieNetPlayerDatum]:
    """Find a player structure by player ID.
    
    Args:
        player_id: ID of player to find
        player_count: Number of players to search through
        players: List of player structures
        
    Returns:
        Matching player structure or None if not found
    """
    if not players:
        return None
    
    for i in range(player_count):
        current_player = players[i]
        if current_player.player_id == player_id:
            return current_player
    return None

def find_same_standings(
    st1: Optional[BungieNetGameStandings],
    st2: Optional[BungieNetGameStandings]
) -> bool:
    """Compare two game standings to check if they are the same.
    
    This is used to validate game results by comparing standings
    reported by different players.
    
    Args:
        st1: First standings to compare
        st2: Second standings to compare
        
    Returns:
        True if standings match, False otherwise
    """
    if st1 is not None and st2 is not None:
        # Basic checks for equality
        if st1.game_ended_code != st2.game_ended_code:
            return False
        if st1.version_number != st2.version_number:
            return False
        if st1.number_of_players != st2.number_of_players:
            return False
        return True
    return False

def find_good_standings_for_game(
    player_count: int,
    all_standings: List[Optional[BungieNetGameStandings]]
) -> Optional[BungieNetGameStandings]:
    """Find a reliable set of standings for scoring a game.
    
    This looks for two matching sets of standings among those reported
    by different players to ensure accuracy.
    
    Args:
        player_count: Number of players in the game
        all_standings: List of standings reported by each player
        
    Returns:
        A reliable set of standings, or None if none found
    """
    if not all_standings:
        return None
    if player_count == 1:
        return all_standings[0]

    good_standings = None
    for i in range(player_count):
        temp_standings = all_standings[i]
        if temp_standings is None:
            continue
        if good_standings is not None:
            if find_same_standings(temp_standings, good_standings):
                return good_standings
        else:
            good_standings = temp_standings

    # If this is reached then there were no two standings the same
    return None

async def bungie_net_game_evaluate(
    game_id: int,
    host_player_id: int,
    game_classification: int,
    player_count: int,
    bungie_net_players: List[BungieNetPlayerDatum],
    bungie_net_orders: List[BungieNetOrderDatum],
    reported_standings: List[Optional[BungieNetGameStandings]]
) -> None:
    """Evaluate game results and update player statistics.
    
    This is the main function for processing game results. It:
    1. Validates the reported standings
    2. Updates player statistics including:
       - Games played
       - Wins/losses/ties
       - Points scored/lost
       - Rankings
    3. Updates both overall stats and game-type specific stats
    
    Args:
        host_player_id: ID of the game host
        game_classification: Type of game (ranked/unranked)
        player_count: Number of players in the game
        bungie_net_players: List of player data structures
        bungie_net_orders: List of order (clan) data structures
        reported_standings: Game results reported by each player
    """
    # Get useable standings for game
    current_standings = find_good_standings_for_game(player_count, reported_standings)
    if current_standings is None:
        logger.error(f"No reliable standings found for game {game_id}")
        return
    if current_standings.players is None or current_standings.teams is None:
        logger.error(f"Invalid standings for game {game_id} - missing players or teams")
        return
        
    # Get game data
    game = await game_service.get_game_data(game_id)
    if game is None:
        logger.error(f"Game {game_id} not found")
        return
        
    # Update player scores
    player_scores = {}
    for i in range(player_count):
        player_id = current_standings.players[i].bungie_net_player_id
        score = current_standings.players[i].points_killed - current_standings.players[i].points_lost
        player_scores[player_id] = score
        
    # End game and record results
    await game_service.end_game(game_id, player_scores)

    # Treat unranked games as if they were ranked
    if game_classification in (RANKED_NORMAL, UNRANKED_NORMAL):
        # Go through reported_standings - only adjust winner and loser points
        for i in range(player_count):
            current_player_id = current_standings.players[i].bungie_net_player_id
            current_team = current_standings.players[i].team_index
            current_player = find_player_struct_by_pid(current_player_id, player_count, bungie_net_players)
            place = current_standings.teams[current_team].place

            # Adjust games played, damage, and wins/losses/ties as appropriate
            if current_player is not None:
                # Adjust ranked score (for all game types)
                current_player.ranked_score.damage_inflicted += current_standings.players[i].points_killed
                current_player.ranked_score.damage_received += current_standings.players[i].points_lost
                current_player.ranked_score.games_played += 1

                # Adjust scores for specific game type
                game_type = current_standings.game_scoring
                current_player.ranked_scores_by_game_type[game_type].damage_inflicted += current_standings.players[i].points_killed
                current_player.ranked_scores_by_game_type[game_type].damage_received += current_standings.players[i].points_lost
                current_player.ranked_scores_by_game_type[game_type].games_played += 1

                if place == 0:  # Winner
                    # Adjust wins & points for all game types
                    current_player.ranked_score.wins += 1
                    current_player.ranked_score.points += 3
                    if current_player.ranked_score.points > current_player.ranked_score.highest_points:
                        current_player.ranked_score.highest_points = current_player.ranked_score.points

                    # Adjust wins & points for specific game type
                    current_player.ranked_scores_by_game_type[game_type].wins += 1
                    current_player.ranked_scores_by_game_type[game_type].points += 3
                    if (current_player.ranked_scores_by_game_type[game_type].points >
                        current_player.ranked_scores_by_game_type[game_type].highest_points):
                        current_player.ranked_scores_by_game_type[game_type].highest_points = \
                            current_player.ranked_scores_by_game_type[game_type].points

                elif place == (current_standings.number_of_teams - 1):  # Loser
                    # Adjust losses and points for all game types
                    current_player.ranked_score.losses += 1
                    current_player.ranked_score.points -= 1

                    # Adjust losses for specific game type
                    current_player.ranked_scores_by_game_type[game_type].losses += 1
                    current_player.ranked_scores_by_game_type[game_type].points -= 1

def scoring_datum_adjust_total(
    score_by_game_types: List[BungieNetPlayerDatum],
    total_score: BungieNetPlayerDatum
) -> None:
    """Adjust total scores based on game type scores.
    
    This is a placeholder function for future implementation of
    total score adjustments based on individual game type scores.
    
    Args:
        score_by_game_types: List of scores by game type
        total_score: Total score to adjust
    """
    # This function is empty in the original code
    pass
