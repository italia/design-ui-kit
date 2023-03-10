from .layer_common import AbstractStyledLayer
from .common import Point
from enum import IntEnum
from dataclasses import dataclass, field, InitVar
from typing import List, NamedTuple
import math


class PointRadiusBehaviour(IntEnum):
    V0 = 0
    V1 = 1
    V1_SMOOTH = 2


class CornerStyle(IntEnum):
    ROUNDED = 0
    ROUNDED_INVERTED = 1
    ANGLED = 2
    SQUARED = 3


class CurveMode(IntEnum):
    UNDEFINED = 0
    STRAIGHT = 1
    MIRRORED = 2
    ASYMMETRIC = 3
    DISCONNECTED = 4


@dataclass(kw_only=True)
class CurvePoint:
    _class: str = field(default="curvePoint")
    curveFrom: Point
    curveTo: Point
    point: Point
    cornerRadius: float = 0.0
    cornerStyle: CornerStyle = CornerStyle.ROUNDED
    hasCurveFrom: bool = False
    hasCurveTo: bool = False
    curveMode: CurveMode = CurveMode.UNDEFINED

    @staticmethod
    def Straight(point: Point, radius: float = 0.0) -> "CurvePoint":
        return CurvePoint(
            curveFrom=point,
            curveTo=point,
            point=point,
            cornerRadius=radius,
            curveMode=CurveMode.STRAIGHT,
        )

    @staticmethod
    def Curved(point: Point, curveFrom: Point, curveTo: Point) -> "CurvePoint":
        return CurvePoint(
            curveFrom=curveFrom,
            curveTo=curveTo,
            point=point,
            hasCurveFrom=True,
            hasCurveTo=True,
            curveMode=CurveMode.MIRRORED,
        )


@dataclass(kw_only=True)
class AbstractShapeLayer(AbstractStyledLayer):
    isClosed: bool
    points: List[CurvePoint]
    edited: bool = False
    pointRadiusBehaviour: PointRadiusBehaviour = PointRadiusBehaviour.V1


@dataclass(kw_only=True)
class ShapePath(AbstractShapeLayer):
    _class: str = field(default="shapePath")
    edited: bool = True


@dataclass(kw_only=True)
class Rectangle(AbstractShapeLayer):
    class Corners(NamedTuple):
        topLeft: float
        topRight: float
        bottomRight: float
        bottomLeft: float

    corners: InitVar[Corners] = Corners(0, 0, 0, 0)
    _class: str = field(default="rectangle")
    fixedRadius: float = 0.0
    hasConvertedToNewRoundCorners: bool = True
    needsConvertionToNewRoundCorners: bool = False
    isClosed: bool = True
    points: List[CurvePoint] = field(default_factory=list)

    def __post_init__(self, corners):
        self.points = [
            CurvePoint.Straight(Point(0, 0), corners.topLeft),
            CurvePoint.Straight(Point(0, 1), corners.bottomLeft),
            CurvePoint.Straight(Point(1, 1), corners.bottomRight),
            CurvePoint.Straight(Point(1, 0), corners.topRight),
        ]


def oval_make_points() -> List[CurvePoint]:
    P1 = 0.22385762510000001
    P2 = 0.77614237490000004
    return [
        CurvePoint.Curved(
            point=Point(0.5, 1),
            curveFrom=Point(P2, 1),
            curveTo=Point(P1, 1),
        ),
        CurvePoint.Curved(
            point=Point(1, 0.5),
            curveFrom=Point(1, P1),
            curveTo=Point(1, P2),
        ),
        CurvePoint.Curved(
            point=Point(0.5, 0),
            curveFrom=Point(P1, 0),
            curveTo=Point(P2, 0),
        ),
        CurvePoint.Curved(
            point=Point(0, 0.5),
            curveFrom=Point(0, P2),
            curveTo=Point(0, P1),
        ),
    ]


@dataclass(kw_only=True)
class Oval(AbstractShapeLayer):
    _class: str = field(default="oval")
    points: List[CurvePoint] = field(default_factory=oval_make_points)
    isClosed: bool = True


@dataclass(kw_only=True)
class Star(AbstractShapeLayer):
    _class: str = field(default="star")
    radius: float
    numberOfPoints: float
    isClosed: bool = True
    points: List[CurvePoint] = field(default_factory=list)

    def __post_init__(self):
        for i in range(self.numberOfPoints):
            angle = -math.pi / 2 + 2 * i * math.pi / self.numberOfPoints
            angle2 = angle + math.pi / self.numberOfPoints

            # Outer point
            x1 = 0.5 + (math.cos(angle) * 0.5)
            y1 = 0.5 + (math.sin(angle) * 0.5)
            self.points.append(CurvePoint.Straight(Point(x1, y1)))

            # Inner point shifted by half the angle
            x2 = 0.5 + (math.cos(angle2) * 0.5 * self.radius)
            y2 = 0.5 + (math.sin(angle2) * 0.5 * self.radius)
            self.points.append(CurvePoint.Straight(Point(x2, y2)))


@dataclass(kw_only=True)
class Polygon(AbstractShapeLayer):
    _class: str = field(default="polygon")
    numberOfPoints: float
    points: List[CurvePoint] = field(default_factory=list)
    isClosed: bool = True

    def __post_init__(self):
        for i in range(self.numberOfPoints):
            angle = -math.pi / 2 + 2 * i * math.pi / self.numberOfPoints
            x1 = 0.5 + (math.cos(angle) * 0.5)
            y1 = 0.5 + (math.sin(angle) * 0.5)
            self.points.append(CurvePoint.Straight(Point(x1, y1)))
