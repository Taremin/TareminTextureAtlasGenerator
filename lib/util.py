import bpy
import os
import json
import time

path = os.path.join(os.path.dirname(__file__), "../resources.json")
resources = json.load(open(path, encoding="utf-8"))


def read_resource(*props):
    lang = bpy.app.translations.locale
    prop = resources
    for prop_name in props:
        prop = prop[prop_name]
    return prop[lang] if lang in prop else prop["en_US"]


def read_property(*props):
    return read_resource("property", *props)


def read_panel(*props):
    return read_resource("panel", *props)


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
        os.path.join(os.path.dirname(__file__), "../asset/TextureAtlasGenerator.blend")
    )

    with context.blend_data.libraries.load(blend) as (data_from, data_to):
        data_to.materials = [material_name]

    return data_to.materials[0]


def measure(msg, func, *args, **kwargs):
    start = time.perf_counter()
    retval = func(*args, **kwargs)
    end = time.perf_counter()

    print(
        f"{msg} in Function:{func.__name__} processing time:{round(end - start, 4)} sec"
    )

    return retval
