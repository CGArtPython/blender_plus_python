from datetime import datetime
import os
import pprint

import bpy


def clean_sequencer(sequence_context):
    bpy.ops.sequencer.select_all(sequence_context, action="SELECT")
    bpy.ops.sequencer.delete(sequence_context)


def find_sequence_editor():
    for area in bpy.context.window.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            return area
    return None


def get_image_files(image_folder_path, image_extention=".png"):
    image_files = list()
    for file_name in os.listdir(image_folder_path):
        if file_name.endswith(image_extention):
            image_files.append(file_name)
    image_files.sort()

    pprint.pprint(image_files)

    return image_files


def get_image_dimensions(image_path):
    image = bpy.data.images.load(image_path)
    width, height = image.size
    return width, height


def set_up_output_params(image_folder_path, image_files, fps):
    frame_count = len(image_files)

    scene = bpy.context.scene

    scene.frame_end = frame_count

    image_path = os.path.join(image_folder_path, image_files[0])

    width, height = get_image_dimensions(image_path)

    scene.render.resolution_y = height
    scene.render.resolution_x = width

    scene.render.fps = fps
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"

    now = datetime.now()
    time = now.strftime("%H-%M-%S")
    filepath = os.path.join(image_folder_path, f"anim_{time}.mp4")
    scene.render.filepath = filepath


def gen_video_from_images(image_folder_path, fps):

    image_files = get_image_files(image_folder_path)

    set_up_output_params(image_folder_path, image_files, fps)

    sequence_editor = find_sequence_editor()

    sequence_editor_context = {
        "area": sequence_editor,
    }
    clean_sequencer(sequence_editor_context)

    file_info = list()
    for image_name in image_files:
        file_info.append({"name": image_name})

    bpy.ops.sequencer.image_strip_add(
        sequence_editor_context,
        directory=image_folder_path + os.sep,
        files=file_info,
        frame_start=1,
    )

    bpy.ops.render.render(animation=True)


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
