from typing import List, Optional

import velvet_dawn
from velvet_dawn.constants import SPECTATORS_TEAM_ID
from velvet_dawn.dao import db
from velvet_dawn.dao.models import Player, Team
from .. import game, constants
from ..db.models import Phase
from ..logger import logger
from ..models.mode import Mode


def list(exclude_spectators: bool = False) -> List[Team]:
    if exclude_spectators:
        return db.session.query(Team).where(Team.team_id != constants.SPECTATORS_TEAM_ID).all()

    return db.session.query(Team).all()


def add_player_to_spectators(player_name: str):
    logger.info(f"Adding '{player_name}' to spectators team.")
    team = db.session.query(Team).where(Team.team_id == SPECTATORS_TEAM_ID).one_or_none()
    if not team:
        new_team(SPECTATORS_TEAM_ID, "Spectators")

    db.session.query(Player).where(Player.name == player_name).update({Player.team: SPECTATORS_TEAM_ID})
    db.session.commit()


def get_players_not_in_teams() -> List[Player]:
    return db.session.query(Player).where(Player.team == None).all()


def new_team(team_id: str, name: str):
    team = Team(
        team_id=team_id,
        name=name,
        color="white"
    )
    db.session.add(team)
    db.session.commit()


# TODO Test this in different game modes and scenes
def auto_update_teams():
    logger.info("Updating teams")
    players = get_players_not_in_teams()

    # If in game, add player to the spectators team
    if velvet_dawn.db.key_values.get_phase() != Phase.Lobby:
        for player in players:
            add_player_to_spectators(player.name)
        return

    if game.mode() == Mode.ALL_V_ALL:
        for player in players:
            logger.info(f"Adding {player.name} to their own team")
            new_team(f"team:{player.name}", f"{str(player.name).title()}")
            db.session.query(Player)\
                .where(Player.name == player.name)\
                .update({
                    Player.team: f"team:{player.name}"
                })
            db.session.commit()

    else:
        raise Exception("Unknown Game mode for auto balancing teams")

    # Remove empty teams
    for team in db.session.query(Team).all():
        players = db.session.query(Player).where(Player.team == team.team_id).all()
        if not players:
            db.session.delete(team)
            db.session.commit()


# TODO Test
def get_team_for_player(player_name: str) -> Optional[Team]:
    player = db.session.query(Player).where(Player.name == player_name).one_or_none()
    if not player:
        return None

    return db.session.query(Team).where(Team.team_id == player.team).one_or_none()
