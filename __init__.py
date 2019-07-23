import bpy
import importlib
import sys
import inspect
from pathlib import Path

# モジュール読み込み
module_names = [
    "atlas",
    "walk_shader_node",
    "blf_solver",
    "texture_group",
    "texture_link",
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
    'name': 'Texture Atlas Generator',
    'category': '3D View',
    'author': 'Taremin',
    'location': 'View 3D > Tools',
    'description': "Generate texture atlas from selected objects",
    'version': (0, 0, 1),
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
    bpy.types.Scene.taremin_tag = bpy.props.PointerProperty(type=panel.AtlasPanelProps)  # TODO


def unregister():
    for value in classes:
        bpy.utils.unregister_class(value)
    del bpy.types.Scene.taremin_tag
    Path(__file__).touch()

if __name__ == '__main__':
    register()
