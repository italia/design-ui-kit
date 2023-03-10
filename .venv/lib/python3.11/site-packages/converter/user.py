from sketchformat.layer_group import Page, Point
from typing import List
from . import positioning


# Default area in pixels of the canvas. This is taken from a macbook 16" as a mid-sized device
CANVAS_RESOLUTION = (1200, 900)


def convert(pages: List[Page]) -> dict:
    return {
        "document": {
            "pageListHeight": 200,
            "pageListCollapsed": 0,
            "expandedSymbolPathsInSidebar": [],
            "expandedTextStylePathsInPopover": [],
            "libraryListCollapsed": 0,
        },
        **{page.do_objectID: default_viewport(page) for page in pages},
    }


def default_viewport(page: Page) -> dict:
    if not page.layers:
        return {"scrollOrigin": Point(0, 0), "zoomValue": 1}

    bbox = positioning.group_bbox(page.layers)
    w = bbox[1] - bbox[0]
    h = bbox[3] - bbox[2]

    # Calculate scale to fit bound in expected canvas size, with some margin
    scale = min(CANVAS_RESOLUTION[0] / w, CANVAS_RESOLUTION[1] / h) * 0.8

    # Center the drawing in the expected canvas size
    x = bbox[0] - (CANVAS_RESOLUTION[0] - w * scale) / scale / 2
    y = bbox[2] - (CANVAS_RESOLUTION[1] - h * scale) / scale / 2
    pos = Point(-x * scale, -y * scale)

    return {"scrollOrigin": pos, "zoomValue": scale}
