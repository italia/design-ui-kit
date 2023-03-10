import io
import zipfile
from . import kiwi
from converter.positioning import Matrix
import logging


def decode(path):
    type_converters = {
        "GUID": lambda x: (x["sessionID"], x["localID"]),
        "Matrix": lambda m: Matrix(
            [[m["m00"], m["m01"], m["m02"]], [m["m10"], m["m11"], m["m12"]], [0, 0, 1]]
        ),
    }

    # Open file and check if it's a zip
    fig_zip = None
    reader = open(path, "rb")
    header = reader.read(2)
    reader.seek(0)
    if header == b"PK":
        fig_zip = zipfile.ZipFile(reader)

    try:
        import fig_kiwi

        logging.debug("Using fast (rust) kiwi reader")
        return fig_kiwi.decode(path, type_converters), fig_zip

    except ImportError:
        logging.debug("Falling back to slow (python) kiwi reader")

    if fig_zip:
        reader = fig_zip.open("canvas.fig")

    return kiwi.decode(reader, type_converters), fig_zip
