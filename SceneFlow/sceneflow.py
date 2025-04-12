# sceneflow.py (v1.0)

import bpy
# import json # No longer using json string for state
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

# --- Property Groups ---

class SceneFlow_VisibilityStateItem(bpy.types.PropertyGroup):
    """Stores visibility state for one object for Isolate/Restore."""
    name: StringProperty()
    hidden: BoolProperty()
    hide_render: BoolProperty()
    hide_viewport: BoolProperty()

class ObjectNameProperty(bpy.types.PropertyGroup):
    """An item in the main SceneFlow list."""
    name: StringProperty(name="Object Name")


# --- Preferences ---

def get_addon_preferences():
    preferences = bpy.context.preferences
    addon_name = __name__.split(".")[0]
    return preferences.addons[addon_name].preferences if addon_name in preferences.addons else None

class SceneFlowAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    enable_auto_export: BoolProperty(
        name="Enable Auto Export",
        default=False,
        description="Automatically export object names to the last used file path whenever the list changes"
    )
    last_export_path: StringProperty(
        name="Last Export Path",
        description="Stores the file path used for the last export",
        default="",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_auto_export")
        layout.prop(self, "last_export_path")

# --- Utility Functions ---

def auto_export_list_names(context):
    prefs = get_addon_preferences()
    # ...(Same as version 1.3)...
    if not prefs or not prefs.enable_auto_export: return
    path = prefs.last_export_path
    if not path: return
    try:
        names = [item.name for item in context.scene.ovm_object_name_list]
        with open(path, 'w', encoding='utf-8') as file: file.write("\n".join(names))
    except Exception as e: print(f"SceneFlow Auto-export failed: {e}")


def get_object_visibility(obj):
    return {
        'name': obj.name, 'hidden': obj.hide_get(),
        'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport
    }

def set_object_visibility(obj_name, state_dict):
    obj = bpy.data.objects.get(obj_name)
    if obj:
        obj.hide_set(state_dict.get('hidden', False))
        obj.hide_render = state_dict.get('hide_render', False)
        obj.hide_viewport = state_dict.get('hide_viewport', False)
        return True
    return False

def store_visibility_state(context, state_prop_name):
    state_collection = getattr(context.scene, state_prop_name)
    state_collection.clear()
    for obj in bpy.data.objects:
        item = state_collection.add()
        vis_state = get_object_visibility(obj)
        item.name = vis_state['name']
        item.hidden = vis_state['hidden']
        item.hide_render = vis_state['hide_render']
        item.hide_viewport = vis_state['hide_viewport']

def restore_visibility_state(context, state_prop_name):
    state_collection = getattr(context.scene, state_prop_name)
    if not state_collection: return False
    objects_in_state = {item.name for item in state_collection}
    count = 0
    for item in state_collection:
        state_dict = { 'hidden': item.hidden, 'hide_render': item.hide_render, 'hide_viewport': item.hide_viewport }
        if set_object_visibility(item.name, state_dict): count += 1
    # Make objects created after isolation visible
    for obj in bpy.data.objects:
        if obj.name not in objects_in_state:
            set_object_visibility(obj.name, {'hidden': False, 'hide_render': False, 'hide_viewport': False})
    state_collection.clear()
    return True


# --- UI List ---

class OBJECT_UL_ovm_object_name_list(bpy.types.UIList): # Renamed class
    bl_idname = "OBJECT_UL_ovm_object_name_list" # Explicitly set bl_idname

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # --- FIX: Reverted to simple label to fix display and errors ---
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Just display the name - more robust, fixes errors
            layout.label(text=item.name if item.name else "...", icon='OBJECT_DATAMODE') # Show '...' if name is empty
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


# --- Operators ---

# List Item Management (+/- buttons near list)
class AddBlankListItemOperator(bpy.types.Operator):
    bl_idname = "object.ovm_add_blank_item"
    # ...(Same as version 1.3)...
    bl_label = "Add Empty Item to List"; bl_description = "Add a new empty slot to the object name list"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        item = context.scene.ovm_object_name_list.add(); item.name = "";
        context.scene.ovm_active_object_name_index = len(context.scene.ovm_object_name_list) - 1
        auto_export_list_names(context); return {'FINISHED'}

class RemoveActiveListItemOperator(bpy.types.Operator):
    bl_idname = "object.ovm_remove_active_item"
    # ...(Same as version 1.3)...
    bl_label = "Remove Selected Item from List"; bl_description = "Remove the currently selected item from the object name list"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): idx = context.scene.ovm_active_object_name_index; return 0 <= idx < len(context.scene.ovm_object_name_list)
    def execute(self, context):
        idx = context.scene.ovm_active_object_name_index
        if 0 <= idx < len(context.scene.ovm_object_name_list):
            context.scene.ovm_object_name_list.remove(idx)
            current_len = len(context.scene.ovm_object_name_list)
            context.scene.ovm_active_object_name_index = min(idx, max(0, current_len - 1)) if current_len > 0 else -1
            auto_export_list_names(context); return {'FINISHED'}
        else: self.report({'WARNING'}, "No item selected in the list to remove"); return {'CANCELLED'}


