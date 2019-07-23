import bpy


def walk_group(group, func, output_type=bpy.types.ShaderNodeOutputMaterial):
    outputs = [n for n in group.nodes if isinstance(n, output_type)]
    for output in outputs:
        walk_node(output, func)

    # chack reachable inputs
    if output_type is bpy.types.NodeGroupOutput:
        input_nodes = [n for n in group.nodes if isinstance(n, bpy.types.NodeGroupInput)]
        reachable = []
        for node in input_nodes:
            outputs = node.outputs
            for o_socket in outputs:
                for link in o_socket.links:
                    next_node = link.to_node

                    def get_reachable(node):
                        if isinstance(node, bpy.types.NodeGroupOutput):
                            reachable.append(o_socket.identifier)

                    walk_input_to_output(next_node, get_reachable)
        return list(set(reachable))
    return None


def walk_input_to_output(node, func):
    func(node)
    if isinstance(node, bpy.types.NodeGroupOutput):
        return
    for o_socket in node.outputs:
        for link in o_socket.links:
            next_node = link.to_node
            walk_input_to_output(next_node, func)


def walk_node(node, func, socket=None):
    func(node)
    inputs = node.inputs if socket is None else socket
    for i_socket in inputs:
        for link in i_socket.links:
            next_node = link.from_node
            if isinstance(next_node, bpy.types.ShaderNodeGroup):
                reachable = walk_group(next_node.node_tree, func, bpy.types.NodeGroupOutput)
                sockdic = {}
                for sock in next_node.inputs:
                    sockdic[sock.identifier] = sock
                reachable_socket = [sockdic[id] for id in reachable]
                walk_node(next_node, func, reachable_socket)
            else:
                walk_node(next_node, func)
