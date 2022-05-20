from app.state import state
from app.utils.maths import closest


def get_rotation(db: int) -> int:
    """Get a servo rotation for a chunk of audio."""
    # Calculate rotation based on the dB of the chunk.
    rotation_step = (state.rotations_range[1] - state.rotations_range[0]) / (state.min_dbfs - state.max_dbfs)
    rotation = state.rotations_range[1] + (state.max_dbfs - db) * rotation_step

    closest_rotation = closest(state.allowed_rotations, rotation)
    if state.rotations_range[0] <= closest_rotation <= state.rotations_range[1]:
        return closest_rotation

    # Make sure the rotation is within the allowed range.
    if rotation < state.rotations_range[0]:
        return state.rotations_range[0]

    if rotation > state.rotations_range[1]:
        return state.rotations_range[1]

    # Make rotation a multiple of 5.
    return rotation - (rotation % 5)