# Selecting/Deselecting based on List
class SelectObjectsInListOperator(bpy.types.Operator):
    bl_idname = "object.ovm_select_list"
    # ...(Same as version 1.3)...
    bl_label = "Select Objects in List"; bl_description = "Select objects in the viewport if their name is in this list"; bl_options = {'REGISTER', 'UNDO'}
    clear_selection: BoolProperty(name="Clear Existing Selection", description="Deselect everything else first", default=True)
    def execute(self, context):
        if not context.scene.ovm_object_name_list: self.report({'INFO'}, "The list is empty."); return {'CANCELLED'}
        if self.clear_selection:
             if context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
             bpy.ops.object.select_all(action='DESELECT')
        count = 0; list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
        for obj in context.view_layer.objects:
             if obj.name in list_names: obj.select_set(True); count += 1
        if count > 0: context.view_layer.objects.active = next((obj for obj in context.selected_objects), None); self.report({'INFO'}, f"Selected {count} objects found in the list.")
        else: self.report({'INFO'}, "No objects in the scene match the names in the list.")
        return {'FINISHED'}

class DeselectObjectsInListOperator(bpy.types.Operator):
    bl_idname = "object.ovm_deselect_list"
    # ...(Same as version 1.3)...
    bl_label = "Deselect Objects in List"; bl_description = "Deselect objects in the viewport if their name is in this list"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        if not context.scene.ovm_object_name_list: return {'CANCELLED'}
        count = 0; list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
        for obj in context.selected_objects: # Only check selected
            if obj.name in list_names: obj.select_set(False); count += 1
        if count > 0: context.view_layer.objects.active = next((obj for obj in context.selected_objects), None); self.report({'INFO'}, f"Deselected {count} objects found in the list.")
        else: self.report({'INFO'}, "No selected objects matched the names in the list.")
        return {'FINISHED'}


# Isolate / Restore Operators
class IsolateRestoreListOperator(bpy.types.Operator):
    bl_idname = "object.ovm_isolate_restore_list"
    # ...(Same as version 1.3)...
    bl_label = "Isolate List / Restore View"; bl_description = "Isolate objects named in the list, or restore previous visibility"; bl_options = {'REGISTER'}
    state_prop_name = "ovm_isolate_list_state"; other_state_prop_name = "ovm_isolate_selection_state"
    @classmethod
    def poll(cls, context): return len(context.scene.ovm_object_name_list) > 0 or len(getattr(context.scene, cls.state_prop_name)) > 0
    def execute(self, context):
        scene = context.scene; state_collection = getattr(scene, self.state_prop_name)
        if state_collection: # Restore
            if restore_visibility_state(context, self.state_prop_name): self.report({'INFO'}, "Restored previous object visibility.")
            else: self.report({'WARNING'}, "Failed to restore state (was not isolated?).")
            return {'FINISHED'}
        else: # Isolate
            if not scene.ovm_object_name_list: self.report({'WARNING'}, "List is empty, cannot isolate."); return {'CANCELLED'}
            restore_visibility_state(context, self.other_state_prop_name) # Clear other mode
            store_visibility_state(context, self.state_prop_name)
            list_names = {item.name for item in scene.ovm_object_name_list if item.name}
            hidden_count = 0; shown_count = 0
            for obj in bpy.data.objects:
                if obj.name in list_names: obj.hide_set(False); shown_count += 1
                else:
                    if not obj.hide_get(): obj.hide_set(True); hidden_count += 1
            self.report({'INFO'}, f"List Isolated: {shown_count} shown, {hidden_count} newly hidden.")
            return {'FINISHED'}

