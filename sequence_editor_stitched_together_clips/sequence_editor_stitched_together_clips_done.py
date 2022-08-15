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


def trim_the_video(clip_start_offset_frame, clip_frame_count):
    # trim the start of the clip
    bpy.context.active_sequence_strip.frame_offset_start = clip_start_offset_frame

    # trim the end of the clip
    bpy.context.active_sequence_strip.frame_final_duration = clip_frame_count


def move_the_clip_into_position(start_frame_pos, clip_start_offset_frame):
    bpy.context.active_sequence_strip.frame_start = start_frame_pos - clip_start_offset_frame


def apply_fade_in_to_clip(clip_transition_overlap):
    # make sure the clips overlap
    bpy.context.active_sequence_strip.frame_start -= clip_transition_overlap

    bpy.ops.sequencer.fades_add(type="IN")


def create_transition_between_videos(video_folder_path, fps, clip_length_sec, video_names, clip_middle_offset):

    sequence_editor = find_sequence_editor()

    sequence_editor_context = {
        "area": sequence_editor,
    }
    clean_sequencer(sequence_editor_context)
    clean_proxies(video_folder_path)

    clip_frame_count = clip_length_sec * fps

    start_frame_pos = 0
    clip_transition_overlap = 1 * fps
    for file_name in os.listdir(video_folder_path):
        if not file_name in video_names:
            continue

        video_name = file_name

        # create a full path to the video
        video_path = os.path.join(video_folder_path, video_name)
        print(f"Processing video {video_path}")

        # add video to the sequence editor
        bpy.ops.sequencer.movie_strip_add(
            sequence_editor_context,
            filepath=video_path,
            directory=video_folder_path + os.sep,
            sound=False,
        )

        # get the middle of the clip
        mid_frame = int(bpy.context.active_sequence_strip.frame_final_duration / 2)

        # apply custom offset
        if clip_middle_offset.get(video_name):
            mid_frame += clip_middle_offset.get(video_name)

        clip_start_offset_frame = mid_frame - clip_frame_count

        trim_the_video(clip_start_offset_frame, clip_frame_count)

        move_the_clip_into_position(start_frame_pos, clip_start_offset_frame)

        # if this is not the first clip in the sequence, add a "fade in" transition
        if start_frame_pos != 0:
            apply_fade_in_to_clip(clip_transition_overlap)

        # update the starting position for the next clip
        start_frame_pos = bpy.context.active_sequence_strip.frame_final_end

    # Set the final frame
    bpy.context.scene.frame_end = bpy.context.active_sequence_strip.frame_final_end

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

    create_transition_between_videos(video_folder_path, fps, clip_length_sec, video_names, clip_middle_offset)


if __name__ == "__main__":
    main()
