import bpy

class DebugUtilityPanel(bpy.types.Panel):
    bl_label = "Debug Utilities"
    bl_idname = "VIEW3D_PT_debug_utilities"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Visibility"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("object.sample_debug_operator", text="Print Selected", icon="CONSOLE")
