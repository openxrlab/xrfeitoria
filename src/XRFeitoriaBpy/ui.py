import bpy
from .operators import BpyRenderWithLogOperator, StartRPCServerOperator, RenderPassesOperator

class VIEW3D_PT_XRFeitoria_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "XRFeitoria"
    bl_label = "XRFeitoria"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator(BpyRenderWithLogOperator.bl_idname, text="Render with log")
        row = layout.row(align=True)
        row.operator(StartRPCServerOperator.bl_idname, text="Start RPC Server")
        row = layout.row(align=True)
        row.operator(RenderPassesOperator.bl_idname, text="Add Render Passes")


panel_classes = [
    VIEW3D_PT_XRFeitoria_Panel,
]

def register():
    for panel_class in panel_classes:
        bpy.utils.register_class(panel_class)
    
def unregister():
    for panel_class in reversed(panel_classes):
        bpy.utils.unregister_class(panel_class)