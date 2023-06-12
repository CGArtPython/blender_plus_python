"""
This code is based on a built-in Blender Python Tempalte - "UI Pie Menu"
"""

bl_info = {
    "name": "Pie Menu: Template",
    "description": "Pie menu example",
    "author": "Viktor Stepanov",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}

import bpy
from bpy.types import Menu

# spawn an edit mode selection pie (run while object is in edit mode to get a valid output)


class VIEW3D_MT_PIE_template(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Mode"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # operator_enum will just spread all available options
        # for the type enum of the operator on the pie
        pie.operator_enum("mesh.select_mode", "type")


global_addon_keymaps = []


def register():
    bpy.utils.register_class(VIEW3D_MT_PIE_template)

    window_manager = bpy.context.window_manager
    if window_manager.keyconfigs.addon:
        keymap = window_manager.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")

        keymap_item = keymap.keymap_items.new("wm.call_menu_pie", "A", "PRESS", ctrl=True, alt=True)
        keymap_item.properties.name = "VIEW3D_MT_PIE_template"

        # save the key map to deregister later
        global_addon_keymaps.append((keymap, keymap_item))


def unregister():
    bpy.utils.unregister_class(VIEW3D_MT_PIE_template)

    window_manager = bpy.context.window_manager
    if window_manager and window_manager.keyconfigs and window_manager.keyconfigs.addon:
        for keymap, keymap_item in global_addon_keymaps:
            keymap.keymap_items.remove(keymap_item)

    global_addon_keymaps.clear()


if __name__ == "__main__":
    register()

    # bpy.ops.wm.call_menu_pie(name="VIEW3D_MT_PIE_template")
