import zipfile
from . import document, meta, tree, user
from .context import context
from sketchformat.layer_group import Page
from sketchformat.serialize import serialize
from typing import Dict, Sequence, List, Tuple, Optional


def convert_fig_tree_to_sketch(
    fig: dict, id_map: Dict[Sequence[int], dict], output: zipfile.ZipFile
) -> None:
    fig_pages, components_page = separate_pages(fig["document"]["children"])

    # We should either bring the fonts to the same indexed_components to pass
    # them as parameter or move the indexed components to the component file
    # and store there the components, for consistency purposes
    context.init(components_page, id_map)

    # Convert all normal pages
    sketch_pages: List[Page] = convert_pages(fig_pages, output)

    sketch_document = document.convert(sketch_pages, output)
    sketch_user = user.convert(sketch_pages)
    sketch_meta = meta.convert(sketch_pages)

    write_sketch_file(sketch_document, sketch_user, sketch_meta, output)


def separate_pages(fig_pages: List[dict]) -> Tuple[List[dict], Optional[dict]]:
    components_page = None
    pages = []

    for fig_page in fig_pages:
        if "internalOnly" in fig_page and fig_page["internalOnly"]:
            components_page = fig_page
        else:
            pages.append(fig_page)

    return pages, components_page


def convert_pages(fig_pages: List[dict], output: zipfile.ZipFile) -> List[Page]:
    pages = []

    for fig_page in fig_pages:
        page = tree.convert_node(fig_page, "DOCUMENT")
        serialize(page, output.open(f"pages/{page.do_objectID}.json", "w"))
        pages.append(page)

    if context.symbols_page:
        page = context.symbols_page
        serialize(page, output.open(f"pages/{page.do_objectID}.json", "w"))
        pages.append(page)

    return pages  # type: ignore


def write_sketch_file(
    sketch_document: dict, sketch_user: dict, sketch_meta: dict, output: zipfile.ZipFile
) -> None:
    serialize(sketch_document, output.open("document.json", "w"))
    serialize(sketch_user, output.open("user.json", "w"))
    serialize(sketch_meta, output.open("meta.json", "w"))
