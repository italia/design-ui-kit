from converter import utils
from . import style
from sketchformat.document import Swatch
from typing import Optional


def convert(fig_style: dict) -> Optional[Swatch]:
    match fig_style:
        # Fill with a single fill -> color variable
        case {"styleType": "FILL", "fillPaints": [{"type": "SOLID"} as paint]}:
            uuid = utils.gen_object_id(fig_style["guid"])
            color = style.convert_color(paint["color"], paint["opacity"])
            color.swatchID = uuid
            return Swatch(do_objectID=uuid, name=fig_style["name"], value=color)
        case _:
            return None
