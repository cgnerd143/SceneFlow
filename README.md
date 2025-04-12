# 🎛️ SceneFlow – Scene & Object Manager for Blender

**SceneFlow** is a lightweight, intuitive Blender addon built to streamline **scene and object visibility management**. Perfect for organizing large scenes, toggling object states, and maintaining clarity in animation or modeling workflows.

![image](https://github.com/user-attachments/assets/fc0a9a93-2bc3-4adb-8f5e-f138907f13d3)


---

## ✨ Features

✅ **Scene-Aware Object List Management**  
Add objects to a custom list from selection or by name, and manage them independently of Blender’s native collection system.

✅ **Powerful Visibility Controls**  
Quickly `Hide`, `Unhide`, `Isolate`, `Restore`, and `Delete` objects — either from the list or current selection.

✅ **Text-Based Import / Export**  
Save and load object lists with `.txt` files to simplify scene setup reuse and shareability.

✅ **Auto Export Support**  
Enable auto-saving of the current list when making changes — great for collaborative workflows or keeping backups.

✅ **Undo & Redo Integration**  
All actions respect Blender’s native Undo system (`Ctrl+Z`), so you can explore freely without risk.

✅ **Clean Sidebar UI**  
Organized into intuitive panels:
- 🎛 List Controls  
- 🧲 Selected Object Controls  
- ℹ️ About Panel with quick access to support & documentation

---
🧪 Upcoming Features (Planned)
🔄 Object History Panel (Inspired by Maya)
Track operations like visibility changes, transformations, and isolations — all stored per object. Aimed at improving scene debugging and non-linear workflows.

🧹 Delete History
Quickly clean object history and reset transform tracking — similar to Maya’s Delete History feature. Ideal for prepping assets before exporting or handing off.

🧊 Freeze Transformations
Zero out location/rotation/scale while preserving world-space positions. Great for rigging, anim cleanup, and instancing.

📍 Advanced Pivot Controls
Move, align, and snap pivot points easily (without affecting geometry). Precise pivot workflows for modeling, rigging, and layout.

## 🔧 Installation

1. Download the latest `.zip` from [Releases](https://github.com/cgnerd143/SceneFlow/releases)
2. In Blender: **Edit > Preferences > Add-ons > Install**
3. Select the `.zip`, click **Install Add-on**, and enable **SceneFlow**

---

## 🧠 Tips & Notes

- `Isolate / Restore` are temporary view modes, not undoable (like Blender's Local View).
- Use `Unhide All` (or `Alt+H`) to reveal everything after isolating.
- Great for animation prep, layout, lookdev, and cluttered scene cleanup.

---



## 🛠 Support & Links

- 📄 [GitHub Page](https://github.com/cgnerd143)
- 🐞 [Report Issues](https://github.com/cgnerd143/SceneFlow/issues)

