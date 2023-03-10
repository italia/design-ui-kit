import dataclasses
import math
from .positioning import Vector, Matrix
from converter import utils
from sketchformat.style import *
from typing import List, TypedDict

BORDER_POSITION = {
    "CENTER": BorderPosition.CENTER,
    "INSIDE": BorderPosition.INSIDE,
    "OUTSIDE": BorderPosition.OUTSIDE,
}

LINE_CAP_STYLE = {
    "NONE": LineCapStyle.BUTT,
    "ROUND": LineCapStyle.ROUND,
    "SQUARE": LineCapStyle.SQUARE,
    "LINE_ARROW": LineCapStyle.SQUARE,
    "ARROW_LINES": LineCapStyle.SQUARE,
    "TRIANGLE_ARROW": LineCapStyle.SQUARE,
    "TRIANGLE_FILLED": LineCapStyle.SQUARE,
}

LINE_JOIN_STYLE = {
    "MITER": LineJoinStyle.MITER,
    "ROUND": LineJoinStyle.ROUND,
    "BEVEL": LineJoinStyle.BEVEL,
}

PATTERN_FILL_TYPE = {
    "STRETCH": PatternFillType.STRETCH,
    "FIT": PatternFillType.FIT,
    "FILL": PatternFillType.FILL,
    "TILE": PatternFillType.TILE,
}

BLEND_MODE = {
    "PASS_THROUGH": BlendMode.NORMAL,
    "NORMAL": BlendMode.NORMAL,
    "DARKEN": BlendMode.DARKEN,
    "MULTIPLY": BlendMode.MULTIPLY,
    # 'LINEAR_BURN': , Unused?
    "COLOR_BURN": BlendMode.COLOR_BURN,
    "LIGHTEN": BlendMode.LIGHTEN,
    "SCREEN": BlendMode.SCREEN,
    # 'LINEAR_DODGE': , Unused?
    "COLOR_DODGE": BlendMode.COLOR_DODGE,
    "OVERLAY": BlendMode.OVERLAY,
    "SOFT_LIGHT": BlendMode.SOFT_LIGHT,
    "HARD_LIGHT": BlendMode.HARD_LIGHT,
    "DIFFERENCE": BlendMode.DIFFERENCE,
    "EXCLUSION": BlendMode.EXCLUSION,
    "HUE": BlendMode.HUE,
    "SATURATION": BlendMode.SATURATION,
    "COLOR": BlendMode.COLOR,
    "LUMINOSITY": BlendMode.LUMINOSITY,
}


def convert(fig_node: dict) -> Style:
    sketch_style = Style(
        do_objectID=utils.gen_object_id(fig_node["guid"], b"style"),
        borderOptions=BorderOptions(
            lineCapStyle=LINE_CAP_STYLE[fig_node["strokeCap"]]
            if "strokeCap" in fig_node
            else BorderOptions.__dict__["lineCapStyle"],
            lineJoinStyle=LINE_JOIN_STYLE[fig_node["strokeJoin"]]
            if "strokeJoin" in fig_node
            else BorderOptions.__dict__["lineCapStyle"],
            dashPattern=fig_node.get("dashPattern", []),
        ),
        borders=[convert_border(fig_node, b) for b in fig_node["strokePaints"]]
        if "strokePaints" in fig_node
        else [],
        fills=[convert_fill(fig_node, f) for f in fig_node["fillPaints"]]
        if "fillPaints" in fig_node
        else [],
        **convert_effects(fig_node),
        contextSettings=context_settings(fig_node),
    )
    return sketch_style


def convert_border(fig_node: dict, fig_border: dict) -> Border:
    return Border.from_fill(
        convert_fill(fig_node, fig_border),
        position=BORDER_POSITION[fig_node.get("strokeAlign", "CENTER")],
        thickness=fig_node["strokeWeight"],
    )


