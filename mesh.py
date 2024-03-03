import zengl


def make_mesh(uniform_buffer, model, framebuffer, blending=False):
    ctx = zengl.context()
    vertex_buffer = ctx.buffer(open(model, 'rb').read())
    blend = None
    if blending:
        blend = {
            'enable': True,
            'src_color': 'src_alpha',
            'dst_color': 'one_minus_src_alpha',
        }
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
        uniforms={
            'Position': [0.0, 0.0, 0.0],
            'Rotation': [0.0, 0.0, 0.0, 0.0],
            'Alpha': 1.0,
        },
        blend=blend,
        framebuffer=framebuffer,
        topology='triangles',
        cull_face='back',
        vertex_buffers=zengl.bind(vertex_buffer, '3f 3f 3f', 0, 1, 2),
        vertex_count=vertex_buffer.size // zengl.calcsize('3f 3f 3f'),
    )
