import time
from typing import List

from velvet_dawn import errors
import velvet_dawn
from velvet_dawn.config import Config
from velvet_dawn.dao import db
from velvet_dawn.dao.models import Player, Team
from velvet_dawn.db.instances import WorldInstance
from velvet_dawn.db.models import Phase
from velvet_dawn.logger import logger
from velvet_dawn.models.game_state import TurnData


def get_active_turn():
    """ Get the current turn.

    If not in the game phase then no-one has the turn
    otherwise, try to load from the key or set to
    the first team.
    """
    phase = velvet_dawn.db.key_values.get_phase()
    if phase != Phase.GAME:
        return None

    active_turn = velvet_dawn.db.key_values.get_active_turn()
    if active_turn:
        return active_turn

    teams = velvet_dawn.teams.list(exclude_spectators=True)
    teams = sorted(teams, key=lambda team: team.team_id)
    return teams[0].team_id


def current_turn_data(config: Config, current_phase: Phase) -> TurnData:
    """ Get the current turn data returned to the user

    Args:
        config: To get the current turn time
        current_phase: The current phase of the game

    Returns:
        TurnData to include the current turn number, player's turn
          when the turn started and how long the turn is
    """
    turn = velvet_dawn.db.key_values.get_turn_number()


    turn_start = velvet_dawn.db.key_values.get_turn_start()
    turn_start = turn_start if turn_start else _update_turn_start_time()

    return TurnData(
        turn=turn,
        turn_seconds=_current_turn_time(config, current_phase),
        turn_start=turn_start,
        active_turn=get_active_turn()
    )


def ready(player: str):
    """ Ready a player, but if the phase is setup, then
    check they've placed a commander.
    """
    from velvet_dawn.game import setup

    if velvet_dawn.db.key_values.get_phase() == Phase.Setup:
        player_setup = setup.get_setup(player)
        if not player_setup.placed_commander:
            raise errors.ValidationError("You must place your commander.")

    logger.info(f"Player '{player}' ready.")
    db.session.query(Player).where(Player.name == player).update({Player.ready: True})
    db.session.commit()


def unready(player: str):
    """ Mark a player as not ready """
    logger.info(f"Player '{player}' unready.")
    db.session.query(Player).where(Player.name == player).update({Player.ready: False})
    db.session.commit()


def check_end_turn_case(config: Config):
    """ Check if the end-turn case has occured either by the turn
    time running or by players ready-ing

    This function should only be called when the host gets the
    game state.

    This will trigger the next turn to occur if true or the game
    to begin.
    """
    # This func should only be called by the host when loading the game state
    from velvet_dawn.game import phase

    current_phase = velvet_dawn.db.key_values.get_phase()
    if current_phase == Phase.Lobby or current_phase == Phase.GAME_OVER:
        return

    if _check_all_players_ready(current_phase):
        logger.info("All players ready!")
        if current_phase == Phase.Setup:
            phase.start_game_phase(config)
        elif current_phase == Phase.GAME:
            begin_next_turn(config)

    current_time = time.time()
    start_time = velvet_dawn.db.key_values.get_turn_start()
    start_time = start_time if start_time else _update_turn_start_time()
    allowed_turn_time = _current_turn_time(config, current_phase)

    if current_time > start_time + allowed_turn_time:
        logger.info(f"{allowed_turn_time} has elapsed in setup, moving to next turn")
        if current_phase == Phase.Setup:
            phase.start_game_phase(config)
        elif current_phase == Phase.GAME:
            begin_next_turn(config)


