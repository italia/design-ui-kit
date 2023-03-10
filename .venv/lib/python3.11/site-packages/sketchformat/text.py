from .common import Point
from .layer_common import AbstractStyledLayer
from .style import Color
from dataclasses import dataclass, field, InitVar
from enum import IntEnum
from typing import Optional, List, Dict


class TextVerticalAlignment(IntEnum):
    TOP = 0
    MIDDLE = 1
    BOTTOM = 2


class TextAlignment(IntEnum):
    LEFT = 0
    RIGHT = 1
    CENTER = 2
    JUSTIFIED = 3


class TextTransform(IntEnum):
    NONE = 0
    UPPERCASE = 1
    LOWERCASE = 2


class UnderlineStyle(IntEnum):
    NONE = 0
    SINGLE = 1


class TextBehaviour(IntEnum):
    FLEXIBLE_WIDTH = 0
    FIXED_WIDTH = 1
    FIXED_WIDTH_AND_HEIGHT = 2


class Bounds:
    def __init__(self, pos: Point, size: Point):
        self.pos = pos
        self.size = size

    def to_json(self):
        return f"{{{self.pos.to_json()}, {self.size.to_json()}}}"


@dataclass(kw_only=True)
class ParagraphStyle:
    _class: str = field(default="paragraphStyle")
    alignment: TextAlignment
    minimumLineHeight: Optional[float] = None
    maximumLineHeight: Optional[float] = None


@dataclass(kw_only=True)
class OTFeature:
    CTFeatureSelectorIdentifier: int
    CTFeatureTypeIdentifier: int


@dataclass(kw_only=True)
class FontDescriptor:
    _class: str = field(default="fontDescriptor")
    name: InitVar[str]
    size: InitVar[float]
    featureSettings: InitVar[List[OTFeature]] = []
    attributes: Dict = field(default_factory=dict)

    def __post_init__(self, name, size, featureSettings):
        self.attributes = {"name": name, "size": size}
        if featureSettings:
            self.attributes["featureSettings"] = featureSettings


@dataclass(kw_only=True)
class EncodedAttributes:
    MSAttributedStringFontAttribute: FontDescriptor
    MSAttributedStringColorAttribute: Color
    textStyleVerticalAlignmentKey: TextVerticalAlignment
    kerning: float
    paragraphStyle: ParagraphStyle
    MSAttributedStringTextTransformAttribute: Optional[TextTransform] = None
    underlineStyle: Optional[UnderlineStyle] = None
    strikethroughStyle: Optional[UnderlineStyle] = None


@dataclass(kw_only=True)
class StringAttribute:
    _class: str = field(default="stringAttribute")
    location: int
    length: int
    attributes: EncodedAttributes


@dataclass(kw_only=True)
class AttributedString:
    _class: str = field(default="attributedString")
    string: str
    attributes: List[StringAttribute]


@dataclass(kw_only=True)
class Text(AbstractStyledLayer):
    _class: str = field(default="text")
    attributedString: AttributedString
    glyphBounds: Bounds
    textBehaviour: TextBehaviour
    automaticallyDrawOnUnderlyingPath: bool = False
    dontSynchroniseWithSymbol: bool = False
    lineSpacingBehaviour: int = 2  # This is more or less a version number


@dataclass(kw_only=True)
class TextStyle:
    _class: str = field(default="textStyle")
    encodedAttributes: EncodedAttributes
    verticalAlignment: TextVerticalAlignment
