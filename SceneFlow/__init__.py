bl_info = {
    "name": "SceneFlow",
    "author": "cgnerd143",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "View3D > Sidebar > SceneFlow",
    "description": "Manage object visibility with batch tools, isolation toggle, undo support, and exportable object lists. Report issues: https://github.com/cgnerd143/SceneFlow/issues.",
    "category": "Scene & Object",
    "support": "Developer", # You can put a text label here if you want
    "developer": "https://github.com/cgnerd143",
    "tracker_url": "https://github.com/cgnerd143/SceneFlow/issues",
    "doc_url": "https://sketchfab.com/XsTerbEnX", # Portfolio URL in doc_url
}

import os
import sys

# Ensure submodules are importable
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Safe deferred registration
from . import sceneflow

register = sceneflow.register
unregister = sceneflow.unregister
