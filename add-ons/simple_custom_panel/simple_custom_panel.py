"""
See YouTube tutorial here: https://youtu.be/Qyy_6N3JV3k
"""

bl_info = {
    "name": "My Custom Panel",
    "author": "Victor Stepanov",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar > My Custom Panel category",
    "description": "My custom operator buttons",
    "category": "Development",
}

# give Python access to Blender's functionality
import bpy


class VIEW3D_PT_my_custom_panel(bpy.types.Panel):  # class naming convention ‘CATEGORY_PT_name’

    # where to add the panel in the UI
    bl_space_type = "VIEW_3D"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

    bl_category = "My Custom Panel category"  # found in the Sidebar
    bl_label = "My Custom Panel label"  # found at the top of the Panel

    def draw(self, context):
        """define the layout of the panel"""
        row = self.layout.row()
        row.operator("mesh.primitive_cube_add", text="Add Cube")
        row = self.layout.row()
        row.operator("mesh.primitive_ico_sphere_add", text="Add Ico Sphere")
        row = self.layout.row()
        row.operator("object.shade_smooth", text="Shade Smooth")


def register():
    bpy.utils.register_class(VIEW3D_PT_my_custom_panel)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_my_custom_panel)


if __name__ == "__main__":
    register()
