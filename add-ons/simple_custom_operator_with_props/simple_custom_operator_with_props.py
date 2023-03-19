"""
See YouTube tutorial here: https://youtu.be/0_QskeU8CPo
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


def add_subdiv_monkey_obj(size, subdiv_viewport_levels, subdiv_render_levels, shade_smooth):
    bpy.ops.mesh.primitive_monkey_add(size=size)

    bpy.ops.object.modifier_add(type="SUBSURF")
    bpy.context.object.modifiers["Subdivision"].levels = subdiv_viewport_levels
    bpy.context.object.modifiers["Subdivision"].render_levels = subdiv_render_levels

    if shade_smooth:
        bpy.ops.object.shade_smooth()


class MESH_OT_add_subdiv_monkey(bpy.types.Operator):
    """Create a new monkey mesh object with a subdivision surf modifier and shaded smooth"""

    bl_idname = "mesh.add_subdiv_monkey"
    bl_label = "Add Subdivided Monkey Mesh Object"
    bl_options = {"REGISTER", "UNDO"}

    mesh_size: bpy.props.FloatProperty(
        name="Size",
        default=4.0,
        description="The size of the monkey",
    )

    subdiv_viewport_lvl: bpy.props.IntProperty(
        name="Subdiv Viewport",
        default=1,
        min=1,
        max=3,
        description="The Subdivision Levels applied in the Viewport",
    )

    subdiv_render_lvl: bpy.props.IntProperty(
        name="Subdiv Render",
        default=3,
        min=3,
        max=7,
        description="The Subdivision Levels applied during the Viewport",
    )

    shade_smooth: bpy.props.BoolProperty(
        name="Shade Smooth",
        default=True,
        description="Apply Smooth Shading to the mesh",
    )

    def execute(self, context):

        add_subdiv_monkey_obj(self.mesh_size, self.subdiv_viewport_lvl, self.subdiv_render_lvl, self.shade_smooth)

        return {"FINISHED"}


class VIEW3D_PT_my_custom_panel(bpy.types.Panel):  # class naming convention ‘CATEGORY_PT_name’

    # where to add the panel in the UI
    bl_space_type = "VIEW_3D"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

    # add labels
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

        self.layout.separator()

        row = self.layout.row()
        row.operator("mesh.add_subdiv_monkey", text="Add Subdivided Monkey")


# register the panel with Blender
def register():
    bpy.utils.register_class(VIEW3D_PT_my_custom_panel)
    bpy.utils.register_class(MESH_OT_add_subdiv_monkey)


def unregister():
    bpy.utils.unregister_class(MESH_OT_add_subdiv_monkey)
    bpy.utils.unregister_class(VIEW3D_PT_my_custom_panel)


if __name__ == "__main__":
    register()
