import bpy


def walk_tree(nodetree, func, output_type=bpy.types.ShaderNodeOutputMaterial):
    outputs = [n for n in nodetree.nodes if isinstance(n, output_type)]
    target = []

    def walk_process(node):
        target.append(node)

    for output in outputs:
        walk_node(output, walk_process)

    for node in list(set(target)):
        func(node)


def walk_node(node, func, socket=None, stack=[], depth=0):
    func(node)
    inputs = node.inputs if socket is None else [socket]

    for i_socket in inputs:
        for link in i_socket.links:
            next_node = link.from_node
            next_socket = link.from_socket

            # Group In
            if isinstance(next_node, bpy.types.ShaderNodeGroup):
                stack.append(next_node)

                group = next_node.node_tree
                group_outputs = [n for n in group.nodes if isinstance(n, bpy.types.NodeGroupOutput)]

                for group_output in group_outputs:
                    for i in group_output.inputs:
                        if i.identifier == next_socket.identifier:
                            walk_node(group_output, func, socket=i, stack=stack, depth=depth + 1)
            # Group Out
            elif isinstance(next_node, bpy.types.NodeGroupInput):
                next_node = stack[-1:][0]
                for i in next_node.inputs:
                    if i.identifier == next_socket.identifier:
                        walk_node(next_node, func, socket=i, stack=stack[:-1], depth=depth - 1)
            else:
                walk_node(next_node, func, stack=stack, depth=depth)