def convert_fill(fig_node: dict, fig_fill: dict) -> Fill:
    if fig_fill.get("blendMode", "NORMAL") != "NORMAL":
        utils.log_conversion_warning("STY003", fig_node)

    match fig_fill:
        case {"type": "EMOJI"}:
            raise Exception("Unsupported fill: EMOJI")
        case {"type": "SOLID"}:
            # Solid color backgrounds do not support specifying the opacity
            # Instead, it must be set in the color itself
            return Fill.Color(
                convert_color(fig_fill["color"], fig_fill["opacity"]),
                isEnabled=fig_fill["visible"],
            )
        case {"type": "IMAGE"}:
            if "transform" in fig_fill and fig_fill["transform"] != Matrix(
                [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            ):
                utils.log_conversion_warning("STY004", fig_node)

            if "paintFilter" in fig_fill:
                utils.log_conversion_warning("STY005", fig_node)

            return Fill.Image(
                f'images/{fig_fill["image"]["filename"]}',
                patternFillType=PATTERN_FILL_TYPE[fig_fill["imageScaleMode"]],
                patternTileScale=fig_fill.get("scale", 1),
                isEnabled=fig_fill["visible"],
                opacity=fig_fill.get("opacity", 1),
            )
        case _:
            return Fill.Gradient(
                convert_gradient(fig_node, fig_fill),
                isEnabled=fig_fill["visible"],
                opacity=fig_fill.get("opacity", 1),
            )


def convert_color(color: dict, opacity: Optional[float] = None) -> Color:
    return Color(
        red=color["r"],
        green=color["g"],
        blue=color["b"],
        alpha=color["a"] if opacity is None else opacity,
    )


def convert_gradient(fig_node: dict, fig_fill: dict) -> Gradient:
    # Convert positions depending on the gradient type
    mat = fig_fill["transform"]

    invmat = mat.inv()

    rotation_offset = 0.0
    if fig_fill["type"] == "GRADIENT_LINEAR":
        # Linear gradients always go from (0, .5) to (1, .5)
        # We just apply the transform to get the coordinates (in a 1x1 square)
        return Gradient.Linear(
            from_=Point.from_array(invmat.dot([0, 0.5, 1])),
            to=Point.from_array(invmat.dot([1, 0.5, 1])),
            stops=convert_stops(fig_fill["stops"]),
        )
    elif fig_fill["type"] in ["GRADIENT_RADIAL", "GRADIENT_DIAMOND"]:
        if fig_fill["type"] == "GRADIENT_DIAMOND":
            utils.log_conversion_warning("STY002", fig_node)

        # Angular gradients have the center at (.5, .5), the vertex at (1, .5)
        # and the co-vertex at (.5, 1). We transform them to the coordinates in a 1x1 square
        point_from = invmat.dot([0.5, 0.5, 1])  # Center
        point_to = invmat.dot([1, 0.5, 1])
        point_ellipse = invmat.dot([0.5, 1, 1])

        # Sketch defines the ratio between axis in the item reference point (not the 1x1 square)
        # So we scale the 1x1 square coordinates to fit the ratio of the item frame before
        # calculating the ellipse's ratio
        stroke = fig_node.get("strokeWeight", 0)
        try:
            x_scale = (fig_node["size"]["x"] + 2 * stroke) / (fig_node["size"]["y"] + 2 * stroke)
        except:
            x_scale = 1

        ellipse_ratio = scaled_distance(point_from, point_ellipse, x_scale) / scaled_distance(
            point_from, point_to, x_scale
        )

        return Gradient.Radial(
            from_=Point.from_array(point_from),
            to=Point.from_array(point_to),
            elipseLength=ellipse_ratio,
            stops=convert_stops(fig_fill["stops"]),
        )
    else:
        # Angular gradients don't allow positioning, but we can at least rotate them
        rotation_offset = (
            math.atan2(-fig_fill["transform"][1][0], fig_fill["transform"][0][0]) / 2 / math.pi
        )

        return Gradient.Angular(stops=convert_stops(fig_fill["stops"], rotation_offset))


def convert_stops(fig_stops: List[dict], rotation_offset: float = 0.0) -> List[GradientStop]:
    stops = [
        GradientStop(
            color=convert_color(stop["color"]),
            position=rotated_stop(stop["position"], rotation_offset),
        )
        for stop in fig_stops
    ]

    if rotation_offset:
        # When we have a rotated angular gradient, stops at 0 and 1 both convert
        # to the exact same position and that confuses Sketch. Force a small difference
        stops[-1].position -= 0.00001
    else:
        # Always add a stop at 0 and 1 if needed
        if stops[0].position != 0:
            stops.insert(0, dataclasses.replace(stops[0], position=0))

        if stops[-1].position != 1:
            stops.append(dataclasses.replace(stops[-1], position=1))

    return stops


def scaled_distance(a: Vector, b: Vector, x_scale: float) -> float:
    v = a - b
    return ((v[0] * x_scale) ** 2 + v[1] ** 2) ** 0.5


def rotated_stop(position: float, offset: float) -> float:
    pos = position + offset
    if pos > 1:
        pos -= 1
    elif pos < 0:
        pos += 1
    if pos < 0:
        pos += 1
    return pos


class _Effects(TypedDict):
    blur: Blur
    shadows: List[Shadow]
    innerShadows: List[InnerShadow]


def convert_effects(fig_node: dict) -> _Effects:
    sketch: _Effects = {"blur": Blur.Disabled(), "shadows": [], "innerShadows": []}

    for e in fig_node.get("effects", []):
        if e["type"] == "INNER_SHADOW":
            sketch["innerShadows"].append(
                InnerShadow(
                    blurRadius=e["radius"],
                    offsetX=e["offset"]["x"],
                    offsetY=e["offset"]["y"],
                    spread=e["spread"],
                    color=convert_color(e["color"]),
                )
            )

        elif e["type"] == "DROP_SHADOW":
            sketch["shadows"].append(
                Shadow(
                    blurRadius=e["radius"],
                    offsetX=e["offset"]["x"],
                    offsetY=e["offset"]["y"],
                    spread=e["spread"],
                    color=convert_color(e["color"]),
                )
            )

        elif e["type"] == "FOREGROUND_BLUR":
            if sketch["blur"].isEnabled:
                utils.log_conversion_warning("STY001", fig_node)
                continue

            sketch["blur"] = Blur(
                radius=e["radius"] / 2,  # Looks best dividing by 2, no idea why,
                type=BlurType.GAUSSIAN,
            )

        elif e["type"] == "BACKGROUND_BLUR":
            if sketch["blur"].isEnabled:
                utils.log_conversion_warning("STY001", fig_node)
                continue

            sketch["blur"] = Blur(
                radius=e["radius"] / 2,  # Looks best dividing by 2, no idea why,
                type=BlurType.BACKGROUND,
            )

        else:
            raise Exception(f'Unsupported effect: {e["type"]}')

    return sketch


def context_settings(fig_node: dict) -> ContextSettings:
    blend_mode = BLEND_MODE[fig_node["blendMode"]]
    opacity = fig_node["opacity"]

    if fig_node["blendMode"] == "NORMAL" and opacity == 1:
        # Sketch interprets normal at 100% opacity as pass-through
        opacity = 0.99

    return ContextSettings(blendMode=blend_mode, opacity=opacity)