class IsolateRestoreSelectedOperator(bpy.types.Operator):
    bl_idname = "object.ovm_isolate_restore_selected"
    # ...(Same as version 1.3)...
    bl_label = "Isolate Selected / Restore View"; bl_description = "Isolate selected objects, or restore previous visibility"; bl_options = {'REGISTER'}
    state_prop_name = "ovm_isolate_selection_state"; other_state_prop_name = "ovm_isolate_list_state"
    @classmethod
    def poll(cls, context): return len(context.selected_objects) > 0 or len(getattr(context.scene, cls.state_prop_name)) > 0
    def execute(self, context):
        scene = context.scene; state_collection = getattr(scene, self.state_prop_name)
        if state_collection: # Restore
            if restore_visibility_state(context, self.state_prop_name): self.report({'INFO'}, "Restored previous object visibility.")
            else: self.report({'WARNING'}, "Failed to restore state (was not isolated?).")
            return {'FINISHED'}
        else: # Isolate
            if not context.selected_objects: self.report({'WARNING'}, "No objects selected, cannot isolate."); return {'CANCELLED'}
            restore_visibility_state(context, self.other_state_prop_name) # Clear other mode
            store_visibility_state(context, self.state_prop_name)
            selected_names_before = {o.name for o in context.selected_objects}
            bpy.ops.object.hide_view_set(unselected=True)
            bpy.ops.object.select_all(action='DESELECT') # Reselect original selection
            shown_count = 0
            for obj_name in selected_names_before:
                 obj = bpy.data.objects.get(obj_name)
                 if obj and not obj.hide_get(): obj.select_set(True); shown_count += 1
            context.view_layer.objects.active = next((obj for obj in context.selected_objects), None)
            self.report({'INFO'}, f"Selection Isolated: {shown_count} objects remain visible.")
            return {'FINISHED'}


# Unhide All Operator
class UnhideAllObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_unhide_all"
    # ...(Same as version 1.3)...
    bl_label = "Unhide All Objects"; bl_description = "Unhide all objects in the viewport (Equivalent to Alt+H)"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return any(obj.hide_get() or obj.hide_viewport for obj in context.view_layer.objects)
    def execute(self, context):
        # Using Blender's built-in operator is best
        bpy.ops.object.hide_view_clear(select=False) # Pass select=False to mimic Alt+H exactly
        self.report({'INFO'}, "Unhid all objects (used Alt+H operator).")
        return {'FINISHED'}

# --- Standard Add/Remove Operators (Restored) ---
class AddSelectedToListOperator(bpy.types.Operator):
    bl_idname = "object.ovm_add_selected"
    # ...(Same as version 1.3)...
    bl_label = "Add Selected to List"; bl_description = "Add currently selected objects to the list"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        count = 0; current_names = {item.name for item in context.scene.ovm_object_name_list}
        for obj in context.selected_objects:
            if obj.name not in current_names:
                item = context.scene.ovm_object_name_list.add(); item.name = obj.name; count += 1
        if count > 0: auto_export_list_names(context); self.report({'INFO'}, f"Added {count} selected objects to list.")
        else: self.report({'INFO'}, "No new objects added (already in list or none selected).")
        return {'FINISHED'}

