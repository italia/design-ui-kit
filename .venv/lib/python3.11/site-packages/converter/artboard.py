import math
from . import base, group, prototype, rectangle
from converter import utils
from sketchformat.layer_group import Artboard, SimpleGrid, LayoutGrid, Rect
from sketchformat.style import Fill, FillType
from typing import Optional
from collections import namedtuple


def convert(fig_frame: dict) -> Artboard:
    obj = Artboard(
        **base.base_styled(fig_frame),
        **prototype.prototyping_information(fig_frame),
        grid=convert_grid(fig_frame),
    )

    obj.layout = convert_layout(fig_frame, obj.frame)

    return obj


def post_process_frame(fig_frame: dict, sketch_artboard: Artboard) -> Artboard:
    # Sketch only supports one custom color as an artboard background
    # If the frame has more than one color or other custom style we just create
    # the background rectangle with whatever style
    # If the frame/artboard has just one color (and not any other custom style)
    # we set the background color in sketch property
    # We could just always create the rectangle to simplify the logic, but I guess
    # adding always a background rectangle is an overhead for the document itself
    if utils.has_rounded_corners(fig_frame):
        utils.log_conversion_warning("ART001", fig_frame)
        group.create_clip_mask_if_needed(fig_frame, sketch_artboard)

    if sketch_artboard.rotation != 0:
        utils.log_conversion_warning("ART002", fig_frame)

    # The .fig file clips overlays implicitly but .sketch doesn't, so we must add a mask
    if sketch_artboard.overlaySettings is not None:
        sketch_artboard.layers.insert(
            0, rectangle.make_clipping_rect(fig_frame, sketch_artboard.frame)
        )

    match sketch_artboard.style.fills:
        case [Fill(fillType=FillType.COLOR, color=color, isEnabled=True)]:
            # Single color, apply to artboard
            sketch_artboard.backgroundColor = color
            sketch_artboard.hasBackgroundColor = True
            sketch_artboard.style.fills = []

    if sketch_artboard.style.fills or sketch_artboard.style.borders:
        # Anything else, add a background rect
        utils.log_conversion_warning("ART003", fig_frame)
        group.convert_frame_style(fig_frame, sketch_artboard)

    return sketch_artboard


def convert_grid(fig_frame: dict) -> Optional[SimpleGrid]:
    grids = sorted(
        [g for g in fig_frame.get("layoutGrids", []) if g["pattern"] == "GRID"],
        key=lambda x: x["sectionSize"],
    )
    if not grids:
        return None

    primary = grids[0]["sectionSize"]
    secondary = None
    for g in grids[1:]:
        size = g["sectionSize"]
        if size % primary == 0:
            if secondary:
                utils.log_conversion_warning("GRD003", fig_frame)
            else:
                secondary = size
        else:
            utils.log_conversion_warning("GRD002", fig_frame)

    return SimpleGrid(
        gridSize=primary,
        thickGridTimes=secondary / primary if secondary else 0,
        isEnabled=True,
    )


def convert_layout(fig_frame: dict, frame: Rect) -> Optional[LayoutGrid]:
    layouts = [g for g in fig_frame.get("layoutGrids", []) if g["pattern"] == "STRIPES"]

    if not layouts:
        return None

    columns = [l for l in layouts if l["axis"] == "X"]
    if len(columns) > 1:
        utils.log_conversion_warning("GRD004", fig_frame)

    col_config = {}
    if columns:
        sizes = calculate_layout(columns[0], frame.width)

        col_config = {
            "columnWidth": sizes.item_size,
            "gutterWidth": columns[0]["gutterSize"],
            "numberOfColumns": sizes.item_count,
            "totalWidth": sizes.size,
            "drawVertical": True,
            "horizontalOffset": sizes.offset,
        }

    rows = [l for l in layouts if l["axis"] == "Y"]
    if len(rows) > 1:
        utils.log_conversion_warning("GRD004", fig_frame)

    row_config = {}
    if rows:
        gutter_size = rows[0]["gutterSize"]
        sizes = calculate_layout(rows[0], frame.height)

        if sizes.size != frame.height:
            utils.log_conversion_warning("GRD005", fig_frame)

        if sizes.offset != 0:
            utils.log_conversion_warning("GRD006", fig_frame)

        if gutter_size <= 0:
            utils.log_conversion_warning("GRD007", fig_frame)
            gutter_size = 1

        row_scale = sizes.item_size / gutter_size
        int_row_scale = round(row_scale)
        if abs(row_scale - int_row_scale) > 0.01:
            utils.log_conversion_warning("GRD007", fig_frame)
        else:
            row_config = {
                "drawHorizontal": True,
                "gutterHeight": gutter_size,
                "rowHeightMultiplication": int_row_scale,
            }

            if col_config:
                utils.log_conversion_warning("GRD007", fig_frame)
            else:
                row_config["totalWidth"] = frame.width

    if not col_config and not row_config:
        return None

    return LayoutGrid(**col_config, **row_config)


LayoutSizes = namedtuple("LayoutSizes", ["size", "offset", "item_count", "item_size"])


def calculate_layout(layout: dict, size: float) -> LayoutSizes:
    item_num = layout["numSections"]
    gutter_width = layout["gutterSize"]
    item_width = layout["sectionSize"]
    offset = layout["offset"]

    if layout["type"] == "STRETCH":
        if item_num == 2147483647:
            item_num = 1
        total_gutter = (item_num - 1) * gutter_width
        item_width = (size - total_gutter - 2 * offset) / item_num
        if item_width < 0:
            item_width = 0
        layout_size = size
    else:
        if item_num == 2147483647:
            item_num = math.ceil(size / item_width)

        layout_size = item_width * item_num + gutter_width * (item_num - 1)
        if layout["type"] == "MAX":
            offset = size - layout_size
        elif layout["type"] == "CENTER":
            offset = (size - layout_size) / 2

    return LayoutSizes(layout_size, offset, item_num, item_width)
