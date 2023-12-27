import bpy

from .util import read_property


class MaterialGroupProps(bpy.types.PropertyGroup):
    is_folding: bpy.props.BoolProperty(default=False)
    name: bpy.props.StringProperty(
        name="Name",
        description=read_property("material_group_name", "description"),
        default="",
    )
    material_name: bpy.props.StringProperty(
        name="Material Name",
        description=read_property("material_group_material_name", "description"),
        default="",
    )
    texture_name: bpy.props.StringProperty(
        name="Texuture Name",
        description=read_property("material_group_texture_name", "description"),
        default="",
    )
    regex: bpy.props.StringProperty(
        name="RegExp",
        description=read_property("material_group_regex", "description"),
        default="",
    )


class VIEW3D_UL_MaterialGroup(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        col = layout.column()

        row = col.row()
        row.prop(
            item,
            "is_folding",
            icon="TRIA_RIGHT" if item.is_folding else "TRIA_DOWN",
            icon_only=True,
        )

        if item.is_folding:
            layout.label(text=item.name)
        else:
            box = layout.box()
            for prop_name, label in (
                ("name", read_property("material_group_name", "name")),
                (
                    "material_name",
                    read_property("material_group_material_name", "name"),
                ),
                ("texture_name", read_property("material_group_texture_name", "name")),
                ("regex", read_property("material_group_regex", "name")),
            ):
                box.prop(item, prop_name, text=label)


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
