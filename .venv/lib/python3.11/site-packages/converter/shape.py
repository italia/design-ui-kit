from . import base
from sketchformat.layer_shape import Polygon, Oval, Star


def convert_polygon(fig_polygon):
    return Polygon(**base.base_shape(fig_polygon), numberOfPoints=fig_polygon["count"])


def convert_oval(fig_ellipse):
    return Oval(**base.base_shape(fig_ellipse))


def convert_star(fig_star):
    return Star(
        **base.base_shape(fig_star),
        numberOfPoints=fig_star["count"],
        radius=fig_star["starInnerScale"],
    )
