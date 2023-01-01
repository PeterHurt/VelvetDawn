import velvet_dawn
from .attributes import Attributes
from velvet_dawn.models.datapacks.taggable import Taggable
from ... import errors, constants


# List of all available keys allowed on an entity
VALID_ENTITY_KEYS = [
    "id", "name", "abstract", "extends", "upgrades", "health",
    "movement", "combat", "tags", "notes", "textures", "triggers",
    "commander", "influence", "attributes", "actions"
]

VALID_HEALTH_KEYS = ["regen", "max", "notes"]
VALID_COMBAT_KEYS = ["range", "attack", "defense", "reload", "notes"]
VALID_MOVEMENT_KEYS = ["range", "notes"]


def _parse_health(unit_id: str, attributes: Attributes, data: dict):
    """ Parse the entity health data, see wiki for more information. """
    for key in data:
        if key not in VALID_HEALTH_KEYS:
            raise errors.ValidationError(f"Invalid health key '{key}' on '{unit_id}'")

    # Extract
    regen = data.get("regen", constants.UNIT_DEFAULT_HEALTH_REGEN)
    max_health = data.get("max", constants.UNIT_DEFAULT_HEALTH_MAX)

    # Validate
    velvet_dawn.validations.is_number(regen, min=0, error_prefix=f"{unit_id} health regen")
    velvet_dawn.validations.is_number(max_health, min=0, error_prefix=f"{unit_id} max health")

    # Validate
    if not isinstance(regen, int) and not isinstance(regen, float):
        raise errors.ValidationError(f"{unit_id} health regen must be a number.")

    if not isinstance(max_health, int) and not isinstance(max_health, float):
        raise errors.ValidationError(f"{unit_id} max health must be a number.")
    if max_health <= 0:
        raise errors.ValidationError(f"{unit_id} max health must be greater than 0.")

    # Set values
    attributes.set("health", "Health", value=0, icon="base:textures.ui.icons.health")
    attributes.set("health.regen", value=regen)
    attributes.set("health.max", value=max_health)


def _parse_combat(unit_id: str, attributes: Attributes, data: dict):
    """ Parse the entity combat data, see wiki for more information. """
    for key in data:
        if key not in VALID_COMBAT_KEYS:
            raise errors.ValidationError(f"Invalid combat key '{key}' on '{unit_id}'")

    # Extract
    combat_range = data.get("range", constants.UNIT_DEFAULT_COMBAT_RANGE)
    combat_attack = data.get("attack", constants.UNIT_DEFAULT_COMBAT_ATTACK)
    combat_defense = data.get("defense", constants.UNIT_DEFAULT_COMBAT_DEFENSE)
    combat_reload = data.get("reload", constants.UNIT_DEFAULT_COMBAT_RELOAD)

    # Validate
    velvet_dawn.validations.is_int(combat_range, min=1, error_prefix=f"{unit_id} combat range")
    velvet_dawn.validations.is_number(combat_attack, min=0, error_prefix=f"{unit_id} combat attack")
    velvet_dawn.validations.is_number(combat_defense, min=0, error_prefix=f"{unit_id} combat defense")
    velvet_dawn.validations.is_int(combat_reload, min=0, error_prefix=f"{unit_id} combat reload")

    # Set
    attributes.set("combat.attack", "Attack", value=combat_attack, icon="base:textures.ui.icons.attack")
    attributes.set("combat.defense", "Defense", value=combat_defense, icon="base:textures.ui.icons.defense")
    attributes.set("combat.range", value=combat_range)
    attributes.set("combat.reload", value=combat_reload)


def _parse_movement(unit_id: str, attributes: Attributes, data: dict):
    """ Parse the entity movement data, see wiki for more information. """
    for key in data:
        if key not in VALID_COMBAT_KEYS:
            raise errors.ValidationError(f"Invalid movement key '{key}' on '{unit_id}'")

    # Extract
    movement_range = data.get("range", constants.UNIT_DEFAULT_MOVEMENT_RANGE)

    # Validate
    velvet_dawn.validations.is_int(movement_range, min=1, error_prefix=f"{unit_id} movement range")

    # Set
    attributes.set("movement.remaining", value=0)
    attributes.set("movement.range", value=movement_range)


# TODO Standard
# TODO Moving
# TODO Fighting
# TODO Movement particles
# TODO Add proper validation
class EntityTextures:
    def __init__(self):
        self.background = None

    def update(self, data: dict):
        self.background = data.get("background")

    def json(self):
        return {
            "background": self.background
        }


class Unit(Taggable):
    def __init__(self, id: str, name: str):
        super().__init__()

        self.id = id
        self.name = name
        self.max_health = 100
        self.commander = False

        self.attributes = Attributes()
        self.textures = EntityTextures()

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "commander": self.commander,
            "attributes": self.attributes.json(),
            "textures": self.textures.json()
        }

    @staticmethod
    def load(id: str, data: dict):
        for key in data:
            if key not in VALID_ENTITY_KEYS:
                raise errors.ValidationError(f"Invalid key '{key}' on entity '{id}'")

        unit = Unit(id=id, name=data['name'])

        unit.commander = data.get("commander", False)

        unit.textures.update(data.get('textures', {}))
        _parse_health(id, unit.attributes, data.get("health", {}))
        _parse_movement(id, unit.attributes, data.get("movement", {}))
        _parse_combat(id, unit.attributes, data.get("combat", {}))

        unit.attributes.load(id, data.get('attributes', []))

        unit._load_tags(data)

        return unit


Entity = Unit
