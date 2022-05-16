import os


def is_uvmap_upper_limit(context):
    limit_objs = []
    result = [False, limit_objs]

    for obj in context.selected_objects:
        if not hasattr(obj.data, "uv_layers"):
            continue
        num = len(obj.data.uv_layers)
        if num >= 8:
            result[0] = True
            limit_objs.append(obj)

    return tuple(result)


def get_asset_material(context, material_name):
    blend = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../asset/TextureAtlasGenerator.blend"
        )
    )

    with context.blend_data.libraries.load(blend) as (data_from, data_to):
        data_to.materials = [material_name]

    return data_to.materials[0]
