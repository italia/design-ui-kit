import math
from .errors import Fig2SketchWarning
from sketchformat.layer_common import Rect, AbstractLayer
from typing import TypedDict, Tuple, List, Sequence


class Vector(list):
    def __init__(self, x: float, y: float):
        super().__init__([x, y])

    def __add__(self, other):
        return Vector(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return Vector(self[0] - other[0], self[1] - other[1])


class Matrix(list):
    def __init__(self, m: Sequence[Sequence[float]]):
        super().__init__(m)

    def dot(self, v: Vector) -> Vector:
        return Vector(
            self[0][2] + self[0][0] * v[0] + self[0][1] * v[1],
            self[1][2] + self[1][0] * v[0] + self[1][1] * v[1],
        )

    def dot2(self, v: Vector) -> Vector:
        return Vector(
            self[0][0] * v[0] + self[0][1] * v[1],
            self[1][0] * v[0] + self[1][1] * v[1],
        )

    def inv(self):
        return Matrix(
            [
                [
                    self[1][1] / (self[0][0] * self[1][1] - self[0][1] * self[1][0]),
                    self[0][1] / (self[0][1] * self[1][0] - self[0][0] * self[1][1]),
                    (self[0][2] * self[1][1] - self[0][1] * self[1][2])
                    / (self[0][1] * self[1][0] - self[0][0] * self[1][1]),
                ],
                [
                    self[1][0] / (self[0][1] * self[1][0] - self[0][0] * self[1][1]),
                    self[0][0] / (self[0][0] * self[1][1] - self[0][1] * self[1][0]),
                    (self[0][2] * self[1][0] - self[0][0] * self[1][2])
                    / (self[0][0] * self[1][1] - self[0][1] * self[1][0]),
                ],
                [0, 0, 1],
            ]
        )


class _Positioning(TypedDict):
    frame: Rect
    rotation: float
    isFlippedHorizontal: bool
    isFlippedVertical: bool


def convert(fig_item: dict) -> _Positioning:
    flip, rotation = guess_flip(fig_item)
    coordinates = transform_frame(fig_item)

    if any([math.isnan(x) for x in [*coordinates, rotation]]):
        raise Fig2SketchWarning("POS001")

    return {
        "frame": Rect(
            constrainProportions=fig_item.get("proportionsConstrained", False),
            height=fig_item["size"]["y"] or 0.1,
            width=fig_item["size"]["x"] or 0.1,
            x=coordinates[0],
            y=coordinates[1],
        ),
        "rotation": rotation or 0,
        "isFlippedHorizontal": flip[0],
        "isFlippedVertical": flip[1],
    }


def transform_frame(item: dict, size: dict = {}) -> Vector:
    if not size:
        size = item["size"]
    # Calculate relative position
    relative_position = Vector(item["transform"][0][2], item["transform"][1][2])

    # Vector from rotation center to origin (0,0)
    vco = Vector(size["x"] / 2, size["y"] / 2)

    # Apply rotation to vector
    vco_rotated = apply_transform(item, vco)

    # Calculate translation of origin
    origin_translation = vco_rotated - vco

    # Return origin coordinates after translation and relative to parent
    return relative_position + origin_translation


def apply_transform(item: dict, vector: Vector) -> Vector:
    # Rotation/flip matrix
    matrix = item["transform"]

    return matrix.dot2(vector)


def guess_flip(fig_item: dict) -> Tuple[List[bool], float]:
    tr = fig_item["transform"]

    # Use a diagonal with big numbers to check for sign flips, to avoid floating point weirdness
    flip = [False, False]
    if abs(tr[1][1]) > 0.1:
        flip[1] = bool(math.copysign(1, tr[1][1]) != math.copysign(1, tr[0][0]))
    else:
        flip[1] = bool(math.copysign(1, tr[0][1]) == math.copysign(1, tr[1][0]))

    angle = math.degrees(math.atan2(-fig_item["transform"][1][0], fig_item["transform"][0][0]))
    if flip[1]:
        angle *= -1

    # It's impossible to know if the user intended a 180º rotation or two flips (H and V).
    # We've got a chance to invert both flips and add 180 to the angle, but we've got to guess
    # We guess that angles between -90 to 90 are OK. Angles of 180 are also OK if there is no flip
    # already applied. This makes sure our output angle is < 90 or that it's 180 with no flips.
    # Note: this heuristic is bound to be wrong lots of times, so maybe we can skip it completely
    if 90 < abs(angle) < 179 or (abs(angle) > 179 and flip[1]):
        flip[0] = not flip[0]
        flip[1] = not flip[1]
        angle = (angle + 180) % 360

    return flip, angle


def group_bbox(children: Sequence[AbstractLayer]) -> Tuple[float, float, float, float]:
    if not children:
        return (0, 0, 0, 0)

    child_bboxes = [bbox_from_frame(child) for child in children]

    return (
        min([b[0] for b in child_bboxes]),
        max([b[1] for b in child_bboxes]),
        min([b[2] for b in child_bboxes]),
        max([b[3] for b in child_bboxes]),
    )


# TODO: Extract this and share code with positioning (after tests are created)
def bbox_from_frame(child: AbstractLayer) -> Tuple[float, float, float, float]:
    frame = child.frame
    theta = math.radians(child.rotation)
    c, s = math.cos(theta), math.sin(theta)
    matrix = Matrix([[c, -s], [s, c]])
    # Rotate the frame to the original position and calculate corners
    x1 = frame.x
    x2 = x1 + frame.width
    y1 = frame.y
    y2 = y1 + frame.height

    w2 = frame.width / 2
    h2 = frame.height / 2
    points = [
        matrix.dot2(Vector(-w2, -h2)) - Vector(-w2, -h2) + Vector(x1, y1),
        matrix.dot2(Vector(w2, -h2)) - Vector(w2, -h2) + Vector(x2, y1),
        matrix.dot2(Vector(w2, h2)) - Vector(w2, h2) + Vector(x2, y2),
        matrix.dot2(Vector(-w2, h2)) - Vector(-w2, h2) + Vector(x1, y2),
    ]

    return (
        min(p[0] for p in points),
        max(p[0] for p in points),
        min(p[1] for p in points),
        max(p[1] for p in points),
    )
