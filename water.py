import zengl


def make_water(uniform_buffer, depth_texture, framebuffer):
    ctx = zengl.context()
    return ctx.pipeline(
        vertex_shader=open('shaders/water.vert').read(),
        fragment_shader=open('shaders/water.frag').read(),
        layout=[
            {
                'name': 'Common',
                'binding': 0,
            },
            {
                'name': 'Depth',
                'binding': 0,
            },
        ],
        resources=[
            {
                'type': 'uniform_buffer',
                'binding': 0,
                'buffer': uniform_buffer,
            },
            {
                'type': 'sampler',
                'binding': 0,
                'image': depth_texture,
                'wrap_x': 'clamp_to_edge',
                'wrap_y': 'clamp_to_edge',
                'min_filter': 'nearest',
                'mag_filter': 'nearest',
            },
        ],
        uniforms={
            'Time': 0.0,
            'WaterLevel': 0.0,
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
