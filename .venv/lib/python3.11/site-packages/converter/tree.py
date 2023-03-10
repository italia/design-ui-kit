from converter import (
    artboard,
    group,
    page,
    rectangle,
    shape,
    shape_path,
    shape_group,
    text,
    slice,
    instance,
    symbol,
)
import logging
from sketchformat.layer_common import AbstractLayer
from sketchformat.layer_group import AbstractLayerGroup
from typing import Dict, Callable, Any
import traceback
from .errors import *
from . import utils

CONVERTERS: Dict[str, Callable[[dict], AbstractLayer]] = {
    "CANVAS": page.convert,
    "ARTBOARD": artboard.convert,
    "GROUP": group.convert,
    "ROUNDED_RECTANGLE": rectangle.convert,
    "RECTANGLE": rectangle.convert,
    "ELLIPSE": shape.convert_oval,
    "VECTOR": shape_path.convert,
    "STAR": shape.convert_star,
    "REGULAR_POLYGON": shape.convert_polygon,
    "TEXT": text.convert,
    "BOOLEAN_OPERATION": shape_group.convert,
    "LINE": shape_path.convert_line,
    "SLICE": slice.convert,
    "SYMBOL": symbol.convert,
    "INSTANCE": instance.convert,
}

POST_PROCESSING: Dict[str, Callable[[dict, Any], AbstractLayer]] = {
    "CANVAS": page.add_page_background,
    "ARTBOARD": artboard.post_process_frame,
    "GROUP": group.post_process_frame,
    "BOOLEAN_OPERATION": shape_group.post_process,
    "SYMBOL": symbol.move_to_symbols_page,
    "INSTANCE": instance.post_process,
}


def convert_node(fig_node: dict, parent_type: str) -> AbstractLayer:
    name = fig_node["name"]
    type_ = get_node_type(fig_node, parent_type)
    logging.debug(f"{type_}: {name}")

    try:
        sketch_item = CONVERTERS[type_](fig_node)
    except Fig2SketchNodeChanged:
        # The fig_node was modified, retry converting with the new values
        # This happens on instance detaching
        return convert_node(fig_node, parent_type)

    if fig_node.get("layoutGrids", []) and type_ != "ARTBOARD":
        utils.log_conversion_warning("GRD001", fig_node)

    children = []
    for child in fig_node.get("children", []):
        try:
            children.append(convert_node(child, fig_node["type"]))
        except Fig2SketchWarning as w:
            utils.log_conversion_warning(w.code, child)
        except Exception as e:
            logging.error(
                f'An unexpected error occurred when converting {child["type"]}: {child["name"]} ({child["guid"]}). It will be skipped\n'
                + "".join(traceback.format_exception(e))
            )

    if children and isinstance(sketch_item, AbstractLayerGroup):
        sketch_item.layers = children

    post_process = POST_PROCESSING.get(type_)
    if post_process:
        sketch_item = post_process(fig_node, sketch_item)

    return sketch_item


def get_node_type(fig_node: dict, parent_type: str) -> str:
    # We do this because Sketch does not support nested artboards
    # If a Frame is detected inside another Frame, the internal one
    # is considered a group
    if fig_node["type"] in ["FRAME", "SECTION"]:
        if parent_type == "CANVAS" and not fig_node["resizeToFit"]:
            return "ARTBOARD"
        else:
            return "GROUP"
    else:
        return fig_node["type"]
