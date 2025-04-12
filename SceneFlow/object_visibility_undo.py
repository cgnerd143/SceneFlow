import bpy

class UndoActionOperator(bpy.types.Operator):
    bl_idname = "object.undo_action"
    bl_label = "Undo Action"

    @classmethod
    def poll(cls, context):
        return bpy.ops.ed.undo.poll()

    def execute(self, context):
        bpy.ops.ed.undo()
        return {'FINISHED'}

class RedoActionOperator(bpy.types.Operator):
    bl_idname = "object.redo_action"
    bl_label = "Redo Action"

    @classmethod
    def poll(cls, context):
        return bpy.ops.ed.redo.poll()

    def execute(self, context):
        bpy.ops.ed.redo()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(UndoActionOperator)
    bpy.utils.register_class(RedoActionOperator)

def unregister():
    bpy.utils.unregister_class(UndoActionOperator)
    bpy.utils.unregister_class(RedoActionOperator)
