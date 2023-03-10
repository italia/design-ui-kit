#!/usr/bin/env python3

import argparse
import json
import logging
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import ssl
import sys
from typing import List

try:
    from importlib.metadata import version

    VERSION = version("fig2sketch")
except:
    VERSION = "unknown version"


def parse_args(args: List[str] = sys.argv[1:]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Converts a .fig document to .sketch")
    parser.add_argument("fig_file")
    parser.add_argument("sketch_file")

    group = parser.add_argument_group("conversion options")
    group.add_argument(
        "--instance-override",
        choices=["detach", "ignore"],
        default="detach",
        help="what to do when converting unsupported instance override (default = detach)",
    )
    group.add_argument(
        "--force-convert-images",
        action="store_true",
        help="try to convert corrupted images",
    )
    group.add_argument(
        "--compress",
        action="store_true",
        help="compress the output sketch file",
    )

    group = parser.add_argument_group("debug options")
    group.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="return more details, can be repeated",
    )
    group.add_argument("--salt", type=str, help="salt used to generate ids, defaults to random")
    group.add_argument(
        "--dump-fig-json",
        type=argparse.FileType("w"),
        help="output a fig representation in json for debugging purposes",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    return parser.parse_args(args)


def run(args: argparse.Namespace) -> None:
    # Set default log level
    level = logging.WARNING
    if args.verbosity:
        level = logging.INFO if args.verbosity == 1 else logging.DEBUG

    logging.basicConfig(level=level)

    # Import these after setting the log level
    from figformat import fig2tree
    from converter import convert
    from converter.config import config

    config.version = VERSION
    if args.salt:
        config.salt = args.salt.encode("utf8")

    if args.force_convert_images:
        from PIL import ImageFile

        ImageFile.LOAD_TRUNCATED_IMAGES = True

    config.can_detach = args.instance_override == "detach"

    # Load SSL certificates in OSs where Python does not use system defaults
    if not ssl.create_default_context().get_ca_certs():
        import certifi
        import os

        os.environ["SSL_CERT_FILE"] = certifi.where()
        logging.debug("Loaded TLS certificates from certifi")
    else:
        logging.debug("Using system TLS certificates")

    logging.debug(config)
    logging.debug(f"Version {VERSION}")

    compression = ZIP_STORED
    if args.compress:
        compression = ZIP_DEFLATED

    with ZipFile(args.sketch_file, "w", compression=compression) as output:
        fig_tree, id_map = fig2tree.convert_fig(args.fig_file, output)

        if args.dump_fig_json:
            json.dump(
                fig_tree,
                args.dump_fig_json,
                indent=2,
                ensure_ascii=False,
                default=lambda x: x.tolist(),
            )

        convert.convert_fig_tree_to_sketch(fig_tree, id_map, output)


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
