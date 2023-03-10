from . import base
from sketchformat.layer_common import BooleanOperation
from sketchformat.layer_group import ShapeGroup

BOOLEAN_OPERATIONS = {
    "UNION": BooleanOperation.UNION,
    "INTERSECT": BooleanOperation.INTERSECT,
    "SUBTRACT": BooleanOperation.SUBTRACT,
    "XOR": BooleanOperation.DIFFERENCE,
}


def convert(fig_bool_ops):
    return ShapeGroup(
        **base.base_styled(fig_bool_ops),
    )


def post_process(fig_bool_ops, sketch_bool_ops):
    op = BOOLEAN_OPERATIONS[fig_bool_ops["booleanOperation"]]
    for l in sketch_bool_ops.layers:
        l.booleanOperation = op

    return sketch_bool_ops
