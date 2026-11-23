DRY_FRICTION = {
    "asphalt": (0.85, 0.70),
    "concrete": (0.90, 0.75),
    "sett": (0.65, 0.55),
    "paving_stones": (0.70, 0.60),
    "concrete:plates": (0.75, 0.60),
    "concrete:lanes": (0.75, 0.60),
    "sett;concrete": (0.70, 0.58),
    "paved": (0.80, 0.65),
    "compacted": (0.60, 0.45),
    "fine_gravel": (0.55, 0.40),
    "gravel": (0.50, 0.35),
    "unpaved": (0.55, 0.40),
    "ground": (0.50, 0.35),
    "dirt": (0.50, 0.35),
    "gruntowa_(ogólnie)a": (0.50, 0.35),
    "wood": (0.60, 0.45),
    "rock": (0.65, 0.50),
}

# Submerged / wet friction (noticeable drop on smooth stone blocks and dirt/mud)
WET_FRICTION = {
    "asphalt": (0.60, 0.45),
    "concrete": (0.65, 0.50),
    "sett": (0.35, 0.25),
    "paving_stones": (0.45, 0.35),
    "concrete:plates": (0.50, 0.40),
    "concrete:lanes": (0.50, 0.40),
    "sett;concrete": (0.40, 0.30),
    "paved": (0.55, 0.40),
    "compacted": (0.35, 0.25),
    "fine_gravel": (0.35, 0.25),
    "gravel": (0.35, 0.25),
    "unpaved": (0.25, 0.15),  # Mud conditions
    "ground": (0.20, 0.10),
    "dirt": (0.20, 0.10),
    "gruntowa_(ogólnie)a": (0.20, 0.10),
    "wood": (0.30, 0.20),
    "rock": (0.35, 0.25),
}

DEFAULT_DRY = (0.70, 0.55)
DEFAULT_WET = (0.40, 0.25)


def get_friction(surface_tag: str, is_wet: bool = False) -> tuple[float, float]:
    """
    Returns (mu_static, mu_kinetic) for a given OSM surface tag.
    Falls back to a safe default if the tag is unmapped or None.
    """
    table = WET_FRICTION if is_wet else DRY_FRICTION
    fallback = DEFAULT_WET if is_wet else DEFAULT_DRY

    if not isinstance(surface_tag, str):
        return fallback

    # Handle semicolon-separated values (e.g. 'sett;concrete') or basic match
    tag = surface_tag.strip().lower()
    return table.get(tag, fallback)
