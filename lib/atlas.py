from enum import Enum

import bmesh
import bpy
import numpy
import os
import re

from . import blf_solver, walk_shader_node, util
from .logging_settings import get_logger

logger = get_logger(name=__name__)


def get_active_object():
    return bpy.context.window.view_layer.objects.active


def set_active_object(obj):
    bpy.context.window.view_layer.objects.active = obj


class TAREMIN_TEXTURE_ATLAS_GENERATOR_OT_Atlas(bpy.types.Operator):
    bl_idname = "taremin.atlas"
    bl_label = "Generate Texture Atlas"
    bl_description = "generate texture atlas"
    bl_options = {"REGISTER", "UNDO"}

    class NodesType(Enum):
        ALL = 0
        WALK = 1

    @classmethod
    def poll(cls, context):
        is_uvmap_limit, uvmap_limit_objs = util.is_uvmap_upper_limit(context)
        return len(context.selected_objects) > 0 and not is_uvmap_limit

    def execute(self, context):
        settings = self.get_settings(context)

        # 選択オブジェクトのマテリアル
        target_materials = self.get_selected_objects_materials(context)

        # 複数のアトラスにマテリアルを振り分ける
        material_groups = {}
        for material in target_materials:
            matched = False

            for material_group in settings.material_groups:
                # 正規表現の入力文字列のエスケープを外す
                pattern = material_group.regex.encode().decode("unicode_escape")

                if re.search(pattern=pattern, string=material.name):
                    replaced_material_name = re.sub(
                        pattern=".*" + pattern + ".*",
                        repl=material_group.material_name,
                        string=material.name,
                    )
                    replaced_texture_name = re.sub(
                        pattern=".*" + pattern + ".*",
                        repl=material_group.texture_name,
                        string=material.name,
                    )
                    logger.debug(
                        f"Material Group: {material.name} => {replaced_material_name}"
                    )
                    if replaced_material_name not in material_groups:
                        material_groups[replaced_material_name] = (
                            [],
                            replaced_texture_name,
                        )
                    material_groups[replaced_material_name][0].append(material)
                    matched = True
                    break

            if not matched:
                if None not in material_groups:
                    material_groups[None] = ([], settings.output_texture_name)
                material_groups[None][0].append(material)

        atlas_materials = []
        atlas_uvmaps = {}
        for output_material_name, (
            materials,
            output_texture_name,
        ) in material_groups.items():
            if output_material_name is None:
                output_material_name = settings.output_material_name

            # 対象マテリアルのテクスチャノード取得
            textures = self.get_texture_nodes(context, materials)

            # scale を適用
            scale = self.create_image_to_scale_dict(context)
            scaled_textures = self.scale_texture(context, textures, scale)

            # テクスチャからUVレイヤーの紐づけ
            image_uv = self.get_image_to_uv_dict(context, textures)

            # create rects
            rects = self.get_rects_from_unique_textures(
                context, image_uv, scaled_textures
            )
            for rect in rects:
                logger.debug("rect: {}".format(rect))

            # create atlas
            image, image_point_dic, link_images = self.create_atlas(
                context, rects, scaled_textures, name=output_texture_name
            )

            # remove scaled texture
            for tex in scaled_textures:
                logger.debug(
                    "remove temporary image: {}".format(scaled_textures[tex][0])
                )
                bpy.data.images.remove(scaled_textures[tex][0])

            # 表示用マテリアルの追加
            atlas_material = util.get_asset_material(context, "AtlasMaterial")
            atlas_material.name = output_material_name
            atlas_materials.append(atlas_material)

            for obj in context.selected_objects:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bm.faces.ensure_lookup_table()

                # マテリアルごとの面を用意
                material_face = self.create_material_face_indices(context, obj, bm)

                remove_mats = []
                for mat in material_face.keys():
                    if mat not in materials:
                        remove_mats.append(mat)
                for mat in remove_mats:
                    del material_face[mat]

                # UVMapの作成
                if obj not in atlas_uvmaps:
                    new_uv = bm.loops.layers.uv.new(settings.output_uvmap_name)
                    atlas_uvmaps[obj] = new_uv.name
                else:
                    new_uv = bm.loops.layers.uv[atlas_uvmaps[obj]]
                self.update_uvmap(
                    context,
                    bm,
                    image.size,
                    image_point_dic,
                    material_face,
                    materials=materials,
                    uvmap=new_uv,
                )

                # マテリアルの追加
                index = len(obj.data.materials)
                obj.data.materials.append(atlas_material)
                obj.active_material_index = index

                # 面のマテリアル割当の差し替え
                if settings.replace_face_material:
                    for face in bm.faces:
                        if (
                            obj.material_slots[face.material_index].material
                            in material_face
                        ):
                            face.material_index = index

                uvmap_name = new_uv.name
                bm.to_mesh(obj.data)
                obj.data.update()
                bm.free()

            # マテリアルのテクスチャノードの書き換え
            self.replace_material_texture(
                context, [atlas_material], image, settings.output_uvmap_name
            )

            if settings.is_auto_save:
                # Texture Atlas (Base)
                self.save_image(context, image)

                # Texture Atlas (Link)
                for group in link_images:
                    image, pixels = link_images[group]
                    self.save_image(context, image)

        # アクティブUVMapの変更
        for obj in context.selected_objects:
            uvmap_name = atlas_uvmaps[obj]
            obj.data.uv_layers.active = obj.data.uv_layers[uvmap_name]
            obj.data.uv_layers[uvmap_name].active_render = True

        # 余計なUVMapの削除
        if settings.remove_uvmaps:
            for obj in context.selected_objects:
                remove_list = []
                uvmap_name = atlas_uvmaps[obj]

                for uv_layer in obj.data.uv_layers:
                    if uv_layer.name != uvmap_name:
                        remove_list.append(uv_layer)
                for uv_layer in reversed(remove_list):
                    obj.data.uv_layers.remove(uv_layer)

        # アトラス以外のマテリアルスロットの削除
        if settings.remove_material_slots:
            active_object = get_active_object()

            for obj in context.selected_objects:
                set_active_object(obj)
                remove_list = reversed(
                    [
                        i
                        for i, slot in enumerate(obj.material_slots)
                        if slot.material not in atlas_materials
                    ]
                )

                for index in remove_list:
                    obj.active_material_index = index
                    bpy.ops.object.material_slot_remove()

            set_active_object(active_object)

        return {"FINISHED"}

    def save_image(self, context, image):
        settings = self.get_settings(context)
        image.filepath_raw = os.path.join(
            settings.output_directory, image.name + ".png"
        )
        image.file_format = "PNG"
        image.save()

    def get_selected_objects_materials(self, context):
        target_materials = []
        for obj in context.selected_objects:
            for material in obj.data.materials:
                if material not in target_materials:
                    target_materials.append(material)
        return target_materials

    def copy_materials(self, context, materials, suffix=".atlas"):
        base_to_copy = {}
        for material in materials:
            if material in base_to_copy:
                material = base_to_copy[material]
            else:
                copy = material.copy()
                copy.name = material.name + suffix
                base_to_copy[material] = copy
                material = copy
        return base_to_copy

    def create_image_to_scale_dict(self, context):
        settings = self.get_settings(context)
        scale_dic = {}
        for tex_scale in settings.texture_scales:
            scale_dic[tex_scale.texture] = tex_scale.scale
            logger.debug(
                "set texture scale: texture=%s, scale=%f",
                tex_scale.texture,
                tex_scale.scale,
            )
        return scale_dic

    def scale_texture(self, context, texture_nodes, scale_dic):
        scaled = {}

        for node in texture_nodes:
            tex = node.image
            logger.debug("texture node found: %s", tex)
            if tex in scale_dic:
                scale = scale_dic[tex]
                if tex in scaled:
                    logger.debug(
                        "skip: scaled texture already exists: {}".format(scaled[tex][0])
                    )
                else:
                    scaled[tex] = (
                        self.create_scaled_texture(context, tex, scale),
                        scale,
                    )
        return scaled

    def create_scaled_texture(self, context, image, scale):
        tmp = image.copy()
        tmp.name = "tmp.scaled." + image.name
        width, height = image.size
        tmp.scale(int(width * scale), int(height * scale))
        return tmp

    def get_settings(self, context):
        return context.scene.taremin_tag

    def get_texture_nodes(self, context, materials):
        textures = []
        for material in materials:
            if material.node_tree is None:
                continue

            def get_texture_image(node):
                if self.check_atlas_target(context, node):
                    textures.append(node)

            walk_shader_node.walk_tree(material.node_tree, get_texture_image)
        return textures

    def check_atlas_target(self, context, node):
        settings = self.get_settings(context)
        link_textures = [link.ref_link for link in settings.texture_links]

        return (
            isinstance(node, bpy.types.ShaderNodeTexImage)
            and node.image is not None
            and node.image not in link_textures
        )

    def get_image_to_uv_dict(self, context, textures):
        image_uv_dict = {}
        for obj in context.selected_objects:
            for tex_node in textures:
                image = tex_node.image
                layers = obj.data.uv_layers
                uv = None

                # Vector 入力がない場合はアクティブUVレンダーレイヤーになる
                if not tex_node.inputs["Vector"].links:
                    uv = layers[layers.active_index]
                else:
                    uvmap_node = tex_node.inputs["Vector"].links[0].from_node
                    if isinstance(uvmap_node, bpy.types.ShaderNodeUVMap):
                        uv = layers[uvmap_node.uv_map]
                    else:
                        logger.warn(
                            "Unsupported Node (UVMap) in {} (Texture: {})".format(
                                obj.name, image.name
                            )
                        )
                        uv = layers[layers.active_index]

                if image not in image_uv_dict:
                    image_uv_dict[image] = []
                if uv not in image_uv_dict[image]:
                    image_uv_dict[image].append(uv)
        return image_uv_dict

    def get_rects_from_unique_textures(self, context, image_to_uv_dict, scale_dic):
        return [
            (
                scale_dic[image][0].size[0],
                scale_dic[image][0].size[1],
                image,
                image_to_uv_dict[image],
            )
            if image in scale_dic
            else (image.size[0], image.size[1], image, image_to_uv_dict[image])
            for image in image_to_uv_dict.keys()
        ]

    def calc_init_size(self, rects):
        size = 1
        total = 0
        for w, h, *etc in rects:
            total += w * h
        while size * size < total:
            size <<= 1

        return size

    def create_atlas(self, context, rects, scaled_texture, name="texture"):
        settings = self.get_settings(context)
        blf = blf_solver.BLFSolver(rects)
        size, results = blf.solve(self.calc_init_size(rects))

        atlas_image = bpy.data.images.new(name=name, width=size, height=size)
        pixels = numpy.zeros((size, size, 4), "f")
        atlas_image.pixels.foreach_get(pixels.ravel())

        # texture link
        dic = {}
        used_texture_group = {}
        link_images = {}
        for link in settings.texture_links:
            ref_type = int(link.ref_type)
            texture_group = settings.texture_groups[ref_type]
            source = link.ref_source

            if texture_group not in used_texture_group:
                # create link texture
                link_texture_name = "_".join((name, texture_group.name))
                link_image = bpy.data.images.new(
                    name=link_texture_name, width=size, height=size
                )
                link_pixels = numpy.full(
                    (size, size, 4), list(texture_group.color) + [1.0]
                )

                used_texture_group[texture_group] = (link_image, link_pixels)
                link_images[link_image] = link_pixels
            else:
                link_image, link_pixels = used_texture_group[texture_group]

            # atlas image -> link image dictionary
            if source not in dic:
                dic[source] = []
            dic[source].append((link_image, link_pixels, link.ref_link))

        # atlas
        atlas_image_map = {}
        for x, y, w, h, idx, image, mesh_uv_loop_layers in results:
            if image in scaled_texture:
                scaled = scaled_texture[image][0]
                src_pixels = numpy.zeros((scaled.size[1], scaled.size[0], 4), "f")
                scaled.pixels.foreach_get(src_pixels.ravel())
            else:
                src_pixels = numpy.zeros((image.size[1], image.size[0], 4), "f")
                image.pixels.foreach_get(src_pixels.ravel())
            self.copy_rect(pixels, x, y, src_pixels, 0, 0, w, h)
            atlas_image_map[image] = (x, y, w, h)

        # copy link texture
        for image in atlas_image_map:
            x, y, w, h = atlas_image_map[image]
            if image in dic:
                for link_image, link_pixels, copy_source_image in dic[image]:
                    if image in scaled_texture:
                        tmp = self.create_scaled_texture(
                            context, copy_source_image, scaled_texture[image][1]
                        )
                        src_pixels = numpy.zeros((tmp.size[1], tmp.size[0], 4), "f")
                        tmp.pixels.foreach_get(src_pixels.ravel())
                        bpy.data.images.remove(tmp)
                    else:
                        src_pixels = numpy.zeros(
                            (copy_source_image.size[1], copy_source_image.size[0], 4),
                            "f",
                        )
                        copy_source_image.pixels.foreach_get(src_pixels.ravel())
                    self.copy_rect(link_pixels, x, y, src_pixels, 0, 0, w, h)
                    link_images[link_image] = link_pixels
        for link_image in link_images:
            link_image.pixels = link_images[link_image].ravel()

        atlas_image.pixels.foreach_set(pixels.ravel())

        return (atlas_image, atlas_image_map, used_texture_group)

    def add_clone_materials(self, context, obj, target_materials):
        add = []
        for material_slot_idx, material_slot in enumerate(obj.material_slots):
            material = material_slot.material
            if material in target_materials:
                add.append(material_slot_idx)
        return add

    def create_material_face_indices(self, context, obj, bm):
        mat_to_face = {}
        for face_idx, face in enumerate(bm.faces):
            material = obj.material_slots[face.material_index].material
            if material not in mat_to_face:
                mat_to_face[material] = []
            mat_to_face[material].append(face_idx)
        return mat_to_face

    def update_uvmap(
        self, context, bm, size, image_point_dic, material_face, materials, uvmap
    ):
        width, height = size
        for material in materials:
            if material not in material_face:
                continue

            def texture_image(node):
                if self.check_atlas_target(context, node):
                    uv_layer = None
                    if not node.inputs["Vector"].links:
                        uv_layer = bm.loops.layers.uv.active
                    else:
                        uvmap_node = node.inputs["Vector"].links[0].from_node
                        if isinstance(uvmap_node, bpy.types.ShaderNodeUVMap):
                            uv_layer = bm.loops.layers.uv[uvmap_node.uv_map]
                        else:
                            logger.warn("Unsupported Node (UVMap)")
                    if uv_layer is not None:
                        new_layer = uvmap
                        x, y, w, h = image_point_dic[node.image]
                        for face_idx in material_face[material]:
                            for loop in bm.faces[face_idx].loops:
                                u, v = loop[uv_layer].uv
                                loop[new_layer].uv = (
                                    (w * u + x) / width,
                                    (h * v + y) / height,
                                )

            if material.node_tree is None:
                continue

            walk_shader_node.walk_tree(material.node_tree, texture_image)

    def get_clone_material_idx_dict(self, context, obj, add, mat_copy_dic):
        material_idx_dict = {}

        for material_slot_idx in add:
            new_idx = len(obj.data.materials)
            material = mat_copy_dic[obj.material_slots[material_slot_idx].material]
            obj.data.materials.append(material)
            material_idx_dict[material_slot_idx] = new_idx

        return material_idx_dict

    def get_uvmap_nodes(self, context, obj, add, material_idx_dict):
        uvmap_nodes = []

        for material_slot_idx in add:
            material = obj.material_slots[material_idx_dict[material_slot_idx]].material

            def get_uvmap_nodes(node):
                if (
                    isinstance(node, bpy.types.ShaderNodeTexImage)
                    and node.image is not None
                ):
                    links = node.inputs["Vector"].links
                    if not links:
                        return
                    uvmap_node = links[0].from_node
                    if isinstance(uvmap_node, bpy.types.ShaderNodeUVMap):
                        uvmap_nodes.append(uvmap_node)

            walk_shader_node.walk_tree(material.node_tree, get_uvmap_nodes)

        return uvmap_nodes

    def replace_material_texture(self, context, target_materials, image, uvmap_name):
        def visit(node):
            texture_image(node)
            uvmap(node)

        def texture_image(node):
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                logger.debug("replace node: %s", node.image)
                node.image = image
                # walk_shader_node.walk_node(node, uvmap)

        def uvmap(node):
            if isinstance(node, bpy.types.ShaderNodeUVMap):
                node.uv_map = uvmap_name

        for material in target_materials:
            self.walk_node(self.NodesType.WALK, material.node_tree, visit)

    def fill_rect(self, array, x, y, w, h, color):
        array[y : y + h, x : x + w] = color

    def copy_rect(self, dst_array, dx, dy, src_array, sx, sy, w, h):
        dst_array[dy : dy + h, dx : dx + w] = src_array[sy : sy + h, sx : sx + w]

    def walk_node(self, type, node_tree, function):
        nodes = None

        if type == self.NodesType.ALL:
            nodes = node_tree.nodes
        elif type == self.NodesType.WALK:
            nodes = []

            def walk(node):
                nodes.append(node)

            walk_shader_node.walk_tree(node_tree, walk)
        else:
            logger.warn("invalid NodesType value: {}".format(type))

        for node in nodes:
            function(node)
