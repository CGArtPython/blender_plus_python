import pathlib

import bpy


def import_image_sequence_into_compositor(image_folder_path):
    pass


def main():
    """
    Python code to import a folder with png(s) into the compositor as a sequence of images.
    """
    image_folder_path = str(pathlib.Path.home() / "tmp" / "my_project")
    import_image_sequence_into_compositor(image_folder_path)


if __name__ == "__main__":
    main()
