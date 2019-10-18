import bpy


class TextureScaleProps(bpy.types.PropertyGroup):
    texture: bpy.props.PointerProperty(type=bpy.types.Image)
    scale: bpy.props.FloatProperty(min=0.0)


class VIEW3D_UL_TextureScale(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "texture", text="")
        col = layout.column()
        col.prop(item, "scale", text="")


class TextureScale_OT_Add(bpy.types.Operator):
    bl_idname = "taremin.add_texture_scale"
    bl_label = "Add Entry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.taremin_tag
        settings.texture_scales.add()
        settings.active_texture_scale_index = len(settings.texture_scales) - 1
        settings.texture_scales[settings.active_texture_scale_index].name = "TextureScale"
        return {'FINISHED'}


class TextureScale_OT_Remove(bpy.types.Operator):
    bl_idname = "taremin.remove_texture_scale"
    bl_label = "Remove Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.taremin_tag.active_texture_scale_index >= 0

    def execute(self, context):
        settings = context.scene.taremin_tag

        settings.texture_scales.remove(settings.active_texture_scale_index)
        max_index = len(settings.texture_scales) - 1
        if settings.active_texture_scale_index > max_index:
            settings.active_texture_scale_index = max_index
        return {'FINISHED'}
