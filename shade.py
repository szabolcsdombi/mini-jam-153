import zengl


def make_shade(framebuffer):
    ctx = zengl.context()
    return ctx.pipeline(
        vertex_shader=open('shaders/shade.vert').read(),
        fragment_shader=open('shaders/shade.frag').read(),
        uniforms={
            'Color': [0.0, 0.0, 0.0, 0.0],
        },
        blend={
            'enable': True,
            'src_color': 'src_alpha',
            'dst_color': 'one_minus_src_alpha',
        },
        framebuffer=framebuffer,
        topology='triangles',
        vertex_count=3,
    )
