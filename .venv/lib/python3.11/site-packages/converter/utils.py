import hashlib
import logging
import struct
import uuid
from .config import config
from typing import Sequence, Dict, Optional

issued_warnings: Dict[tuple[int, int], list[str]] = {}


def gen_object_id(fig_id: Sequence[int], suffix: bytes = b"") -> str:
    # Generate UUIDs by hashing the fig GUID with a salt
    salted_id = config.salt + struct.pack("<" + "I" * len(fig_id), *fig_id) + suffix
    uuid_bytes = bytearray(hashlib.shake_128(salted_id).digest(16))

    # Override bits to match UUIDv4
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x40
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80

    return str(uuid.UUID(bytes=bytes(uuid_bytes))).upper()


def generate_file_ref(data: bytes) -> str:
    return hashlib.sha1(hashlib.sha1(data).digest()).hexdigest()


def get_style_table_override(fig_item):
    override_table = {0: {}}

    if "styleOverrideTable" in fig_item:
        override_table.update({s["styleID"]: s for s in fig_item["styleOverrideTable"]})

    return override_table


UINT_MAX = 4294967295


def is_invalid_ref(uuid: Optional[Sequence[int]]) -> bool:
    return uuid is None or uuid[0] == UINT_MAX or uuid[1] == UINT_MAX


def has_rounded_corners(fig: dict) -> bool:
    return any(
        [
            fig.get(c, 0) != 0
            for c in [
                "rectangleTopLeftCornerRadius",
                "rectangleTopLeftCornerRadius",
                "rectangleTopLeftCornerRadius",
                "rectangleTopLeftCornerRadius",
            ]
        ]
    )


WARNING_MESSAGES = {
    "TXT001": "is missing the glyphs property. If the text has unicode characters, it may not convert the format properly",
    "TXT002": "has multiple text fill colors. Only the first one will be converted",
    "TXT003": "has a non-solid text color (gradient or image) which is not supported by Sketch",
    "TXT004": "contains a 'TITLE' transformation. Sketch does not support this text transformation, so no transformation is applied",
    "TXT005": "contains a LIST style with list markers. This style will be ignored",
    "TXT006": "uses OpenType features not supported by Sketch: {features}. They will be ignored",
    "SHP001": "contains a line with at least one 'Reversed triangle' end. This type of marker does not exist in Sketch. It has been converted to a 'Line' type marker",
    "SHP002": "does not have any points. It will be skipped",
    "STY001": "contains a layer blur and a background blur. Only one will be converted",
    "STY002": "contains a DIAMOND gradient, which is not supported. It is converted to a RADIAL gradient",
    "STY003": "contains a fill with a non-standard blend mode, which is not supported at the fill level (us the layer blend mode instead). It will be ignored",
    "STY004": "has a cropped image background, which is not supported yet. It will be set to stretch",
    "STY005": "contains a image fill property, which is not supported. The extra properties will be ignored",
    "SYM001": "references an invalid symbol. It will be converted to an empty placeholder group",
    "SYM002": "overrides unsupported properties: {props}. The override will be ignored",
    "SYM003": "overrides unsupported properties: {props}. The instance will be detached",
    "SYM004": "contains an override of an unknown node {node_ref}. The override will be ignored",
    "ART001": "has at least one corner radius which is not supported by sketch artboards. The corner radius will be ignored",
    "ART002": "is being converted to an artboard. However, artboard rotations are not supported. Rotation will be ignored",
    "ART003": "has a style that is not supported by sketch artboards. It will add a background rectangle to the artboard with the frame style",
    "GRP001": "has inner shadows which are not supported at group level in Sketch. It will be copied to the layers inside the frame",
    "GRP002": "has children with different resizing constraints. This cannot be accurately represented in Sketch so the converted group will not scale correctly",
    "CMP001": "uses a shared style which could not be found in the document. It will not be applied",
    "POS001": "contains NaN in the positioning matrix and cannot be converted. It will be skipped",
    "PRT001": "uses an unsupported interaction type: {props}. Prototype interaction ignored",
    "PRT002": "has multiple actions per layer, which is not supported. Only the first one will be converted",
    "PRT003": "has an action with an unsupported navigation type: {props}. This action will be ignored",
    "PRT004": "has an action with an unsupported connection type: {props}. This action will be ignored",
    "PRT005": "has a prototype with a scroll overflow which is not supported. This setting will be ignored.",
    "GRD001": "has a layout grid which is only supported in Sketch artboards. It will be ignored",
    "GRD002": "has multiple grids but their sizes that are not multiples of each other. The larger one will not be converted",
    "GRD003": "has more than three or more grids and Sketch only supports two. Only the two finer grids will be converted",
    "GRD004": "has more than one layouts in the same axis. Only the first one will be converted",
    "GRD005": "has a row layout with a set height which is not supported by Sketch. It will be converted to a layout grid taking the whole height of the artboard",
    "GRD006": "has a row layout with an offset that is not supported. The offset will be ignored",
    "GRD007": "has a row layout with non-integer ratio between gutter and row size. The row layout will not be converted",
    "GRD008": "has a row and column layout. The rows will only be as wide as the columns (instead of taking the entire width of the artboard)",
    "IMG001": "appears to be corrupted in the .fig file, it will not be converted. Try passing --force-convert-images to try to convert it anyway",
    "IMG002": "appears to be corrupted in the .fig file, it will not be converted",
    "IMG003": "is missing from the .fig file, it will not be converted",
}


def log_conversion_warning(warning_code: str, fig_node: dict, **kw: list) -> None:
    if fig_node["guid"] not in issued_warnings:
        issued_warnings[fig_node["guid"]] = [warning_code]
    elif warning_code not in issued_warnings[fig_node["guid"]]:
        issued_warnings[fig_node["guid"]].append(warning_code)
    else:
        return
    logging.info(
        f"[{warning_code}] {fig_node['type']} '{fig_node['name']}' {WARNING_MESSAGES[warning_code].format(**kw)}"
    )
