import datetime
import os
import shutil

import bpy


def clean_sequencer(sequence_context):
    bpy.ops.sequencer.select_all(sequence_context, action="SELECT")
    bpy.ops.sequencer.delete(sequence_context)


def find_sequence_editor():
    for area in bpy.context.window.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            return area
    return None


def set_up_output_params(folder_path):
    scene = bpy.context.scene

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"

    now = datetime.datetime.now()
    time = now.strftime("%H-%M-%S")
    filepath = os.path.join(folder_path, f"stitched_together_{time}.mp4")
    scene.render.filepath = filepath


def clean_proxies(video_folder_path):
    """
    This will delete the BL_proxies folder
    """

    def on_error(function, path, excinfo):
        print(f"Failed to remove {path}\n{excinfo}")

    bl_proxy_path = os.path.join(video_folder_path, "BL_proxy")
    if os.path.exists(bl_proxy_path):
        print(f"Removing the BL_proxies folder in {bl_proxy_path}")
        shutil.rmtree(bl_proxy_path, ignore_errors=False, onerror=on_error)


def create_transition_between_videos(video_folder_path):

    sequence_editor = find_sequence_editor()

    sequence_editor_context = {
        "area": sequence_editor,
    }
    clean_sequencer(sequence_editor_context)
    clean_proxies(video_folder_path)

    # TODO: add code here

    # Render the clip sequence
    # bpy.ops.render.render(animation=True)


def main():
    """
    Python code to create short clips from videos and stich them back to back
    with a transition
    """

    video_folder_path = r"C:\tmp\my_videos"

    # uncomment the next two lines when running on macOS or Linux
    # user_folder = os.path.expanduser("~")
    # video_folder_path = f"{user_folder}/tmp/my_videos"

    set_up_output_params(video_folder_path)

    video_names = [
        "video_01.mp4",
        "video_02.mp4",
        "video_03.mp4",
        "video_04.mp4",
    ]

    fps = 30
    clip_middle_offset = {
        "video_01.mp4": 8 * fps,
        "video_03.mp4": 4 * fps,
    }

    # The length of the clips in seconds
    clip_length_sec = 4

    create_transition_between_videos(video_folder_path)


if __name__ == "__main__":
    main()
