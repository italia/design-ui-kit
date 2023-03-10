from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Union

from .prototype import FlowConnection
from .style import Style, Color


class ExportLayerOptions(IntEnum):
    ALL = 0
    SELECTED = 1
    IN_GROUP = 2


class ExportNamingScheme(IntEnum):
    SUFFIX = 0
    SECONDARY_PREFIX = 1
    PRIMARY_PREFIX = 2


class VisibleScaleType(IntEnum):
    SCALE = 0
    WIDTH = 1
    HEIGHT = 2


class BooleanOperation(IntEnum):
    NONE = -1
    UNION = 0
    SUBTRACT = 1
    INTERSECT = 2
    DIFFERENCE = 3


class LayerListStatus(IntEnum):
    UNDECIDED = 0
    COLLAPSED = 1
    EXPANDED = 2


class ClippingMaskMode(IntEnum):
    OUTLINE = 0
    ALPHA = 1


class ResizeType(IntEnum):
    STRETCH = 0
    PIN_TO_EDGE = 1
    RESIZE = 2
    FLOAT = 2


@dataclass(kw_only=True)
class ExportFormat:
    _class: str = field(default="exportFormat")
    fileFormat: str
    name: str
    visibleScaleType: VisibleScaleType
    absoluteSize: int = 0
    namingScheme: ExportNamingScheme = ExportNamingScheme.PRIMARY_PREFIX
    scale: float = 1


@dataclass(kw_only=True)
class ExportOptions:
    _class: str = field(default="exportOptions")
    exportFormats: List[ExportFormat] = field(default_factory=list)
    includedLayerIds: List[str] = field(default_factory=list)
    layerOptions: ExportLayerOptions = ExportLayerOptions.ALL
    shouldTrim: bool = False


@dataclass(kw_only=True)
class Rect:
    _class: str = field(default="rect")
    height: float
    width: float
    x: float
    y: float
    constrainProportions: bool = False


@dataclass(kw_only=True)
class AbstractLayer:
    do_objectID: str
    frame: Rect
    name: str
    resizingConstraint: int
    rotation: float
    booleanOperation: BooleanOperation = BooleanOperation.NONE
    exportOptions: ExportOptions = field(default_factory=ExportOptions)
    flow: Optional[FlowConnection] = None
    isFixedToViewport: bool = False
    isFlippedHorizontal: bool = False
    isFlippedVertical: bool = False
    isLocked: bool = False
    isTemplate: bool = False
    isVisible: bool = True
    layerListExpandedType: LayerListStatus = LayerListStatus.UNDECIDED
    nameIsFixed: bool = False
    resizingType: ResizeType = ResizeType.STRETCH
    shouldBreakMaskChain: bool = False


@dataclass(kw_only=True)
class AbstractStyledLayer(AbstractLayer):
    style: Style
    hasClippingMask: bool = False
    clippingMaskMode: ClippingMaskMode = ClippingMaskMode.OUTLINE
    sharedStyleID: Optional[str] = None


@dataclass(kw_only=True)
class Slice(AbstractLayer):
    _class: str = field(default="slice")
    hasBackgroundColor: bool = False
    backgroundColor: Color = field(default_factory=Color.White)
