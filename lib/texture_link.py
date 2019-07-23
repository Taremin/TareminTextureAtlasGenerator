import bpy


class TextureLinkProps(bpy.types.PropertyGroup):
    def get_ref_type(scene, context):
        settings = context.scene.taremin_tag

        texture_groups = [
            (str(i), group.name, "")
            for i, group in enumerate(settings.texture_groups)
        ]
        return texture_groups

    ref_type: bpy.props.EnumProperty(items=get_ref_type)
    ref_source: bpy.props.PointerProperty(type=bpy.types.Image)
    ref_link: bpy.props.PointerProperty(type=bpy.types.Image)


class VIEW3D_UL_TextureLink(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        col = layout.column()
        col.ui_units_x = 1.0
        col.label(text="", icon="LINKED")
        layout.prop(item, "ref_type", text="")
        layout.prop(item, "ref_source", text="")
        layout.prop(item, "ref_link", text="", icon="TRIA_LEFT")


class TextureLink_OT_Add(bpy.types.Operator):
    bl_idname = "taremin.add_texture_link"
    bl_label = "Add Entry"
    bl_description = 'hoge'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.taremin_tag
        settings.texture_links.add()
        settings.active_texture_link_index = len(settings.texture_links) - 1
        return {'FINISHED'}


class TextureLink_OT_Remove(bpy.types.Operator):
    bl_idname = "taremin.remove_texture_link"
    bl_label = "Remove Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_texture_link_index >= 0

    def execute(self, context):
        settings = context.scene.taremin_tag
        settings.texture_links.remove(settings.active_texture_link_index)
        max_index = len(settings.texture_links) - 1
        if settings.active_texture_link_index > max_index:
            settings.active_texture_link_index = max_index
        return {'FINISHED'}
