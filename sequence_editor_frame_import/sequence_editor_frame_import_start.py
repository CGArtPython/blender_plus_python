from datetime import datetime
import os
import pprint

import bpy


def gen_video_from_images(image_folder_path, fps):
    pass


def main():
    """
    Python code to generate a mp4 video for a folder with png(s)
    """
    image_folder_path = "C:\\tmp\\day334_3"

    # uncomment the next two lines when running on macOS or Linux
    # user_folder = os.path.expanduser("~")
    # image_folder_path = f"{user_folder}/tmp/my_rendered_frames"

    fps = 30
    gen_video_from_images(image_folder_path, fps)


if __name__ == "__main__":
    main()
