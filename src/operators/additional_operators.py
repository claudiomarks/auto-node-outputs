import bpy
from bpy.types import Operator

class COMPOSITOR_OT_setup_nodes(Operator):
    """Enable compositor nodes"""
    bl_idname = "compositor.setup_nodes"
    bl_label = "Enable Compositor Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.use_nodes = True
        self.report({'INFO'}, "Compositor nodes enabled")
        return {'FINISHED'}

class COMPOSITOR_OT_clear_viewlayer_outputs(Operator):
    """Clear previously created ViewLayer output nodes"""
    bl_idname = "compositor.clear_viewlayer_outputs"
    bl_label = "Clear ViewLayer Outputs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.scene.use_nodes:
            self.report({'WARNING'}, "Compositor nodes are not enabled")
            return {'CANCELLED'}
        
        tree = context.scene.node_tree
        nodes_removed = 0
        
        # Remove ViewLayer nodes
        for node in tree.nodes:
            if node.name.startswith("ViewLayer_") or node.name.startswith("Output_"):
                tree.nodes.remove(node)
                nodes_removed += 1
        
        self.report({'INFO'}, f"Removed {nodes_removed} nodes")
        return {'FINISHED'}