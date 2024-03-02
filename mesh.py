import zengl


def make_mesh(uniform_buffer, model, framebuffer):
    ctx = zengl.context()
    vertex_buffer = ctx.buffer(open(model, 'rb').read())
    return ctx.pipeline(
        vertex_shader=open('shaders/mesh.vert').read(),
        fragment_shader=open('shaders/mesh.frag').read(),
        layout=[
            {
                'name': 'Common',
                'binding': 0,
            },
        ],
        resources=[
            {
                'type': 'uniform_buffer',
                'binding': 0,
                'buffer': uniform_buffer,
            },
        ],
        framebuffer=framebuffer,
        topology='triangles',
        cull_face='back',
        vertex_buffers=zengl.bind(vertex_buffer, '3f 3f 3f', 0, 1, 2),
        vertex_count=vertex_buffer.size // zengl.calcsize('3f 3f 3f'),
    )
