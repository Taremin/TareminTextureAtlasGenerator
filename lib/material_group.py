import bpy


class MaterialGroupProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    regex: bpy.props.StringProperty(name="RegExp", default="")


class VIEW3D_UL_MaterialGroup(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text="", icon="MATERIAL")
        row = layout.row()
        col = row.column()
        col.prop(item, "name", text="")
        col = row.column()
        col.prop(item, "regex", text="")


class MaterialGroup_OT_Add(bpy.types.Operator):
    bl_idname = "taremin.add_material_group"
    bl_label = "Add Entry"
    bl_description = "hoge"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.taremin_tag
        settings.material_groups.add()
        settings.active_material_group_index = len(settings.material_groups) - 1
        print("addd")
        return {"FINISHED"}


class MaterialGroup_OT_Remove(bpy.types.Operator):
    bl_idname = "taremin.remove_material_group"
    bl_label = "Remove Entry"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_material_group_index >= 0

    def execute(self, context):
        settings = context.scene.taremin_tag

        settings.material_groups.remove(settings.active_material_group_index)
        max_index = len(settings.material_groups) - 1
        if settings.active_material_group_index > max_index:
            settings.active_material_group_index = max_index
        return {"FINISHED"}


class MaterialGroup_OT_Up(bpy.types.Operator):
    bl_idname = "taremin.up_material_group"
    bl_label = "Up Entry"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_material_group_index > 0

    def execute(self, context):
        settings = context.scene.taremin_tag
        index = settings.active_material_group_index
        settings.material_groups.move(index, index - 1)
        settings.active_material_group_index = index - 1
        return {"FINISHED"}


class MaterialGroup_OT_Down(bpy.types.Operator):
    bl_idname = "taremin.down_material_group"
    bl_label = "Down Entry"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.taremin_tag
        max_index = len(settings.material_groups) - 1
        return settings.active_material_group_index < max_index

    def execute(self, context):
        settings = context.scene.taremin_tag
        index = settings.active_material_group_index
        settings.material_groups.move(index, index + 1)
        settings.active_material_group_index = index + 1
        return {"FINISHED"}
