from . import instance, group, base, prototype
from .context import context
from converter import utils
from sketchformat.layer_group import *

LAYOUT_AXIS = {
    "NONE": None,
    "HORIZONTAL": LayoutAxis.HORIZONTAL,
    "VERTICAL": LayoutAxis.VERTICAL,
}

LAYOUT_ANCHOR = {
    "MIN": LayoutAnchor.MIN,
    "CENTER": LayoutAnchor.MIDDLE,
    "MAX": LayoutAnchor.MAX,
    "BASELINE": LayoutAnchor.MIDDLE,
    "SPACE_EVENLY": LayoutAnchor.MIDDLE,
}


def convert(fig_symbol):
    # A symbol is an artboard with a symbolID
    master = SymbolMaster(
        **base.base_styled(fig_symbol),
        **prototype.prototyping_information(fig_symbol),
        symbolID=utils.gen_object_id(fig_symbol["guid"]),
    )

    # Keep the base ID as the symbol reference, create a new one for the container
    master.do_objectID = utils.gen_object_id(fig_symbol["guid"], b"symbol_master")

    # Also add group layout if auto-layout is enabled
    axis = LAYOUT_AXIS[fig_symbol.get("stackMode", "NONE")]
    if axis is not None:
        anchor = LAYOUT_ANCHOR[fig_symbol.get("stackPrimaryAlignItems", "MIN")]

        master.groupLayout = InferredGroupLayout(
            axis=axis,
            layoutAnchor=anchor,
        )

    # Use better names for variants if possible
    try:
        parent = context.fig_node(fig_symbol["parent"]["guid"])
        if parent and parent.get("isStateGroup", False):
            master.name = symbol_variant_name(parent, fig_symbol)
        elif "=" in fig_symbol["name"]:
            import pdb

            pdb.set_trace()
    except Exception as e:
        print(e)

    return master


def move_to_symbols_page(fig_symbol, sketch_symbol):
    if utils.has_rounded_corners(fig_symbol):
        group.create_clip_mask_if_needed(fig_symbol, sketch_symbol)

    # Apply frame transforms
    group.convert_frame_style(fig_symbol, sketch_symbol)

    # After the entire symbol is converted, move it to the Symbols page
    context.add_symbol(sketch_symbol)

    # Since we put the Symbol in a different page in Sketch, leave an instance where the
    # master used to be
    return instance.master_instance(fig_symbol)


def symbol_variant_name(parent, symbol):
    property_values = [x.strip().split("=")[1] for x in symbol["name"].split(",")]
    ordered_values = [parent["name"]] + property_values
    return "/".join(ordered_values)
