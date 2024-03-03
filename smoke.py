import struct

import zengl
import vmath


class Smoke:
    def __init__(self, uniform_buffer, model, framebuffer):
        ctx = zengl.context()
        self.instance = struct.Struct('3f 4f 1f 3f')
        self.vertex_buffer = ctx.buffer(open(model, 'rb').read())
        self.instance_buffer = ctx.buffer(size=self.instance.size * 10000)
        self.pipeline = ctx.pipeline(
            vertex_shader=open('shaders/particles.vert').read(),
            fragment_shader=open('shaders/particles.frag').read(),
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
            vertex_buffers=[
                *zengl.bind(self.vertex_buffer, '3f 3f 3f', 0, 1, -1),
                *zengl.bind(self.instance_buffer, '3f 4f 1f 3f /i', 2, 3, 4, 5),
            ],
            vertex_count=self.vertex_buffer.size // zengl.calcsize('3f 3f 3f'),
        )
        self.instances = []

    def add(self, position, velocity, rotation, scale, color, lifetime):
        self.instances.append([position, velocity, rotation, scale, color, lifetime])

    def update(self):
        remove = False
        for instance in self.instances:
            instance[0] = vmath.add(instance[0], instance[1])
            instance[5] -= 1
            if instance[5] <= 0:
                remove = True

        if remove:
            self.instances = [x for x in self.instances if x[5] > 0]

    def render(self):
        data = bytearray()
        for position, velocity, rotation, scale, color, lifetime in self.instances:
            data.extend(self.instance.pack(*position, *rotation, scale, *color))
        self.instance_buffer.write(data)
        self.pipeline.instance_count = len(self.instances)
        self.pipeline.render()