class RemoveSelectedFromListOperator(bpy.types.Operator):
    bl_idname = "object.ovm_remove_selected"
    # ...(Same as version 1.3)...
    bl_label = "Remove Selected from List"; bl_description = "Remove currently selected objects from the list"; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        selected_names = {obj.name for obj in context.selected_objects}
        indices_to_remove = [i for i, item in enumerate(context.scene.ovm_object_name_list) if item.name in selected_names]
        if not indices_to_remove: self.report({'INFO'}, "No selected objects found in the list."); return {'CANCELLED'}
        count = 0
        for i in reversed(indices_to_remove): context.scene.ovm_object_name_list.remove(i); count += 1
        if count > 0:
            current_len = len(context.scene.ovm_object_name_list)
            context.scene.ovm_active_object_name_index = min(context.scene.ovm_active_object_name_index, max(0, current_len - 1)) if current_len > 0 else -1
            auto_export_list_names(context); self.report({'INFO'}, f"Removed {count} objects from list based on selection.")
        return {'FINISHED'}


# --- Other List/Manual Operators ---
class AddManualNameOperator(bpy.types.Operator):
    bl_idname = "object.ovm_add_manual"
    # ...(Same as version 1.3)...
    bl_label = "Add Name"; bl_description = "Add the name entered below to the list"; bl_options = {'REGISTER', 'UNDO'}
    name_to_add: StringProperty(name="Object Name")
    def invoke(self, context, event): self.name_to_add = context.scene.ovm_object_name_input; return self.execute(context)
    def execute(self, context):
        name = self.name_to_add.strip();
        if not name: self.report({'WARNING'}, "Cannot add empty name."); return {'CANCELLED'}
        current_names = {item.name for item in context.scene.ovm_object_name_list}
        if name in current_names: self.report({'INFO'}, f"Name '{name}' is already in the list."); return {'CANCELLED'}
        item = context.scene.ovm_object_name_list.add(); item.name = name
        context.scene.ovm_active_object_name_index = len(context.scene.ovm_object_name_list) - 1
        context.scene.ovm_object_name_input = ""; auto_export_list_names(context); self.report({'INFO'}, f"Added '{name}' to list.")
        return {'FINISHED'}

class RemoveManualNameOperator(bpy.types.Operator):
    bl_idname = "object.ovm_remove_manual"
    # ...(Same as version 1.3)...
    bl_label = "Remove Name"; bl_description = "Remove the name entered below from the list"; bl_options = {'REGISTER', 'UNDO'}
    name_to_remove: StringProperty(name="Object Name")
    def invoke(self, context, event): self.name_to_remove = context.scene.ovm_object_name_input; return self.execute(context)
    def execute(self, context):
        name = self.name_to_remove.strip();
        if not name: self.report({'WARNING'}, "Cannot remove empty name."); return {'CANCELLED'}
        found_index = -1
        for i, item in enumerate(context.scene.ovm_object_name_list):
            if item.name == name: found_index = i; break
        if found_index != -1:
            context.scene.ovm_object_name_list.remove(found_index)
            current_len = len(context.scene.ovm_object_name_list)
            context.scene.ovm_active_object_name_index = min(context.scene.ovm_active_object_name_index, max(0, current_len - 1)) if current_len > 0 else -1
            context.scene.ovm_object_name_input = ""; auto_export_list_names(context); self.report({'INFO'}, f"Removed '{name}' from list.")
            return {'FINISHED'}
        else: self.report({'INFO'}, f"Name '{name}' not found in the list."); return {'CANCELLED'}

class RemoveAllNamesOperator(bpy.types.Operator):
    bl_idname = "object.ovm_clear_list"
    # ...(Same as version 1.3)...
    bl_label = "Clear List"; bl_description = "Remove all names from the list"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return len(context.scene.ovm_object_name_list) > 0
    def execute(self, context):
        if not context.scene.ovm_object_name_list: return {'CANCELLED'}
        count = len(context.scene.ovm_object_name_list); context.scene.ovm_object_name_list.clear();
        context.scene.ovm_active_object_name_index = -1; auto_export_list_names(context); self.report({'INFO'}, f"Cleared {count} names from the list.")
        return {'FINISHED'}

class ImportNamesFromFileOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "object.ovm_import_names"
    # ...(Same as version 1.3)...
    bl_label = "Import Names from .txt"; bl_description = "Add names from a text file (one name per line)"; bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(default="*.txt", options={'HIDDEN'}); filename_ext = ".txt"
    def execute(self, context):
        count = 0; current_names = {item.name for item in context.scene.ovm_object_name_list}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name and name not in current_names:
                        item = context.scene.ovm_object_name_list.add(); item.name = name; current_names.add(name); count += 1
            if count > 0: auto_export_list_names(context); self.report({'INFO'}, f"Imported {count} new names from {self.filepath}")
            else: self.report({'INFO'}, "No new names imported (empty file or names already exist).")
        except Exception as e: self.report({'ERROR'}, f"Import failed: {e}"); return {'CANCELLED'}
        return {'FINISHED'}

class ExportNamesToFileOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "object.ovm_export_names"
    # ...(Same as version 1.3)...
    bl_label = "Export Names to .txt"; bl_description = "Save the names currently in the list to a text file"; bl_options = {'PRESET'}
    filename_ext = ".txt"; filter_glob: StringProperty(default="*.txt", options={'HIDDEN'}); filepath: StringProperty(subtype="FILE_PATH")
    def execute(self, context):
        prefs = get_addon_preferences()
        if not self.filepath: self.report({'ERROR'}, "No file path specified."); return {'CANCELLED'}
        if not self.filepath.lower().endswith(".txt"): self.filepath += ".txt"
        try:
            count = len(context.scene.ovm_object_name_list)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for item in context.scene.ovm_object_name_list: f.write(item.name + "\n")
            if prefs: prefs.last_export_path = self.filepath
            self.report({'INFO'}, f"Exported {count} names to {self.filepath}")
        except Exception as e: self.report({'ERROR'}, f"Export failed: {e}"); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self, context, event):
        prefs = get_addon_preferences()
        if prefs and prefs.last_export_path: self.filepath = prefs.last_export_path
        else: self.filepath = "object_list.txt"
        context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}


class HideListObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_hide_list"
    # ...(Same as version 1.3)...
    bl_label = "Hide Objects in List"; bl_description = "Hide objects in the viewport if their name is in the list"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return len(context.scene.ovm_object_name_list) > 0
    def execute(self, context):
        count = 0; list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
        for obj in context.view_layer.objects:
             if obj.name in list_names and not obj.hide_get(): obj.hide_set(True); count += 1
        self.report({'INFO'}, f"Hid {count} objects found in the list.")
        return {'FINISHED'}

class UnhideListObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_unhide_list"
    # ...(Same as version 1.3)...
    bl_label = "Unhide Objects in List"; bl_description = "Unhide objects in the viewport if their name is in the list"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
         if not context.scene.ovm_object_name_list: return False
         list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
         return any(obj.name in list_names and obj.hide_get() for obj in context.view_layer.objects)
    def execute(self, context):
        count = 0; list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
        for obj in context.view_layer.objects:
             if obj.name in list_names and obj.hide_get(): obj.hide_set(False); count += 1
        self.report({'INFO'}, f"Unhid {count} objects found in the list.")
        return {'FINISHED'}

class DeleteListObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_delete_list"
    # ...(Same as version 1.3)...
    bl_label = "Delete Objects in List"; bl_description = "Delete objects from the scene if their name is in the list (Use with caution!)"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
         if not context.scene.ovm_object_name_list: return False
         list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
         return any(obj.name in list_names for obj in bpy.data.objects)
    def execute(self, context):
        objects_to_delete = []; list_names = {item.name for item in context.scene.ovm_object_name_list if item.name}
        for obj in bpy.data.objects:
            if obj.name in list_names: objects_to_delete.append(obj)
        if not objects_to_delete: self.report({'INFO'}, "No objects from the list found in the scene."); return {'CANCELLED'}
        count = len(objects_to_delete); deleted_names = {obj.name for obj in objects_to_delete}
        if context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT');
        for obj in objects_to_delete: obj.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)
        indices_to_remove = [i for i, item in enumerate(context.scene.ovm_object_name_list) if item.name in deleted_names]
        if indices_to_remove:
            for i in reversed(indices_to_remove): context.scene.ovm_object_name_list.remove(i)
            current_len = len(context.scene.ovm_object_name_list)
            context.scene.ovm_active_object_name_index = min(context.scene.ovm_active_object_name_index, max(0, current_len - 1)) if current_len > 0 else -1
        self.report({'INFO'}, f"Deleted {count} objects found in the list."); auto_export_list_names(context)
        return {'FINISHED'}

