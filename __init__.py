import importlib
import inspect
import sys
from pathlib import Path

import bpy

from .lib import logging_settings

logger = logging_settings.get_logger(__name__)

# モジュール読み込み
module_names = [
    "logging_settings",
    "atlas",
    "walk_shader_node",
    "blf_solver",
    "texture_group",
    "texture_link",
    "texture_scale",
    "panel"
]
namespace = globals()
for name in module_names:
    fullname = '{}.{}.{}'.format(__package__, "lib", name)
    if fullname in sys.modules:
        namespace[name] = importlib.reload(sys.modules[fullname])
    else:
        namespace[name] = importlib.import_module(fullname)

# アドオン情報
bl_info = {
    'name': 'Taremin Texture Atlas Generator',
    'category': '3D View',
    'author': 'Taremin',
    'location': 'View 3D > Taremin',
    'description': "Generate texture atlas from selected objects",
    'version': (0, 0, 4),
    'blender': (2, 80, 0),
    'wiki_url': '',
    'tracker_url': '',
    'warning': '',
}

# クラスの登録
classes = [
    # このファイル内のBlenderクラス
]
for module in module_names:
    for module_class in [obj for name, obj in inspect.getmembers(namespace[module], inspect.isclass) if hasattr(obj, "bl_rna")]:
        classes.append(module_class)


def register():
    for value in classes:
        bpy.utils.register_class(value)
    panel = namespace["panel"]
    bpy.types.Scene.taremin_tag = bpy.props.PointerProperty(type=panel.AtlasPanelProps)


def unregister():
    for value in classes:
        bpy.utils.unregister_class(value)
    del bpy.types.Scene.taremin_tag
    Path(__file__).touch()


if __name__ == '__main__':
    register()
