from . import base
from converter import utils
from sketchformat.layer_common import Rect, ClippingMaskMode
from sketchformat.layer_shape import Rectangle
from sketchformat.style import Style
from typing import Tuple


def convert(fig_rect: dict) -> Rectangle:
    radius, corners = convert_corners(fig_rect)
    return Rectangle(
        **base.base_shape(fig_rect),
        fixedRadius=radius,
        corners=corners,
    )


def convert_corners(fig_rect: dict) -> Tuple[float, Rectangle.Corners]:
    radius = fig_rect.get("cornerRadius", 0)
    fixed = not fig_rect.get("rectangleCornerRadiiIndependent", True)
    return radius, Rectangle.Corners(
        radius if fixed else fig_rect.get("rectangleTopLeftCornerRadius", 0),
        radius if fixed else fig_rect.get("rectangleTopRightCornerRadius", 0),
        radius if fixed else fig_rect.get("rectangleBottomRightCornerRadius", 0),
        radius if fixed else fig_rect.get("rectangleBottomLeftCornerRadius", 0),
    )


def make_clipping_rect(fig: dict, frame: Rect) -> Rectangle:
    obj = make_background_rect(fig, frame, "Clip")
    obj.hasClippingMask = True
    obj.clippingMaskMode = ClippingMaskMode.OUTLINE
    return obj


def make_background_rect(fig: dict, frame: Rect, name: str) -> Rectangle:
    radius, corners = convert_corners(fig)
    return Rectangle(
        do_objectID=utils.gen_object_id(fig["guid"], name.encode()),
        name=name,
        frame=Rect(height=frame.height, width=frame.width, x=0, y=0),
        style=Style(do_objectID=utils.gen_object_id(fig["guid"], f"{name}_style".encode())),
        resizingConstraint=10,
        rotation=0,
        fixedRadius=radius,
        corners=corners,
    )
