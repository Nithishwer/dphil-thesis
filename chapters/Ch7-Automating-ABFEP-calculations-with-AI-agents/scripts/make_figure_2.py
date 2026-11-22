#!/usr/bin/env python3
"""Combine the four Figure 2 SVGs, labelled A–D from left to right.

Panels A–D correspond to Tasks 33, 38, 47, and 48.

Run with Python, Pillow, and the Inkscape command-line program:
    python make_figure_2.py

Fits each SVG page to its artwork and regenerates its matching PNG. Writes
figure_2.svg with editable text, figure_2.png (600 dpi), and figure_2.pdf.
All PNG exports have an opaque white background.
"""

import copy
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_2"
OUTPUT_STEM = HERE / "figure_2"
PANEL_PATHS = (
    HERE / "a-RBFE/a-RBFE.svg",
    HERE / "b-QMMM/b-QMMM.svg",
    HERE / "c-pAsp/c-pAsp.svg",
    HERE / "d-AlchMetad/d-AlchemMetad.svg",
)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NAMESPACE)
ET.register_namespace("xlink", XLINK_NAMESPACE)
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")

# Match the panel-label font and size in Figures 1, 3, and 4.
FONT_FAMILY = "DejaVu Sans"
LABEL_SIZE = 14
LABEL_GAP_POINTS = 12
FIGURE_WIDTH = 14.0
PANEL_GAP = 0.28  # Inches between images.
MARGIN = 0.12  # Inches around the combined figure.
DPI = 600
PANEL_DPI = 300
PNG_BACKGROUND = ("--export-background=#ffffff", "--export-background-opacity=1")


def inkscape(*arguments: str) -> str:
    result = subprocess.run(
        ["inkscape", *arguments], check=True, capture_output=True, text=True
    )
    return result.stdout


def write_svg(root: ET.Element, path: Path) -> None:
    document = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    path.write_bytes(
        b"\n".join(line.rstrip(b" \t") for line in document.splitlines()) + b"\n"
    )


def load_panel(path: Path) -> tuple[ET.Element, tuple[float, float, float, float]]:
    """Export the SVG page and use its PNG to locate the visible artwork."""
    root = ET.parse(path).getroot()
    # With xml:space="preserve", XML indentation becomes unwanted label spacing.
    for text in root.iter(f"{{{SVG_NAMESPACE}}}text"):
        for node in text.iter():
            for attribute in ("text", "tail"):
                value = getattr(node, attribute)
                if value and ("\n" in value or "\r" in value):
                    setattr(
                        node,
                        attribute,
                        "".join(line.strip(" \t") for line in value.splitlines()),
                    )
    write_svg(root, path)
    view_x, view_y, view_width, _ = map(float, root.attrib["viewBox"].split())
    pixels_per_unit = float(root.attrib["width"].removesuffix("in")) * 96 / view_width
    drawing = next(
        line.split(",")[1:]
        for line in inkscape(str(path), "--query-all").splitlines()
        if line.split(",")[0] == root.attrib["id"]
    )
    x, y, width, height = map(float, drawing)

    # A fitted SVG page and a page-area PNG include exactly the same artwork.
    view_x += x / pixels_per_unit
    view_y += y / pixels_per_unit
    view_width = width / pixels_per_unit
    view_height = height / pixels_per_unit
    root.set("viewBox", f"{view_x} {view_y} {view_width} {view_height}")
    root.set("width", f"{width / 96}in")
    root.set("height", f"{height / 96}in")
    write_svg(root, path)
    png_path = path.with_suffix(".png")
    inkscape(
        str(path),
        "--export-area-page",
        f"--export-dpi={PANEL_DPI}",
        f"--export-filename={png_path}",
    )
    with Image.open(png_path) as image:
        bounds = image.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"Panel is fully transparent: {path}")
        left, top, right, bottom = bounds
        crop = (
            view_x + left / image.width * view_width,
            view_y + top / image.height * view_height,
            (right - left) / image.width * view_width,
            (bottom - top) / image.height * view_height,
        )
        # Measure transparency before adding white so the layout stays the same.
        white_image = Image.new("RGB", image.size, "white")
        white_image.paste(image, mask=image.getchannel("A"))
        white_image.save(png_path, dpi=(PANEL_DPI, PANEL_DPI))
    print(f"Updated {path} and {png_path}", flush=True)
    return root, crop


def prefix_ids(root: ET.Element, prefix: str) -> None:
    """Keep clip paths and other references distinct between the four SVGs."""
    identifiers = {
        node.attrib["id"]: f"{prefix}_{node.attrib['id']}"
        for node in root.iter()
        if "id" in node.attrib
    }
    for node in root.iter():
        if "id" in node.attrib:
            node.set("id", identifiers[node.attrib["id"]])
        for name, value in list(node.attrib.items()):
            if value.startswith("data:"):
                continue
            value = re.sub(
                r"url\(#([^)]+)\)",
                lambda match: f"url(#{identifiers[match[1]]})",
                value,
            )
            if name.endswith("href") and value.startswith("#"):
                value = "#" + identifiers[value[1:]]
            node.set(name, value)


def main() -> None:
    panels = [load_panel(path) for path in PANEL_PATHS]
    aspect_ratios = [crop[2] / crop[3] for _, crop in panels]

    # Lay out in points so 14-unit SVG text is physically 14-point text.
    image_width = FIGURE_WIDTH - 2 * MARGIN - (len(panels) - 1) * PANEL_GAP
    image_height = image_width / sum(aspect_ratios)
    label_space = (LABEL_SIZE + LABEL_GAP_POINTS) / 72
    figure_height = image_height + label_space + 2 * MARGIN
    image_top = (MARGIN + label_space) * 72
    figure = ET.Element(
        f"{{{SVG_NAMESPACE}}}svg",
        {
            "id": "figure_2",
            "width": f"{FIGURE_WIDTH}in",
            "height": f"{figure_height}in",
            "viewBox": f"0 0 {FIGURE_WIDTH * 72} {figure_height * 72}",
            "version": "1.1",
        },
    )

    left = MARGIN
    for letter, (source, crop), aspect in zip(
        "ABCD", panels, aspect_ratios, strict=True
    ):
        panel_width = image_height * aspect
        panel = copy.deepcopy(source)
        prefix_ids(panel, f"panel_{letter}")
        panel.set("x", str(left * 72))
        panel.set("y", str(image_top))
        panel.set("width", str(panel_width * 72))
        panel.set("height", str(image_height * 72))
        panel.set("viewBox", " ".join(map(str, crop)))
        panel.set("overflow", "hidden")
        figure.append(panel)
        label = ET.SubElement(
            figure,
            f"{{{SVG_NAMESPACE}}}text",
            {
                "id": f"label_{letter}",
                "x": str(left * 72),
                "y": str(image_top - LABEL_GAP_POINTS),
                "font-family": FONT_FAMILY,
                "font-size": str(LABEL_SIZE),
                "font-weight": "bold",
                "fill": "black",
            },
        )
        label.text = letter
        left += panel_width + PANEL_GAP

    svg_path = OUTPUT_STEM.with_suffix(".svg")
    write_svg(figure, svg_path)
    print(f"Saved {svg_path}", flush=True)
    # Both exports come from the assembled SVG to keep every format consistent.
    for extension in ("png", "pdf"):
        output = OUTPUT_STEM.with_suffix(f".{extension}")
        inkscape(
            str(svg_path),
            "--export-area-page",
            f"--export-dpi={DPI}",
            f"--export-filename={output}",
            *(PNG_BACKGROUND if extension == "png" else ()),
        )
        print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
