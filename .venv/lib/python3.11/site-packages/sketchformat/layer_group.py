from .layer_common import *
from .common import WindingRule
from .prototype import *
from enum import IntEnum
from typing import Any, Optional, List


class LayoutAxis(IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1


class LayoutAnchor(IntEnum):
    MIN = 0
    MIDDLE = 1
    MAX = 2


@dataclass(kw_only=True)
class RulerData:
    _class: str = field(default="rulerData")
    base: int = 0
    guides: List[int] = field(default_factory=list)


@dataclass(kw_only=True)
class SimpleGrid:
    _class: str = field(default="simpleGrid")
    gridSize: int = 8
    thickGridTimes: int = 1
    isEnabled: bool = False


@dataclass(kw_only=True)
class LayoutGrid:
    _class: str = field(default="layoutGrid")
    columnWidth: int = 0
    gutterHeight: int = 0
    gutterWidth: int = 0
    horizontalOffset: int = 0
    numberOfColumns: int = 0
    rowHeightMultiplication: int = 0
    totalWidth: int = 0
    guttersOutside: bool = False
    drawHorizontal: bool = False
    drawHorizontalLines: bool = False
    drawVertical: bool = False
    isEnabled: bool = True


@dataclass(kw_only=True)
class FreeFormGroupLayout:
    _class: str = field(default="MSImmutableFreeformGroupLayout")


@dataclass(kw_only=True)
class InferredGroupLayout:
    _class: str = field(default="MSImmutableInferredGroupLayout")
    axis: LayoutAxis
    layoutAnchor: LayoutAnchor
    maxSize: int = 0
    minSize: int = 0


@dataclass(kw_only=True)
class AbstractLayerGroup(AbstractStyledLayer):
    hasClickThrough: bool = False
    groupLayout: Union[FreeFormGroupLayout, InferredGroupLayout] = field(
        default_factory=FreeFormGroupLayout
    )
    layers: List[AbstractLayer] = field(default_factory=list)


@dataclass(kw_only=True)
class Page(AbstractLayerGroup):
    _class: str = field(default="page")
    horizontalRulerData: RulerData = field(default_factory=RulerData)
    verticalRulerData: RulerData = field(default_factory=RulerData)
    grid: SimpleGrid = field(default_factory=SimpleGrid)
    layout: Optional[LayoutGrid] = None


@dataclass(kw_only=True)
class ShapeGroup(AbstractLayerGroup):
    _class: str = field(default="shapeGroup")
    windingRule: WindingRule = WindingRule.NON_ZERO  # Legacy, should match style.windingRule


@dataclass(kw_only=True)
class Group(AbstractLayerGroup):
    _class: str = field(default="group")


@dataclass(kw_only=True)
class Artboard(AbstractLayerGroup):
    _class: str = field(default="artboard")
    horizontalRulerData: RulerData = field(default_factory=RulerData)
    verticalRulerData: RulerData = field(default_factory=RulerData)
    grid: Optional[SimpleGrid] = None
    layout: Optional[LayoutGrid] = None
    hasBackgroundColor: bool = False
    backgroundColor: Color = field(default_factory=Color.White)
    includeBackgroundColorInExport: bool = False
    resizesContent: bool = True
    isFlowHome: bool = False
    overlayBackgroundInteraction: OverlayBackgroundInteraction = OverlayBackgroundInteraction.NONE
    presentationStyle: PresentationStyle = PresentationStyle.SCREEN
    overlaySettings: Optional[FlowOverlaySettings] = None
    prototypeViewport: Optional[PrototypeViewport] = None

    shouldBreakMaskChain: bool = True
    layerListExpandedType: LayerListStatus = LayerListStatus.EXPANDED


@dataclass(kw_only=True)
class OverrideProperty:
    _class: str = field(default="overrideProperty")
    overrideName: str
    canOverride: bool


@dataclass(kw_only=True)
class SymbolMaster(Artboard):
    _class: str = field(default="symbolMaster")
    allowsOverrides: bool = True
    includeBackgroundColorInInstance: bool = False
    symbolID: str
    overrideProperties: List[OverrideProperty] = field(default_factory=list)


@dataclass(kw_only=True)
class OverrideValue:
    _class: str = field(default="overrideValue")
    overrideName: str
    value: Any


@dataclass(kw_only=True)
class SymbolInstance(AbstractStyledLayer):
    _class: str = field(default="symbolInstance")
    preservesSpaceWhenHidden: bool = False
    scale: float = 1
    symbolID: str
    overrideValues: List[OverrideValue] = field(default_factory=list)
