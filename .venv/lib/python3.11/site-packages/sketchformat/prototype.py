from .common import Point
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class OverlayBackgroundInteraction(IntEnum):
    NONE = 0
    CLOSES_OVERLAY = 1


class PresentationStyle(IntEnum):
    SCREEN = 0
    OVERLAY = 1


class AnimationType(IntEnum):
    NONE = -1
    SLIDE_FROM_RIGHT = 0
    SLIDE_FROM_LEFT = 1
    SLIDE_FROM_BOTTOM = 2
    SLIDE_FROM_TOP = 3


@dataclass(kw_only=True)
class FlowOverlaySettings:
    _class: str = field(default="MSImmutableFlowOverlaySettings")
    overlayAnchor: Point
    sourceAnchor: Point
    offset: Point = field(default_factory=lambda: Point(0, 0))
    overlayType: int = 0

    @staticmethod
    def Positioned(position: str, offset: Point = Point(0, 0)) -> "FlowOverlaySettings":
        anchor = Point(0.5, 0.5)

        match position:
            case "TOP_LEFT":
                anchor = Point(0, 0)
            case "TOP_CENTER":
                anchor = Point(0.5, 0)
            case "TOP_RIGHT":
                anchor = Point(1, 0)
            case "BOTTOM_LEFT":
                anchor = Point(0, 1)
            case "BOTTOM_CENTER":
                anchor = Point(0.5, 1)
            case "BOTTOM_RIGHT":
                anchor = Point(1, 1)
            case "MANUAL":
                anchor = Point(0, 0)

        return FlowOverlaySettings(overlayAnchor=anchor, sourceAnchor=anchor, offset=offset)

    @staticmethod
    def RegularArtboard() -> "FlowOverlaySettings":
        anchor = Point(0.5, 0.5)

        return FlowOverlaySettings(overlayAnchor=anchor, sourceAnchor=anchor)


@dataclass(kw_only=True)
class FlowConnection:
    _class: str = field(default="MSImmutableFlowConnection")
    destinationArtboardID: str
    overlaySettings: Optional[FlowOverlaySettings]
    animationType: AnimationType = AnimationType.NONE
    maintainScrollPosition: bool = False
    shouldCloseExistingOverlays: bool = False


@dataclass(kw_only=True)
class PrototypeViewport:
    _class: str = field(default="MSImmutablePrototypeViewport")
    name: str
    size: Point
    # libraryID: str = 'EB972BCC-0467-4E50-998E-0AC5A39517F0'
    # templateID: str = '55992B99-92E5-4A93-AF90-B3A461675C05'
