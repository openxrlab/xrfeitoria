import bpy

from .operators import RenderPassesOperator, StartRPCServerOperator


class VIEW3D_PT_XRFeitoria_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XRFeitoria'
    bl_label = 'XRFeitoria'

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        op = row.operator(StartRPCServerOperator.bl_idname, text='Start RPC Server')
        op.debug = True

        layout.separator()
        layout.label(text='Manage sequences:')

        # TODO: new sequence
        scene = context.scene
        layout.prop(scene.level_properties, property='active_sequence', text='Active')


panel_classes = [VIEW3D_PT_XRFeitoria_Panel]


def register():
    for panel_class in panel_classes:
        bpy.utils.register_class(panel_class)


def unregister():
    for panel_class in reversed(panel_classes):
        bpy.utils.unregister_class(panel_class)
