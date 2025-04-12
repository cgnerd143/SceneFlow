import bpy

class SampleDebugOperator(bpy.types.Operator):
    bl_idname = "object.sample_debug_operator"
    bl_label = "Print Selected Object Names"

    def execute(self, context):
        self.report({'INFO'}, "Logging selected objects to system console.")
        for item in context.scene.object_name_list:
            if item.selected:
                print(f"[SELECTED] {item.name}")
        return {'FINISHED'}

def register_ops():
    bpy.utils.register_class(SampleDebugOperator)

def unregister_ops():
    bpy.utils.unregister_class(SampleDebugOperator)
