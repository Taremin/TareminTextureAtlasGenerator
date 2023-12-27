import bpy

from . import atlas, material_group, texture_group, texture_link, texture_scale, util
from .util import read_property, read_panel


# TODO: Class name
class AtlasPanelProps(bpy.types.PropertyGroup):
    output_texture_name: bpy.props.StringProperty(
        name=read_property("output_texture_name", "name"), default="AtlasTexture"
    )
    output_uvmap_name: bpy.props.StringProperty(
        name=read_property("output_uvmap_name", "name"), default="AtlasUVMap"
    )
    output_material_name: bpy.props.StringProperty(
        name=read_property("output_material_name", "name"), default="AtlasMaterial"
    )

    material_groups: bpy.props.CollectionProperty(
        type=material_group.MaterialGroupProps
    )
    active_material_group_index: bpy.props.IntProperty(
        name=read_property("active_material_group_index", "name"), default=-1
    )

    texture_groups: bpy.props.CollectionProperty(type=texture_group.TextureGroupProps)
    active_texture_group_index: bpy.props.IntProperty(
        name=read_property("active_texture_group_index", "name"), default=-1
    )

    texture_links: bpy.props.CollectionProperty(type=texture_link.TextureLinkProps)
    active_texture_link_index: bpy.props.IntProperty(
        name=read_property("active_texture_link_index", "name"), default=-1
    )

    texture_scales: bpy.props.CollectionProperty(type=texture_scale.TextureScaleProps)
    active_texture_scale_index: bpy.props.IntProperty(
        name=read_property("active_texture_scale_index", "name"), default=-1
    )

    remove_uvmaps: bpy.props.BoolProperty(name=read_property("remove_uvmaps", "name"))
    replace_face_material: bpy.props.BoolProperty(
        name=read_property("replace_face_material", "name")
    )
    remove_material_slots: bpy.props.BoolProperty(
        name=read_property("remove_material_slots", "name")
    )

    is_auto_save: bpy.props.BoolProperty(
        name=read_property("is_auto_save", "name"), default=False
    )
    output_directory: bpy.props.StringProperty(
        name=read_property("output_directory", "name"), default="//", subtype="DIR_PATH"
    )


class TAREMIN_TEXTURE_ATLAS_GENERATOR_PT_Panel(bpy.types.Panel):
    bl_label = "Taremin Texture Atlas Generator"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "Taremin"

    def check_link_size(self, context):
        settings = context.scene.taremin_tag

        errors = []
        for link in settings.texture_links:
            if link.ref_source is None or link.ref_link is None:
                continue
            if (
                link.ref_source.size[0] != link.ref_link.size[0]
                or link.ref_source.size[1] != link.ref_link.size[1]
            ):
                errors.append(link)

        if len(errors) > 0:
            return errors
        else:
            return None

    def draw(self, context):
        settings = context.scene.taremin_tag
        layout = self.layout

        row = layout.row()
        row.label(text=read_panel("output_texture_name", "label") + ":")
        row = layout.row()
        row.prop(settings, "output_texture_name", text="")

        row = layout.row()
        row.label(text=read_panel("output_uvmap_name", "label") + ":")
        row = layout.row()
        row.prop(settings, "output_uvmap_name", text="")

        row = layout.row()
        row.label(text=read_panel("output_material_name", "label") + ":")
        row = layout.row()
        row.prop(settings, "output_material_name", text="")

        layout.separator()

        # Material Group
        row = layout.row()
        row.label(text=read_panel("material_group", "label") + ":")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_MaterialGroup",
            "",
            settings,
            "material_groups",
            settings,
            "active_material_group_index",
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(material_group.MaterialGroup_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(
            material_group.MaterialGroup_OT_Remove.bl_idname, text="", icon="REMOVE"
        )
        col.separator()
        col.operator(
            material_group.MaterialGroup_OT_Up.bl_idname, text="", icon="TRIA_UP"
        )
        col.operator(
            material_group.MaterialGroup_OT_Down.bl_idname, text="", icon="TRIA_DOWN"
        )

        # Texture Group
        row = layout.row()
        row.label(text=read_panel("texture_group", "label") + ":")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureGroup",
            "",
            settings,
            "texture_groups",
            settings,
            "active_texture_group_index",
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(texture_group.TextureGroup_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(
            texture_group.TextureGroup_OT_Remove.bl_idname, text="", icon="REMOVE"
        )
        col.separator()
        col.operator(
            texture_group.TextureGroup_OT_Up.bl_idname, text="", icon="TRIA_UP"
        )
        col.operator(
            texture_group.TextureGroup_OT_Down.bl_idname, text="", icon="TRIA_DOWN"
        )

        # Texture Link
        row = layout.row()
        row.label(text=read_panel("texture_link", "label") + ":")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureLink",
            "",
            settings,
            "texture_links",
            settings,
            "active_texture_link_index",
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(texture_link.TextureLink_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(
            texture_link.TextureLink_OT_Remove.bl_idname, text="", icon="REMOVE"
        )
        col.separator()
        col.operator(texture_link.TextureLink_OT_Up.bl_idname, text="", icon="TRIA_UP")
        col.operator(
            texture_link.TextureLink_OT_Down.bl_idname, text="", icon="TRIA_DOWN"
        )

        # テクスチャリンクのサイズが一致するかチェック
        isValidLink = self.check_link_size(context)
        if isValidLink is not None:
            box = layout.box()
            for error_link in isValidLink:
                row = box.row()
                row.label(
                    text='"{}" and "{}" sizes are different'.format(
                        error_link.ref_source.name, error_link.ref_link.name
                    ),
                    icon="ERROR",
                )

        # Texture Scale
        row = layout.row()
        row.label(text=read_panel("texture_scale", "label") + ":")

        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_TextureScale",
            "",
            settings,
            "texture_scales",
            settings,
            "active_texture_scale_index",
            type="DEFAULT",
        )
        col = row.column(align=True)
        col.operator(texture_scale.TextureScale_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(
            texture_scale.TextureScale_OT_Remove.bl_idname, text="", icon="REMOVE"
        )
        col.separator()
        col.operator(
            texture_scale.TextureScale_OT_Up.bl_idname, text="", icon="TRIA_UP"
        )
        col.operator(
            texture_scale.TextureScale_OT_Down.bl_idname, text="", icon="TRIA_DOWN"
        )

        # extra settings
        row = layout.row()
        row.label(text=read_panel("extra_settings", "label") + ":")

        row = layout.row()
        row.prop(settings, "remove_uvmaps", text=read_property("remove_uvmaps", "name"))

        row = layout.row()
        row.prop(
            settings,
            "replace_face_material",
            text=read_property("replace_face_material", "name"),
        )

        row = layout.row()
        row.prop(
            settings,
            "remove_material_slots",
            text=read_property("remove_material_slots", "name"),
        )

        row = layout.row()
        row.prop(settings, "is_auto_save", text=read_property("is_auto_save", "name"))
        if settings.is_auto_save:
            box = layout.box()
            row = box.row()
            row.prop(
                settings,
                "output_directory",
                text=read_property("output_directory", "name"),
            )

        layout.separator()

        # generate atlas texture
        row = layout.row()
        is_uvmap_limit, uvmap_limit_objs = util.is_uvmap_upper_limit(context)
        if is_uvmap_limit:
            col = row.column()
            col.label(text="limit")
            row = layout.row()

        row.operator(
            atlas.TAREMIN_TEXTURE_ATLAS_GENERATOR_OT_Atlas.bl_idname,
            text=read_panel("generate_texture", "label"),
        )