# === Operators: Viewport Selection ===
class HideSelectedObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_hide_selected"
    # ...(Same as version 1.3)...
    bl_label = "Hide Selected"; bl_description = "Hide selected objects in the viewport"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return context.selected_objects
    def execute(self, context):
        if not context.selected_objects: return {'CANCELLED'}
        bpy.ops.object.hide_view_set(unselected=False) # Use built-in
        self.report({'INFO'}, f"Hid {len(context.selected_objects)} selected objects.")
        return {'FINISHED'}

class UnhideSelectedObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_unhide_selected"
    bl_label = "Unhide Selected"
    bl_description = "Unhide selected objects in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # --- FIX: Check selected objects specifically ---
        return context.selected_objects and any(obj.hide_get() for obj in context.selected_objects)

    def execute(self, context):
        # --- FIX: Iterate explicitly to only unhide selected ---
        if not context.selected_objects: return {'CANCELLED'}
        count = 0
        for obj in context.selected_objects:
            if obj.hide_get():
                obj.hide_set(False)
                count += 1
        if count > 0:
             self.report({'INFO'}, f"Unhid {count} selected objects.")
        else:
             self.report({'INFO'}, "Selected objects were already visible.")
        return {'FINISHED'}


class DeleteSelectedObjectsOperator(bpy.types.Operator):
    bl_idname = "object.ovm_delete_selected"
    # ...(Same as version 1.3)...
    bl_label = "Delete Selected"; bl_description = "Delete selected objects from the scene (Use with caution!)"; bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return context.selected_objects
    def execute(self, context):
        if not context.selected_objects: return {'CANCELLED'}
        selected_names = {obj.name for obj in context.selected_objects}; count = len(selected_names)
        # if context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT') # Delete op handles mode
        bpy.ops.object.delete(use_global=False, confirm=False)
        indices_to_remove = [i for i, item in enumerate(context.scene.ovm_object_name_list) if item.name in selected_names]
        if indices_to_remove:
            removed_from_list_count = 0
            for i in reversed(indices_to_remove): context.scene.ovm_object_name_list.remove(i); removed_from_list_count += 1
            current_len = len(context.scene.ovm_object_name_list)
            context.scene.ovm_active_object_name_index = min(context.scene.ovm_active_object_name_index, max(0, current_len - 1)) if current_len > 0 else -1
            self.report({'INFO'}, f"Deleted {count} selected objects (removed {removed_from_list_count} from SceneFlow list)."); auto_export_list_names(context)
        else: self.report({'INFO'}, f"Deleted {count} selected objects.")
        return {'FINISHED'}

# --- Panels ---

#    def draw(self, context):
#        layout = self.layout
#       row = layout.row(align=True)
#        row.operator("wm.undo", text="Undo", icon='LOOP_BACK')
#        row.operator("wm.redo", text="Redo", icon='LOOP_FORWARDS')
        # --- FIX: Removed Unhide All from this top panel ---