def begin_next_turn(config: Config):
    """ Start the next turn by:
         - Marking all players as not ready
         - Set the next team's turn
         - Update the turn timer
         - Updating the remaining movement of all entities to their range

    Args:
        config: Game config
    """
    teams: List[Team] = sorted(velvet_dawn.teams.list(exclude_spectators=True), key=lambda t: t.team_id)

    db.session.query(Player).update({Player.ready: False})
    db.session.commit()

    # Find the next team's turn
    # If current none, default to the last team for when looped through, else loop through and find the next iteration
    current_turn = velvet_dawn.db.key_values.get_active_turn()

    # If there is a turn, then trigger the end turn actions, otherwise it means there
    # is no turn as the game has only just begin
    if current_turn: _trigger_on_turn_end_actions(current_turn)
    else: current_turn = teams[-1].team_id

    velvet_dawn.db.gateway.save()

    new_team_turn = None
    for i, team in enumerate(teams):
        if team.team_id == current_turn:
            new_team_turn = teams[i + 1 - len(teams)].team_id

    velvet_dawn.db.key_values.set_active_turn(new_team_turn)

    # Update turn's player's entities to reset there remaining moves
    players = velvet_dawn.players.list(team=new_team_turn)
    for player in players:
        for unit in velvet_dawn.units.list(player=player.name):
            unit.set_attribute("movement.remaining", unit.get_attribute("movement.range", default=1))

    # Fire triggers on turn begins
    if new_team_turn == teams[0].team_id:
        _trigger_on_round_begin_actions()
    _trigger_on_turn_begin_actions(new_team_turn)

    _update_turn_start_time()


def _trigger_on_round_begin_actions():
    """ Trigger all entity/tile round being actions """
    for unit in velvet_dawn.units.list():
        velvet_dawn.datapacks.entities[unit.entity_id].triggers.on_round(unit)
    for tile in velvet_dawn.db.tiles.all():
        velvet_dawn.datapacks.tiles[tile.tile_id].triggers.on_round(tile)
    velvet_dawn.datapacks.world.triggers.on_round(WorldInstance())


def _trigger_on_turn_begin_actions(new_team_turn: str):
    """ Trigger all entity/tile turn begin actions

    Testing for this exists in the triggers test suite

    Args:
        new_team_turn: The team who's turn is starting
    """
    friendly_players, enemy_players = velvet_dawn.players.get_friendly_enemy_players_breakdown(for_team=new_team_turn)

    for unit in velvet_dawn.units.list():
        entity_definition = velvet_dawn.datapacks.entities[unit.entity_id]

        entity_definition.triggers.on_turn(unit)
        if unit.player in friendly_players: entity_definition.triggers.on_friendly_turn(unit)
        if unit.player in enemy_players: entity_definition.triggers.on_enemy_turn(unit)

    for tile in velvet_dawn.db.tiles.all():
        velvet_dawn.datapacks.tiles[tile.tile_id].triggers.on_turn(tile)
    velvet_dawn.datapacks.world.triggers.on_turn(WorldInstance())


def _trigger_on_turn_end_actions(old_team_turn):
    """ Trigger all entity/tile turn end actions

    Testing for this exists in the triggers test suite

    Args:
        old_team_turn: The team who's turn is ending
    """
    friendly_players, enemy_players = velvet_dawn.players.get_friendly_enemy_players_breakdown(for_team=old_team_turn)

    for unit in velvet_dawn.units.list():
        entity_definition = velvet_dawn.datapacks.entities[unit.entity_id]

        entity_definition.triggers.on_turn_end(unit)
        if unit.player in friendly_players: entity_definition.triggers.on_friendly_turn_end(unit)
        if unit.player in enemy_players: entity_definition.triggers.on_enemy_turn_end(unit)

    for tile in velvet_dawn.db.tiles.all():
        velvet_dawn.datapacks.tiles[tile.tile_id].triggers.on_turn_end(tile)
    velvet_dawn.datapacks.world.triggers.on_turn_end(WorldInstance())


def _check_all_players_ready(current_phase: Phase) -> bool:
    """ Check all players are ready for the current team

    Args:
        current_phase: Current phase of the game

    Returns:
        If all players are ready
    """
    all_ready = True
    players = []

    if current_phase == Phase.Setup:
        players = velvet_dawn.players.list(exclude_spectators=True)

    elif current_phase == Phase.GAME:
        current_turn = get_active_turn()
        players = velvet_dawn.players.list(team=current_turn)

    for player in players:
        all_ready = all_ready and player.ready

    return all_ready


def _update_turn_start_time() -> float:
    """ Update the time the current turn started to the current time

    Returns:
        Current time.
    """
    return velvet_dawn.db.key_values.set_turn_start(time.time())


def _current_turn_time(config: Config, current_phase: Phase) -> int:
    """ Return config turn time unless in setup phase """
    return int(config.setup_time) if current_phase == Phase.Setup else int(config.turn_time)
