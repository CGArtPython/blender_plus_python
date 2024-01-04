"""
This script is used to render color palettes in Blender. It loads color palettes from a JSON file, selects a random color palette, and updates the colors of materials and nodes in the Blender scene based on the selected palette. The scene is then rendered and saved as a PNG image.

The script contains several helper functions for tasks such as setting the random seed, converting hex color strings to RGBA values, selecting random color palettes, choosing random colors from a palette, and updating colors in the scene.

To use the script, simply run it. By default, it will render all the color palettes loaded from the JSON file. You can also specify a specific color palette index and random seed to render a single palette.

Note: This script assumes that the JSON file containing the color palettes is located at the path specified in the `load_color_palettes` function.
"""

import json
import math
import pathlib
import random
import time

import bpy

################################################################
# helper functions BEGIN
################################################################


def time_seed():
    """
    Sets the random seed based on the time
    and copies the seed into the clipboard

    Returns:
    - seed (int): The random seed based on the current time.
    """
    seed = int(time.time())
    print(f"seed: {seed}")
    random.seed(seed)

    # add the seed value to your clipboard
    bpy.context.window_manager.clipboard = str(seed)

    return seed


def hex_color_str_to_rgba(hex_color: str):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB with an Alpha of 1.0

    Args:
    - hex_color (str): The hex color string in the format "#RRGGBB" or "RRGGBB"

    Returns:
    - rgba_color (tuple): The Linear RGB color with an Alpha of 1.0
    """
    # remove the leading '#' symbol if present
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]

    assert len(hex_color) == 6, "RRGGBB is the supported hex color format"

    # extracting the Red color component - RRxxxx
    red = int(hex_color[:2], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_red = red / 255
    linear_red = convert_srgb_to_linear_rgb(srgb_red)

    # extracting the Green color component - xxGGxx
    green = int(hex_color[2:4], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_green = green / 255
    linear_green = convert_srgb_to_linear_rgb(srgb_green)

    # extracting the Blue color component - xxxxBB
    blue = int(hex_color[4:6], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_blue = blue / 255
    linear_blue = convert_srgb_to_linear_rgb(srgb_blue)

    alpha = 1.0
    return tuple([linear_red, linear_green, linear_blue, alpha])


def convert_srgb_to_linear_rgb(srgb_color_component):
    """
    Converting from sRGB to Linear RGB
    based on https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ

    Args:
    - srgb_color_component (float): The sRGB color component value

    Returns:
    - linear_color_component (float): The linear RGB color component value
    """
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)

    return linear_color_component


def select_random_color_palette(context):
    """
    Selects a random color palette from the available color palettes.

    Args:
    - context (dict): The context containing the available color palettes.

    Returns:
    - random_palette (list): The randomly selected color palette.
    """
    random_palette = random.choice(context["color_palettes"])
    print(f"Random palette: {random_palette}")
    return random_palette


def choose_random_color(palette, exclude_colors=None):
    """
    Chooses a random color from the given palette, excluding the specified colors if provided.

    Args:
    - palette (list): The color palette to choose from.
    - exclude_colors (list, optional): The colors to exclude from the selection.

    Returns:
    - color (str): The randomly selected color.
    """
    if not exclude_colors:
        return random.choice(palette)

    while True:
        color = random.choice(palette)
        if color not in exclude_colors:
            return color


################################################################
# helper functions END
################################################################


def load_color_palettes():
    """
    Loads the color palettes from a JSON file.

    Returns:
    - color_palettes (list): The list of color palettes loaded from the JSON file.
    """
    # https://github.com/CGArtPython/get_color_palettes_py/blob/main/palettes/1000_five_color_palettes.json
    path = pathlib.Path.home() / "tmp" / "1000_five_color_palettes.json"
    with open(path, "r") as color_palette:
        color_palettes = json.loads(color_palette.read())

    return color_palettes


def setup_scene(palette_index, seed=0):
    """
    Sets up the scene for rendering with the specified palette index and seed.

    Args:
    - palette_index (int): The index of the color palette to use.
    - seed (float, optional): The random seed to use. If not provided, a new seed will be generated based on the current time.
    """
    if seed:
        random.seed(seed)
    else:
        seed = time_seed()

    project_name = "applying_1k_color_palettes"

    render_dir_path = pathlib.Path.home() / project_name / f"palette_{palette_index}_seed_{seed}.png"
    render_dir_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = str(render_dir_path)


def prepare_and_render_scene(palette, palette_index, seed=None):
    """
    Prepares and renders the scene with the specified palette and index.

    Args:
    - palette (list): The color palette to use for updating the colors.
    - palette_index (int): The index of the color palette.
    - seed (float, optional): The random seed to use. If not provided, a new seed will be generated based on the current time.
    """
    setup_scene(palette_index, seed)
    update_colors(palette)
    bpy.ops.render.render(write_still=True)


def render_all_palettes(palettes):
    """
    Renders all the color palettes.

    Args:
        palettes (list): A list of color palettes to be rendered.
    """
    # make sure we are using the EEVEE render engine for faster rendering
    bpy.context.scene.render.engine = "BLENDER_EEVEE"

    start_time = time.time()
    for palette_index, palette in enumerate(palettes):
        prepare_and_render_scene(palette, palette_index)

        # remove the following line to render all the palettes
        break

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")


def update_colors(palette):
    """
    Updates the colors of the materials and nodes in the Blender scene based on the given palette.

    Args:
    - palette (list): The color palette to use for updating the colors.
    """
    random.shuffle(palette)

    palette = [hex_color_str_to_rgba(hex_color) for hex_color in palette]

    # YOUR CODE HERE


def main():
    """
    The main entry point of the script.
    """
    palettes = load_color_palettes()

    palette_index = None
    seed = None

    if palette_index is not None and seed is not None:
        bpy.context.scene.render.engine = "CYCLES"
        selected_palette = palettes[palette_index]
        prepare_and_render_scene(selected_palette, palette_index, seed)
        return

    render_all_palettes(palettes)


if __name__ == "__main__":
    main()
