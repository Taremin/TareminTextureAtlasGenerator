import bpy
import numpy
import bmesh
from enum import Enum
from . import walk_shader_node
from . import blf_solver


class OBJECT_OT_Atlas(bpy.types.Operator):
    bl_idname = 'taremin.atlas'
    bl_label = 'Generate Texture Atlas'
    bl_description = 'atlas'
    bl_options = {'REGISTER', 'UNDO'}

    class NodesType(Enum):
        ALL = 0
        WALK = 1

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        settings = context.scene.taremin_tag

        # 選択オブジェクトのマテリアル
        target_materials = self.get_selected_objects_materials(context)

        # 対象マテリアルのコピーを作成し、コピー元からコピー先への辞書を作成
        mat_copy_dic = self.copy_materials(target_materials)

        # 対象マテリアルのテクスチャノード取得
        textures = self.get_texture_nodes(target_materials)

        # テクスチャからUVレイヤーの紐づけ
        image_uv_dic = self.get_image_to_uv_dict(context, textures)

        # TODO: UVが同じでテクスチャが異なるものの対策を考える

        # create rects
        rects = self.get_rects_from_unique_textures(image_uv_dic.keys(), image_uv_dic)

        # create atlas
        image, image_point_dic = self.create_atlas(context, rects, name=settings.output_texture_name)

        for obj in context.selected_objects:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.faces.ensure_lookup_table()

            add = self.add_clone_materials(obj, target_materials)

            # マテリアルごとの面を用意
            material_face = self.create_material_face_indices(obj, bm)

            # UVMapの作成
            new_uv = self.create_new_uvmap(obj, bm, image.size, image_point_dic, material_face, name=settings.output_uvmap_name)

            # マテリアル(コピー)の追加
            material_idx_dict = self.get_clone_material_idx_dict(obj, add, mat_copy_dic)

            # UVMapノードの取得
            uvmap_nodes = self.get_uvmap_nodes(obj, add, material_idx_dict)

            # 面のマテリアル割当の差し替え
            if settings.replace_face_material:
                for face in bm.faces:
                    face.material_index = material_idx_dict[face.material_index]

            uvmap_name = new_uv.name
            bm.to_mesh(obj.data)
            obj.data.update()
            bm.free()

            # UVMapノードを書き換え
            for uvmap_node in uvmap_nodes:
                uvmap_node.uv_map = uvmap_name

            # アクティブUVMapの変更
            obj.data.uv_layers.active = obj.data.uv_layers[uvmap_name]
            obj.data.uv_layers[uvmap_name].active_render = True

            # 余計なUVMapの削除
            if settings.remove_uvmaps:
                remove_list = []
                for uv_layer in obj.data.uv_layers:
                    if uv_layer.name != uvmap_name:
                        remove_list.append(uv_layer)
                for uv_layer in reversed(remove_list):
                    obj.data.uv_layers.remove(uv_layer)

        # マテリアルのテクスチャノードの書き換え
        self.replace_material_texture([mat_copy_dic[material] for material in target_materials], image)

        # 使用してないマテリアルスロットの削除
        # self.remove_unused_material_slots(context)
        if settings.remove_material_slots:
            active_materials = {}
            for obj in context.selected_objects:
                active_index = obj.active_material_index
                remove_list = reversed([i for i, slot in enumerate(obj.material_slots) if i != active_index])
                for index in remove_list:
                    obj.active_material_index = index
                    bpy.ops.object.material_slot_remove()
                active_materials[obj.material_slots[obj.active_material_index].material] = True

            if settings.replace_active_material_nodetree:
                self.replace_material_texture(active_materials.keys(), image)

        # TODO: 画像をパックする？

        return {'FINISHED'}

    def get_selected_objects_materials(self, context):
        target_materials = []
        for obj in context.selected_objects:
            for material in obj.data.materials:
                if material not in target_materials:
                    target_materials.append(material)
        return target_materials

    def copy_materials(self, materials, suffix=".atlas"):
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

    def get_texture_nodes(self, materials):
        textures = []
        for material in materials:
            if material.node_tree is None:
                continue

            def get_texture_image(node):
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image is not None:
                    textures.append(node)

            walk_shader_node.walk_group(material.node_tree, get_texture_image)
        return textures

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
                        print("Unsupported Node (UVMap)")
                        return {'CANCELLED'}

                if image not in image_uv_dict:
                    image_uv_dict[image] = []
                if uv not in image_uv_dict[image]:
                    image_uv_dict[image].append(uv)
        return image_uv_dict

    def get_rects_from_unique_textures(self, images, image_to_uv_dict):
        return [
            (image.size[0], image.size[1], image, image_to_uv_dict[image])
            for image in images
        ]

    def calc_init_size(self, rects):
        size = 1
        max_size = 0
        total = 0
        for w, h, *etc in rects:
            total += w * h
        while size * size < total:
            size <<= 1

        return size

    def create_atlas(self, context, rects, name="texture"):
        settings = context.scene.taremin_tag
        blf = blf_solver.BLFSolver(rects)
        size, results = blf.solve(self.calc_init_size(rects))

        atlas_image = bpy.data.images.new(name=name, width=size, height=size)
        pixels = numpy.array(atlas_image.pixels).reshape(size, size, 4)

        # texture link
        dic = {}
        used_texture_group = {}
        numpy_dic = {}
        for link in settings.texture_links:
            ref_type = int(link.ref_type)
            texture_group = settings.texture_groups[ref_type]
            source = link.ref_source

            if texture_group not in used_texture_group:
                # create link texture
                link_texture_name = ".".join((name, texture_group.name))
                link_image = bpy.data.images.new(name=link_texture_name, width=size, height=size)
                link_pixels = numpy.full((size, size, 4), list(texture_group.color) + [1.0])

                used_texture_group[texture_group] = link_image
            else:
                link_image = used_texture_group[texture_group]

            # atlas image -> link image dictionary
            if source not in dic:
                dic[source] = []
            dic[source].append((link_image, link_pixels, link.ref_link))

        # atlas
        atlas_image_map = {}
        for (x, y, w, h, idx, image, mesh_uv_loop_layers) in results:
            src_pixels = numpy.array(image.pixels).reshape(image.size[1], image.size[0], 4)
            self.copy_rect(pixels, x, y, src_pixels, 0, 0, w, h)
            atlas_image_map[image] = (x, y, w, h)

        # copy link texture
        link_images = {}
        for image in atlas_image_map:
            x, y, w, h = atlas_image_map[image]
            if image in dic:
                for (link_image, link_pixels, copy_source_image) in dic[image]:
                    src_pixels = numpy.array(copy_source_image.pixels).reshape(copy_source_image.size[1], copy_source_image.size[0], 4)
                    self.copy_rect(link_pixels, x, y, src_pixels, 0, 0, w, h)
                    link_images[link_image] = link_pixels
        for link_image in link_images:
            link_image.pixels = link_images[link_image].ravel()

        atlas_image.pixels = pixels.ravel()

        return (atlas_image, atlas_image_map)

    def add_clone_materials(self, obj, target_materials):
        add = []
        for material_slot_idx, material_slot in enumerate(obj.material_slots):
            material = material_slot.material
            if material in target_materials:
                add.append(material_slot_idx)
        return add

    def create_material_face_indices(self, obj, bm):
        mat_to_face = {}
        for face_idx, face in enumerate(bm.faces):
            material = obj.material_slots[face.material_index].material
            if material not in mat_to_face:
                mat_to_face[material] = []
            mat_to_face[material].append(face_idx)
        return mat_to_face

    def create_new_uvmap(self, obj, bm, size, image_point_dic, material_face, name="AtlasUVMap"):
        new_uv = bm.loops.layers.uv.new(name)
        width, height = size
        for material_slot in obj.material_slots:
            material = material_slot.material
            if material not in material_face:
                continue
            faces = material_face[material]

            def texture_image(node):
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image is not None:
                    uv_layer = None
                    if not node.inputs["Vector"].links:
                        uv_layer = bm.loops.layers.uv.active
                    else:
                        uvmap_node = node.inputs["Vector"].links[0].from_node
                        if isinstance(uvmap_node, bpy.types.ShaderNodeUVMap):
                            uv_layer = bm.loops.layers.uv[uvmap_node.uv_map]
                        else:
                            print("Unsupported Node (UVMap)")
                    if uv_layer is not None:
                        new_layer = new_uv
                        x, y, w, h = image_point_dic[node.image]
                        for face_idx in material_face[material]:
                            for loop in bm.faces[face_idx].loops:
                                u, v = loop[uv_layer].uv
                                loop[new_layer].uv = (
                                    (w * u + x) / width,
                                    (h * v + y) / height
                                )

            if material.node_tree is None:
                continue

            walk_shader_node.walk_group(material.node_tree, texture_image)
        return new_uv

    def get_clone_material_idx_dict(self, obj, add, mat_copy_dic):
        material_idx_dict = {}

        for material_slot_idx in add:
            new_idx = len(obj.data.materials)
            material = mat_copy_dic[obj.material_slots[material_slot_idx].material]
            obj.data.materials.append(material)
            material_idx_dict[material_slot_idx] = new_idx

        return material_idx_dict

    def get_uvmap_nodes(self, obj, add, material_idx_dict):
        uvmap_nodes = []

        for material_slot_idx in add:
            material = obj.material_slots[material_idx_dict[material_slot_idx]].material

            def get_uvmap_nodes(node):
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image is not None:
                    links = node.inputs["Vector"].links
                    if not links:
                        return
                    uvmap_node = links[0].from_node
                    if isinstance(uvmap_node, bpy.types.ShaderNodeUVMap):
                        uvmap_nodes.append(uvmap_node)

            walk_shader_node.walk_group(material.node_tree, get_uvmap_nodes)

        return uvmap_nodes

    def replace_material_texture(self, target_materials, image):
        def texture_image(node):
            if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image is not None:
                print(node.image)
                node.image = image

        for material in target_materials:
            self.walk_node(self.NodesType.WALK, material.node_tree, texture_image)

    def remove_unused_material_slots(self, context):
        for obj in context.selected_objects:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.faces.ensure_lookup_table()

            used_material = {}
            for face in bm.faces:
                used_material[face.material_index] = True

            bm.to_mesh(obj.data)
            obj.data.update()
            bm.free()

            material_slot_num = len(obj.material_slots)
            current = obj.active_material_index
            for i in range(material_slot_num):
                idx = material_slot_num - i - 1
                if idx in used_material:
                    continue
                obj.active_material_index = idx
                bpy.ops.object.material_slot_remove()

                if idx == current:
                    current = 0
                if idx < current:
                    current -= 1
            obj.active_material_index = current

    def fill_rect(self, array, x, y, w, h, color):
        array[y:y + h, x:x + w] = color

    def copy_rect(self, dst_array, dx, dy, src_array, sx, sy, w, h):
        dst_array[dy:dy + h, dx:dx + w] = src_array[sy:sy + h, sx:sx + w]

    def walk_node(self, type, node_tree, function):
        if type == self.NodesType.ALL:
            nodes = node_tree.nodes
        elif type == self.NodesType.WALK:
            nodes = []

            def walk(node):
                nodes.append(node)

            walk_shader_node.walk_group(node_tree, walk)
        else:
            print("Invalid NodesType value: {}".format(type))

        for node in nodes:
            function(node)
