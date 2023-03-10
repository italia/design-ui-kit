from . import style, positioning
from converter import utils
from sketchformat.layer_group import *
from sketchformat.layer_shape import Rectangle
from sketchformat.style import Fill
from typing import Sequence


def convert(fig_canvas: dict) -> Page:
    return make_page(fig_canvas["guid"], fig_canvas["name"])


def symbols_page() -> Page:
    page = make_page((0, 0), "Symbols", suffix=b"symbols_page")

    return page


def make_page(guid: Sequence[int], name: str, suffix: bytes = b"") -> Page:
    return Page(
        do_objectID=utils.gen_object_id(guid, suffix),
        frame=Rect(height=300, width=300, x=0, y=0),
        name=name,
        resizingConstraint=63,
        rotation=0.0,
        style=Style(do_objectID=utils.gen_object_id(guid, suffix + b"style")),
        hasClickThrough=True,
    )


DEFAULT_CANVAS_BACKGROUND = Color(
    red=0.9607843160629272, green=0.9607843160629272, blue=0.9607843160629272, alpha=1
)


def add_page_background(fig_canvas, sketch_page):
    background_color = style.convert_color(
        fig_canvas["backgroundColor"], fig_canvas["backgroundOpacity"]
    )
    if background_color != DEFAULT_CANVAS_BACKGROUND:
        page_bbox = positioning.group_bbox(sketch_page.layers)
        sketch_page.layers.insert(
            0,
            Rectangle(
                do_objectID=utils.gen_object_id(fig_canvas["guid"], b"background"),
                name="Page background",
                style=Style(
                    do_objectID=utils.gen_object_id(fig_canvas["guid"], b"background_style"),
                    fills=[Fill.Color(background_color)],
                ),
                resizingConstraint=0,
                rotation=0,
                frame=Rect(
                    x=page_bbox[0] - 1000,
                    y=page_bbox[2] - 1000,
                    width=(page_bbox[1] - page_bbox[0]) + 2000,
                    height=(page_bbox[3] - page_bbox[2]) + 2000,
                ),
            ),
        )

    return sketch_page
