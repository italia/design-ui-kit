from . import base
from sketchformat.layer_common import Slice


def convert(fig_slice):
    return Slice(
        **base.base_layer(fig_slice),
    )