class OBJECT_PT_SceneFlow_ListControls(bpy.types.Panel):
    bl_label = "SceneFlow - List Controls"
    bl_idname = "OBJECT_PT_ovm_list_controls"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = "SceneFlow"; bl_order = 1

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- List Management ---
        box_list_mgmt = layout.box()
        col_list_mgmt = box_list_mgmt.column(align=True) # Align column content
        col_list_mgmt.label(text="Manage List Entries:")

        # Manual Add/Remove Row
        row_manual = col_list_mgmt.row(align=True)
        row_manual.prop(scene, "ovm_object_name_input", text="")
        row_manual.operator(AddManualNameOperator.bl_idname, text="", icon='ADD')
        row_manual.operator(RemoveManualNameOperator.bl_idname, text="", icon='REMOVE')

        # Add/Remove from Selection Buttons (Restored)
        row_select = col_list_mgmt.row(align=True)
        row_select.operator(AddSelectedToListOperator.bl_idname, text="Add Selected", icon='PLUS')
        row_select.operator(RemoveSelectedFromListOperator.bl_idname, text="Remove Selected", icon='REMOVE')

        col_list_mgmt.separator()

        # Main List UI with +/- buttons
        row_list_ui = col_list_mgmt.row() # Don't align this row itself
        # Use the explicit bl_idname for template_list
        row_list_ui.template_list(OBJECT_UL_ovm_object_name_list.bl_idname, "", scene, "ovm_object_name_list", scene, "ovm_active_object_name_index", rows=5)
        col_list_btns = row_list_ui.column(align=True) # Align the button column
        col_list_btns.operator(AddBlankListItemOperator.bl_idname, text="", icon='ADD')
        col_list_btns.operator(RemoveActiveListItemOperator.bl_idname, text="", icon='REMOVE')
        col_list_btns.separator()
        col_list_btns.operator(RemoveAllNamesOperator.bl_idname, text="", icon='X')

        # --- List-based Selection ---
        box_list_select = layout.box()
        col_list_select = box_list_select.column(align=True)
        col_list_select.label(text="Select Scene Objects:")
        row_list_select_ops = col_list_select.row(align=True)
        row_list_select_ops.operator(SelectObjectsInListOperator.bl_idname, text="Select List Objs", icon='RESTRICT_SELECT_OFF')
        row_list_select_ops.operator(DeselectObjectsInListOperator.bl_idname, text="Deselect List Objs", icon='PANEL_CLOSE')


        # --- File Operations For Text File ---
        box_file = layout.box()
        col_file = box_file.column(align=True)
        col_file.label(text="Text File Operations:")
        row_file = col_file.row(align=True)
        row_file.operator(ImportNamesFromFileOperator.bl_idname, text="Import Text File", icon='IMPORT')
        row_file.operator(ExportNamesToFileOperator.bl_idname, text="Export Text File", icon='EXPORT')
        prefs = get_addon_preferences()
        if prefs:
           col_file.prop(prefs, "enable_auto_export") # Keep it simple

        # --- List-based Object Actions ---
        box_list_actions = layout.box()
        col_list_actions = box_list_actions.column(align=True)
        col_list_actions.label(text="List Object Actions:")
        row_list_vis = col_list_actions.row(align=True)
        row_list_vis.operator(HideListObjectsOperator.bl_idname, text="Hide", icon='HIDE_ON')
        row_list_vis.operator(UnhideListObjectsOperator.bl_idname, text="Unhide", icon='HIDE_OFF')

        row_list_iso = col_list_actions.row(align=True)
        op_list_iso = row_list_iso.operator(IsolateRestoreListOperator.bl_idname, text="Isolate / Restore", icon='SELECT_SUBTRACT')
        row_list_iso.operator(UnhideAllObjectsOperator.bl_idname, text="Unhide All", icon='RESTRICT_VIEW_OFF') # Changed icon for clarity

        col_list_actions.separator()
        col_list_actions.operator(DeleteListObjectsOperator.bl_idname, text="Delete Objects in List", icon='TRASH')


class OBJECT_PT_SceneFlow_SelectedControls(bpy.types.Panel):
    bl_label = "SceneFlow - Selected Object Controls"
    bl_idname = "OBJECT_PT_ovm_selected_controls"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = "SceneFlow"; bl_order = 2

    def draw(self, context):
        layout = self.layout
        # scene = context.scene # Not needed here currently

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Selected Object Actions:")

        row_vis = col.row(align=True)
        row_vis.operator(HideSelectedObjectsOperator.bl_idname, text="Hide", icon='HIDE_ON')
        row_vis.operator(UnhideSelectedObjectsOperator.bl_idname, text="Unhide", icon='HIDE_OFF') # Ensure this uses the fixed operator

        row_iso = col.row(align=True)
        op_sel_iso = row_iso.operator(IsolateRestoreSelectedOperator.bl_idname, text="Isolate / Restore", icon='SELECT_SUBTRACT')
        row_iso.operator(UnhideAllObjectsOperator.bl_idname, text="Unhide All", icon='RESTRICT_VIEW_OFF') # Changed icon

        col.separator()
        col.operator(DeleteSelectedObjectsOperator.bl_idname, text="Delete Selected", icon='TRASH')


