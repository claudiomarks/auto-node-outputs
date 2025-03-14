import bpy
import math

def create_node_group(tree, nodes, name):
    """Create a group node containing the specified nodes"""
    # Create a new node group
    group = bpy.data.node_groups.new(name, 'CompositorNodeTree')
    
    # Create group input/output nodes
    group_inputs = group.nodes.new('NodeGroupInput')
    group_inputs.location = (-200, 0)
    group_outputs = group.nodes.new('NodeGroupOutput')
    group_outputs.location = (400, 0)
    
    # Add nodes to the group
    for node in nodes:
        # Keep track of the node's links
        input_links = []
        output_links = []
        
        for input_socket in node.inputs:
            for link in input_socket.links:
                input_links.append((link.from_socket, input_socket))
        
        for output_socket in node.outputs:
            for link in output_socket.links:
                if link.to_node not in nodes:  # Only track links to nodes outside the group
                    output_links.append((output_socket, link.to_socket))
        
        # Temporarily remove the node from the tree
        tree.nodes.remove(node)
        
        # Create a new node in the group
        new_node = group.nodes.new(node.bl_idname)
        new_node.name = node.name
        new_node.label = node.label
        new_node.location = node.location
        
        # TODO: Copy other properties if needed
        
        # Recreate links within the group
        for from_socket, to_socket in input_links:
            if from_socket.node in nodes:
                # Internal link, recreate within group
                group.links.new(from_socket, to_socket)
            else:
                # External input, create group input socket
                group_input = group.inputs.new('NodeSocketColor', from_socket.name)
                group.links.new(group_inputs.outputs[-1], to_socket)
        
        for from_socket, to_socket in output_links:
            # Create group output socket
            group_output = group.outputs.new('NodeSocketColor', from_socket.name)
            group.links.new(from_socket, group_outputs.inputs[-1])
    
    # Create the group node in the original tree
    group_node = tree.nodes.new('CompositorNodeGroup')
    group_node.node_tree = group
    group_node.name = name
    group_node.label = name
    
    # Connect the group node to the original tree
    # TODO: Restore external connections
    
    return group_node

def arrange_nodes(tree, organize_type='GRID'):
    """Arrange nodes in the compositor tree"""
    # Get all nodes
    nodes = tree.nodes
    
    if organize_type == 'GRID':
        # Simple grid arrangement
        grid_size = math.ceil(math.sqrt(len(nodes)))
        for i, node in enumerate(nodes):
            row = i // grid_size
            col = i % grid_size
            node.location = (col * 300, -row * 300)
    
    elif organize_type == 'FLOW':
        # Arrange nodes in a left-to-right flow
        # First, find all render layer nodes (starting points)
        render_layer_nodes = [n for n in nodes if n.type == 'R_LAYERS']
        
        # Position render layer nodes vertically
        for i, node in enumerate(render_layer_nodes):
            node.location = (0, -i * 300)
        
        # TODO: Implement a more sophisticated flow layout algorithm
        # This would need to follow the connections between nodes
    
    elif organize_type == 'HIERARCHY':
        # Group nodes by their connections
        # For each render layer node and its output node
        viewlayer_nodes = [(n, get_connected_output(tree, n)) for n in nodes if n.type == 'R_LAYERS']
        
        for i, (rl_node, output_node) in enumerate(viewlayer_nodes):
            if output_node:
                rl_node.location = (0, -i * 300)
                output_node.location = (300, -i * 300)
    
    return {'FINISHED'}

def get_connected_output(tree, node):
    """Find the output node connected to the given node"""
    for output in node.outputs:
        for link in output.links:
            if link.to_node.type == 'OUTPUT_FILE':
                return link.to_node
    return None

def sort_viewlayers(scene, sort_type='ALPHABETICAL'):
    """Sort viewlayers by the specified method"""
    viewlayers = list(scene.view_layers)
    
    if sort_type == 'ALPHABETICAL':
        # Sort alphabetically
        viewlayers.sort(key=lambda vl: vl.name.lower())
    elif sort_type == 'CUSTOM':
        # Sort by custom property (would need to be added to viewlayers)
        pass
    
    # Return the sorted list
    return viewlayers

def clear_all_viewlayer_nodes(tree):
    """Remove all viewlayer and output nodes"""
    nodes_to_remove = []
    
    for node in tree.nodes:
        if node.type == 'R_LAYERS' or node.type == 'OUTPUT_FILE':
            nodes_to_remove.append(node)
    
    # Remove the nodes
    for node in nodes_to_remove:
        tree.nodes.remove(node)
    
    return len(nodes_to_remove)

def group_viewlayer_nodes(tree):
    """Group each viewlayer node with its corresponding output node"""
    viewlayer_nodes = [n for n in tree.nodes if n.type == 'R_LAYERS']
    groups_created = 0
    
    for vl_node in viewlayer_nodes:
        output_node = get_connected_output(tree, vl_node)
        if output_node:
            group_name = f"ViewLayer_{vl_node.name}_Group"
            create_node_group(tree, [vl_node, output_node], group_name)
            groups_created += 1
    
    return groups_created