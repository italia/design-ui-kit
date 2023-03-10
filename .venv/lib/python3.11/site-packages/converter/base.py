import logging
from sketchformat.layer_common import *
from sketchformat.layer_shape import *
from sketchformat.style import *
from typing import TypedDict

from . import positioning, style, prototype, utils
from .context import context

SUPPORTED_INHERIT_STYLES = {
    "inheritFillStyleID": ("fillPaints",),
    "inheritFillStyleIDForStroke": (),  # Special cased below
    "inheritStrokeStyleID": (),  # Unused?
    "inheritTextStyleID": (
        "fontName",
        "textCase",
        "fontSize",
        "textDecoration",
        "letterSpacing",
        "lineHeight",
        "paragraphSpacing",
    ),
    "inheritExportStyleID": (),  # Unused?
    "inheritEffectStyleID": ("blur", "shadows", "innerShadows"),
    "inheritGridStyleID": ("layoutGrids"),
    "inheritFillStyleIDForBackground": (),  # Unused?
}


class _Masking(TypedDict):
    shouldBreakMaskChain: bool
    hasClippingMask: bool
    clippingMaskMode: ClippingMaskMode


class _BaseLayer(positioning._Positioning, prototype._Flow):
    do_objectID: str
    name: str
    booleanOperation: BooleanOperation
    exportOptions: ExportOptions
    isFixedToViewport: bool
    isLocked: bool
    isVisible: bool
    layerListExpandedType: LayerListStatus
    nameIsFixed: bool
    resizingConstraint: int
    resizingType: ResizeType
    isTemplate: bool


def base_layer(fig_node: dict) -> _BaseLayer:
    # TODO: Hack for groups that only contain non-visible items
    if math.isnan(fig_node["size"]["x"]):
        fig_node["size"] = {"x": 1, "y": 1}

    return {
        "do_objectID": utils.gen_object_id(fig_node["guid"]),
        "name": fig_node["name"],
        "booleanOperation": -1,
        "exportOptions": export_options(fig_node.get("exportSettings", [])),
        **positioning.convert(fig_node),  # type: ignore
        "isFixedToViewport": False,
        "isLocked": fig_node["locked"],
        "isVisible": fig_node["visible"],
        "layerListExpandedType": 0,
        "nameIsFixed": False,
        "resizingConstraint": resizing_constraint(fig_node),
        "resizingType": ResizeType.STRETCH,
        **prototype.convert_flow(fig_node),  # type: ignore
        "isTemplate": False,
    }


class _BaseStyled(_BaseLayer, _Masking):
    style: Style


def base_styled(fig_node: dict) -> _BaseStyled:
    obj: _BaseShape = {
        **base_layer(fig_node),  # type: ignore
        **masking(fig_node),  # type: ignore
        "style": process_styles(fig_node),
    }

    if obj["hasClippingMask"] and obj["clippingMaskMode"] == 0:
        # Outline mask behave differently in fig files and Sketch in regard to fill/stroke colors
        # Remove fill
        obj["style"].fills = []
        # TODO: If we have stroke, we should remove it and enlarge ourselves to occupy that space
        # which is quite tricky in things like shapePaths. This should be pretty rare in practice

    return obj


class _BaseShape(_BaseStyled):
    pointRadiusBehaviour: PointRadiusBehaviour


def base_shape(fig_node: dict) -> _BaseShape:
    return {
        **base_styled(fig_node),  # type: ignore
        # Sketch smooth corners are a boolean, but here it's a percent. Use an arbitrary threshold
        "pointRadiusBehaviour": PointRadiusBehaviour.V1_SMOOTH
        if fig_node.get("cornerSmoothing", 0) > 0.4
        else PointRadiusBehaviour.V1,
    }


