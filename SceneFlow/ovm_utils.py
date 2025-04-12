import bpy

class ObjectNameProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Object Name")
    selected: bpy.props.BoolProperty(name="Selected", default=False)

def register_utils():
    bpy.utils.register_class(ObjectNameProperty)
    bpy.types.Scene.object_name_list = bpy.props.CollectionProperty(type=ObjectNameProperty)
    bpy.types.Scene.active_object_name_index = bpy.props.IntProperty()
    bpy.types.Scene.object_name_input = bpy.props.StringProperty(name="Object Name")

def unregister_utils():
    bpy.utils.unregister_class(ObjectNameProperty)
    del bpy.types.Scene.object_name_list
    del bpy.types.Scene.active_object_name_index
    del bpy.types.Scene.object_name_input
