import bpy

from . import atlas, texture_group, texture_link, texture_scale


# TODO: Class name
class AtlasPanelProps(bpy.types.PropertyGroup):
    output_texture_name: bpy.props.StringProperty(name="Output Texture Name", default="AtlasTexture")
    output_uvmap_name: bpy.props.StringProperty(name="Output UVMap Name", default="AtlasUVMap")

    texture_groups: bpy.props.CollectionProperty(type=texture_group.TextureGroupProps)
    active_texture_group_index: bpy.props.IntProperty(name="Active Index", default=-1)

    texture_links: bpy.props.CollectionProperty(type=texture_link.TextureLinkProps)
    active_texture_link_index: bpy.props.IntProperty(name="Active Index", default=-1)

    texture_scales: bpy.props.CollectionProperty(type=texture_scale.TextureScaleProps)
    active_texture_scale_index: bpy.props.IntProperty(name="Active Index", default=-1)

    remove_uvmaps: bpy.props.BoolProperty(name="Remove UVMaps except atlas")
    replace_face_material: bpy.props.BoolProperty(name="Replace face material with texture atlas")
    remove_material_slots: bpy.props.BoolProperty(name="Remove material slots except active")
    replace_active_material_nodetree: bpy.props.BoolProperty(name="Replace node tree texture with texture atlas")


class VIEW3D_PT_AtlasPanel(bpy.types.Panel):
    bl_label = 'Texture Atlas Generator'
    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = 'Tools'

    def check_link_size(self, context):
        settings = context.scene.taremin_tag

        errors = []
        for link in settings.texture_links:
            if link.ref_source is None or link.ref_link is None:
                continue
            if link.ref_source.size[0] != link.ref_link.size[0] or link.ref_source.size[1] != link.ref_link.size[1]:
                errors.append(link)

        if len(errors) > 0:
            return errors
        else:
            return None

    def draw(self, context):
        settings = context.scene.taremin_tag
        layout = self.layout

        row = layout.row()
        row.label(text="Output texture name:")
        row = layout.row()
        row.prop(settings, "output_texture_name", text="")

        row = layout.row()
        row.label(text="Output UVMap name:")
        row = layout.row()
        row.prop(settings, "output_uvmap_name", text="")

        layout.separator()

        row = layout.row()
        row.label(text="Texture Group:")

        # Texture Group
        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureGroup",
            "test2",  # TODO
            settings,
            "texture_groups",
            settings,
            "active_texture_group_index",
            type="DEFAULT"
        )
        col = row.column(align=True)
        col.operator(texture_group.TextureGroup_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(texture_group.TextureGroup_OT_Remove.bl_idname, text="", icon="REMOVE")

        # Texture Link
        row = layout.row()
        row.label(text="Texture Link:")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureLink",
            "test",  # TODO
            settings,
            "texture_links",
            settings,
            "active_texture_link_index",
            type="DEFAULT"
        )
        col = row.column(align=True)
        col.operator(texture_link.TextureLink_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(texture_link.TextureLink_OT_Remove.bl_idname, text="", icon="REMOVE")

        isValidLink = self.check_link_size(context)
        if isValidLink is not None:
            box = layout.box()
            for error_link in isValidLink:
                row = box.row()
                row.label(
                    text='"{}" and "{}" sizes are different'.format(error_link.ref_source.name, error_link.ref_link.name),
                    icon='ERROR'
                )

        # Texture Scale
        row = layout.row()
        row.label(text="Texture Scale:")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureScale",
            "test3",  # TODO
            settings,
            "texture_scales",
            settings,
            "active_texture_scale_index",
            type="DEFAULT"
        )
        col = row.column(align=True)
        col.operator(texture_scale.TextureScale_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(texture_scale.TextureScale_OT_Remove.bl_idname, text="", icon="REMOVE")

        # extra settings
        row = layout.row()
        row.label(text="Extra settings:")
        row = layout.row()
        row.prop(settings, "remove_uvmaps", text="Remove all UVMaps except atlas")
        row = layout.row()
        row.prop(settings, "replace_face_material", text="Replace face material with texture atlas")
        row = layout.row()
        row.prop(settings, "remove_material_slots", text="Remove material slots except active")
        if settings.remove_material_slots:
            row = layout.row()
            row.prop(settings, "replace_active_material_nodetree", text="Replace active material nodetree with texture atlas")

        layout.separator()

        # generate atlas texture
        row = layout.row()
        row.operator(atlas.OBJECT_OT_Atlas.bl_idname, text="Generate Texture")