def process_styles(fig_node: dict) -> Style:
    # First we apply any overrides that we may have (from inherit* properties)
    # If any of them can be linked as a shared style, we keep track of them to add the IDs at
    # the end
    components = {}
    for inherit_style, copy_keys in SUPPORTED_INHERIT_STYLES.items():
        inherit_node_id = fig_node.get(inherit_style)
        if inherit_node_id is None or utils.is_invalid_ref(inherit_node_id):
            continue

        try:
            inherit_node, sketch_component = context.component(inherit_node_id)
        except KeyError:
            utils.log_conversion_warning("CMP001", fig_node)
            continue

        if inherit_style == "inheritFillStyleIDForStroke":
            fig_node["strokePaints"] = inherit_node["fillPaints"]
        elif inherit_style is not None:
            for key in copy_keys:
                if key in inherit_node:
                    fig_node[key] = inherit_node[key]
        else:
            logging.warning(f"Unsupported {inherit_style}, it will not be copied")

        if sketch_component:
            components[inherit_style] = sketch_component

    st = style.convert(fig_node)

    for key, value in components.items():
        if key == "inheritFillStyleID":
            st.fills[0].color = value.value
        elif key == "inheritFillStyleIDForStroke":
            st.borders[0].color = value.value
        else:
            logging.error(f"Unexpected component for {key}")

    return st


def export_options(fig_export_settings: dict) -> ExportOptions:
    return ExportOptions(
        exportFormats=[
            ExportFormat(
                fileFormat=s["imageType"].lower(),
                name=s["suffix"],
                **export_scale(s["constraint"]),
            )
            for s in fig_export_settings
        ]
    )


class _ExportScale(TypedDict):
    absoluteSize: int
    scale: float
    visibleScaleType: VisibleScaleType


def export_scale(fig_constraint: dict) -> _ExportScale:
    match fig_constraint:
        case {"type": "CONTENT_SCALE", "value": scale}:
            return {
                "absoluteSize": 0,
                "scale": scale,
                "visibleScaleType": VisibleScaleType.SCALE,
            }
        case {"type": "CONTENT_WIDTH", "value": size}:
            return {
                "absoluteSize": size,
                "scale": 0,
                "visibleScaleType": VisibleScaleType.WIDTH,
            }
        case {"type": "CONTENT_HEIGHT", "value": size}:
            return {
                "absoluteSize": size,
                "scale": 0,
                "visibleScaleType": VisibleScaleType.HEIGHT,
            }
        case _:
            logging.warning("Unknown export scale")
            return {
                "absoluteSize": 0,
                "scale": 1,
                "visibleScaleType": VisibleScaleType.SCALE,
            }


# resizingConstraint is a bitfield:
#  1: right sizeable
#  2: width sizeable
#  4: left sizeable
#  8: bottom sizeable
# 16: height sizeable
# 32: top sizeable
# 64: all fixed (should be 0 but it's overridden to mean all sizeable, same as 63). Impossible
HORIZONTAL_CONSTRAINT = {
    "MIN": 1,  # Fixed left + width
    "CENTER": 5,  # Fixed width
    "MAX": 4,  # Fixed right + width
    "STRETCH": 2,  # Fixed left and right
    "SCALE": 7,  # All free
    # 'FIXED_MIN': 0, # Unused?
    # 'FIXED_MAX': 0, # Unused?
}


# Vertical constraints are equivalent to horizontal ones, with a 3 bit shift
def resizing_constraint(fig_node: dict) -> int:
    h = HORIZONTAL_CONSTRAINT[fig_node["horizontalConstraint"]]
    v = HORIZONTAL_CONSTRAINT[fig_node["verticalConstraint"]] << 3
    return h + v


CLIPPING_MODE = {
    "ALPHA": ClippingMaskMode.ALPHA,
    "OUTLINE": ClippingMaskMode.OUTLINE,
}


def masking(fig_node: dict) -> _Masking:
    return {
        "shouldBreakMaskChain": False,
        "hasClippingMask": bool(fig_node.get("mask")),
        "clippingMaskMode": CLIPPING_MODE[fig_node.get("maskType", "OUTLINE")],
    }
