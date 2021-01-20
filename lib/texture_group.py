import bpy


class TextureGroupProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty
    color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        min=0.0,
        max=1.0,
    )


class VIEW3D_UL_TextureGroup(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text="", icon="GROUP")
        layout.prop(item, "name", text="")
        col = layout.column()
        col.ui_units_x = 1.0
        col.prop(item, "color", text="")


class TextureGroup_OT_Add(bpy.types.Operator):
    bl_idname = "taremin.add_texture_group"
    bl_label = "Add Entry"
    bl_description = 'hoge'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.taremin_tag
        settings.texture_groups.add()
        settings.active_texture_group_index = len(settings.texture_groups) - 1
        settings.texture_groups[settings.active_texture_group_index].name = "TextureGroup"
        return {'FINISHED'}


class TextureGroup_OT_Remove(bpy.types.Operator):
    bl_idname = "taremin.remove_texture_group"
    bl_label = "Remove Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_texture_group_index >= 0

    def execute(self, context):
        settings = context.scene.taremin_tag

        # テクスチャグループを削除するときにそのテクスチャグループを参照しているテクスチャリンクを削除する
        remove_index = settings.active_texture_group_index
        remove_list = []
        for i, link in enumerate(settings.texture_links):
            link_type = int(link.ref_type)
            if link_type == remove_index:
                remove_list.append(i)
            if link_type > remove_index:
                link.ref_type = str(link_type - 1)
        for i in reversed(remove_list):
            settings.texture_links.remove(i)

        settings.texture_groups.remove(settings.active_texture_group_index)
        max_index = len(settings.texture_groups) - 1
        if settings.active_texture_group_index > max_index:
            settings.active_texture_group_index = max_index
        return {'FINISHED'}


class TextureGroup_OT_Up(bpy.types.Operator):
    bl_idname = "taremin.up_texture_group"
    bl_label = "Up Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_texture_group_index > 0

    def execute(self, context):
        settings = context.scene.taremin_tag
        index = settings.active_texture_group_index
        settings.texture_groups.move(index, index - 1)
        settings.active_texture_group_index = index - 1
        return {'FINISHED'}


class TextureGroup_OT_Down(bpy.types.Operator):
    bl_idname = "taremin.down_texture_group"
    bl_label = "Down Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.taremin_tag
        max_index = len(settings.texture_groups) - 1
        return settings.active_texture_group_index < max_index

    def execute(self, context):
        settings = context.scene.taremin_tag
        index = settings.active_texture_group_index
        settings.texture_groups.move(index, index + 1)
        settings.active_texture_group_index = index + 1
        return {'FINISHED'}
