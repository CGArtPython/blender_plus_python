import os
import pathlib
import pprint

import bpy


def remove_compositor_nodes():
    bpy.context.scene.node_tree.nodes.clear()


def get_image_files(image_folder_path, image_extension=".png"):
    image_files = list()
    for file_name in os.listdir(image_folder_path):
        if file_name.endswith(image_extension):
            image_files.append(file_name)
    image_files.sort()

    pprint.pprint(image_files)

    return image_files


def add_compositor_nodes(image_sequence, duration):
    """
    Find the Compositor Nodes we need here
    https://docs.blender.org/api/current/bpy.types.CompositorNode.html#bpy.types.CompositorNode
    """
    scene = bpy.context.scene
    compositor_node_tree = scene.node_tree

    image_node = compositor_node_tree.nodes.new(type="CompositorNodeImage")
    image_node.image = image_sequence
    image_node.frame_duration = duration

    composite_node = compositor_node_tree.nodes.new(type="CompositorNodeComposite")
    composite_node.location.x = 200

    viewer_node = compositor_node_tree.nodes.new(type="CompositorNodeViewer")
    viewer_node.location.x = 200
    viewer_node.location.y = -200

    # create links
    compositor_node_tree.links.new(image_node.outputs["Image"], composite_node.inputs["Image"])
    compositor_node_tree.links.new(image_node.outputs["Image"], viewer_node.inputs["Image"])


def import_image_sequence_into_compositor(image_folder_path, fps):
    image_files = get_image_files(image_folder_path)

    file_info = list()
    for image_name in image_files:
        file_info.append({"name": image_name})

    bpy.ops.image.open(directory=image_folder_path, files=file_info)

    scene = bpy.context.scene
    scene.use_nodes = True

    remove_compositor_nodes()

    image_data_name = image_files[0]
    image_sequence = bpy.data.images[image_data_name]
    duration = len(image_files)
    add_compositor_nodes(image_sequence, duration)

    scene.frame_end = duration
    width, height = image_sequence.size
    scene.render.resolution_y = height
    scene.render.resolution_x = width
    scene.render.fps = fps


def main():
    """
    Python code to import a folder with png(s) into the compositor as a sequence of images.
    """
    image_folder_path = str(pathlib.Path.home() / "tmp" / "my_project")
    fps = 30
    import_image_sequence_into_compositor(image_folder_path, fps)


if __name__ == "__main__":
    main()