class OBJECT_PT_SceneFlow_About(bpy.types.Panel):
    bl_label = "About SceneFlow"
    bl_idname = "OBJECT_PT_sceneflow_about"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SceneFlow"
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        layout.label(text="SceneFlow")
        layout.label(text="Version: 1.0 (Beta)")
        layout.operator("wm.url_open", text="GitHub Page", icon="URL").url = "https://github.com/cgnerd143"
        layout.operator("wm.url_open", text="Report Issues", icon="ERROR").url = "https://github.com/cgnerd143/SceneFlow/issues"


# --- Register ---




class OBJECT_PT_SceneFlow_ActionControls(bpy.types.Panel):
    bl_label = "SceneFlow Actions"
    bl_idname = "VIEW3D_PT_sceneflow_action_controls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SceneFlow"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.operator("object.undo_action", text="Undo", icon="LOOP_BACK")
        layout.operator("object.redo_action", text="Redo", icon="LOOP_FORWARDS")


classes = (
    SceneFlow_VisibilityStateItem,
    ObjectNameProperty,
    SceneFlowAddonPreferences,
    OBJECT_UL_ovm_object_name_list, # Use new class name

    # Operators (ensure all are included)
    AddBlankListItemOperator, RemoveActiveListItemOperator,
    SelectObjectsInListOperator, DeselectObjectsInListOperator,
    IsolateRestoreListOperator, IsolateRestoreSelectedOperator,
    UnhideAllObjectsOperator,
    AddSelectedToListOperator, # Restored
    RemoveSelectedFromListOperator, # Restored
    AddManualNameOperator, RemoveManualNameOperator,
    RemoveAllNamesOperator,
    ImportNamesFromFileOperator, ExportNamesToFileOperator,
    HideListObjectsOperator, UnhideListObjectsOperator, DeleteListObjectsOperator,
    HideSelectedObjectsOperator, UnhideSelectedObjectsOperator, DeleteSelectedObjectsOperator,

    # Panels
    OBJECT_PT_SceneFlow_ActionControls, OBJECT_PT_SceneFlow_ListControls,
    OBJECT_PT_SceneFlow_SelectedControls, OBJECT_PT_SceneFlow_About,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene properties (using ovm_ prefix)
    bpy.types.Scene.ovm_object_name_list = CollectionProperty(type=ObjectNameProperty)
    bpy.types.Scene.ovm_active_object_name_index = IntProperty(name="Active SceneFlow Name Index", default=-1, min=-1)
    bpy.types.Scene.ovm_object_name_input = StringProperty(name="Manual Object Name", description="Name to add/remove manually")
    bpy.types.Scene.ovm_isolate_list_state = CollectionProperty(type=SceneFlow_VisibilityStateItem)
    bpy.types.Scene.ovm_isolate_selection_state = CollectionProperty(type=SceneFlow_VisibilityStateItem)
    print("SceneFlow Addon Registered (v1.4)")


def unregister():
    # Delete scene properties first (use correct names)
    prop_names = [
        "ovm_object_name_list", "ovm_active_object_name_index", "ovm_object_name_input",
        "ovm_isolate_list_state", "ovm_isolate_selection_state"
    ]
    for prop_name in prop_names:
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)

    for cls in reversed(classes):
         try: bpy.utils.unregister_class(cls)
         except RuntimeError: print(f"SceneFlow: Could not unregister class {cls.__name__}")
    print("SceneFlow Addon Unregistered (v1.4)")


if __name__ == "__main__":
    try: unregister()
    except Exception as e: print(f"SceneFlow Dev: Unregister failed (likely first run): {e}")
    register()