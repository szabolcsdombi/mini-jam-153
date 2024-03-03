import itertools
import math
import os
import struct
import sys

import numpy as np
import pygame
import zengl

import quat
from mesh import make_mesh
from shade import make_shade
from water import make_water

def step(x, a, b):
    return (min(max(x, a), b) - a) / (b - a)

def smoothstep(x, a, b):
    x = step(x, a, b)
    return x * x * (3 - 2 * x)

def smootherstep(x, a, b):
    x = step(x, a, b)
    return x * x * x * (x * (x * 6 - 15) + 10)

os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

pygame.init()
pygame.display.set_mode((1280, 720), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)

ctx = zengl.context()

size = pygame.display.get_window_size()
image = ctx.image(size, 'rgba8unorm')
depth = ctx.image(size, 'depth24plus')

uniform_buffer = ctx.buffer(size=96, uniform=True)

water = make_water(uniform_buffer, depth, [image])
sand = make_mesh(uniform_buffer, 'assets/sand.bin', [image, depth])
start = make_mesh(uniform_buffer, 'assets/start.bin', [image, depth], blending=True)
sign = make_mesh(uniform_buffer, 'assets/sign.bin', [image, depth])
fish = make_mesh(uniform_buffer, 'assets/fish.bin', [image, depth])
shotgun = make_mesh(uniform_buffer, 'assets/shotgun.bin', [image, depth])

shade = make_shade([image])

eye = (6.4, 0.0, 3.5)
light = (3.0, 4.0, 30.0)

def update_camera(target, fov):
    aspect = size[0] / size[1]
    camera = zengl.camera(eye, target, aspect=aspect, fov=fov)
    uniform_buffer.write(struct.pack('64s3f4x3f4x', camera, *eye, *light))

def render_model(model, position, rotation):
    model.uniforms['Position'][:] = struct.pack('3f', *position)
    model.uniforms['Rotation'][:] = struct.pack('4f', *rotation)
    model.render()

def render_water():
    water.uniforms['Time'][:] = struct.pack('f', g.now)
    water.uniforms['WaterLevel'][:] = struct.pack('f', 1.0 + math.sin(g.now) * 0.5)
    water.render()


class ScenePlay:
    def __init__(self):
        self.fishes = np.random.uniform(-0.5, 0.5, (10, 4))
        self.rotations = np.random.uniform(-0.5, 0.5, (10, 4))
        self.rotations /= np.linalg.norm(self.rotations, axis=1)[:, None]

    def render(self):
        mouse = pygame.mouse.get_pos()
        mx = mouse[0] / size[0] * 2.0 - 1.0
        my = 1.0 - mouse[1] / size[1] * 2.0
        camera_target = (5.68, 0.0, 2.9 + 0.55)
        gun_rotation = quat.quatmul(quat.rz(-mx * 0.5), quat.ry(my * 0.5))
        update_camera(camera_target, fov=50.0)
        sand.render()
        render_model(shotgun, (5.96, 0.38, 3.25), gun_rotation)
        for i in range(10):
            x, y, z, w = self.fishes[i]
            z += math.sin(g.now * 3.0 + w * 6.0) * 6.0
            render_model(fish, (x * 10.0 - 16.0, y + (i - 4.5) * 3.0, z), self.rotations[i])
        render_water()


class SceneIntro:
    def __init__(self):
        self.start = g.now

    def render(self):
        elapsed = g.now - self.start

        z = smootherstep(elapsed, 1.0, 5.0) * 0.55
        y = smootherstep(elapsed, 6.0, 9.0) * 0.225
        y -= smootherstep(elapsed, 12.0, 15.0) * 0.225
        fov = 45.0 + smootherstep(elapsed, 12.0, 15.0) * 5.0
        start_alpha = 0.8 - smoothstep(elapsed, 0.0, 0.3) * 0.8

        update_camera((5.68, -y, 2.9 + z), fov=fov)
        sand.render()

        start.uniforms['Alpha'][:] = struct.pack('f', start_alpha)
        start.render()

        sign.render()

        render_water()

        if elapsed > 15.0:
            g.scene = ScenePlay()


class SceneFadeIn:
    def __init__(self):
        self.start = g.now

    def render(self):
        elapsed = g.now - self.start

        shade_alpha = 1.0 - smoothstep(elapsed, 0.0, 1.0)
        start_alpha = smoothstep(elapsed, 7.1, 7.6)

        mouse = pygame.mouse.get_pos()
        mx = mouse[0] / size[0] * 2.0 - 1.0
        my = 1.0 - mouse[1] / size[1] * 2.0

        hovering_start = elapsed > 7.5 and -0.23 < mx < 0.23 and 0.035 < my < 0.3

        if hovering_start:
            start_alpha = 0.8

        update_camera((5.68, 0.0, 2.9), fov=45.0)
        sand.render()

        start.uniforms['Alpha'][:] = struct.pack('f', start_alpha)
        start.render()

        render_water()

        shade.uniforms['Color'][:] = struct.pack('4f', 0.0, 0.0, 0.0, shade_alpha)
        shade.render()

        if hovering_start and 'mouse1' in g.keys:
            g.scene = SceneIntro()


class ScenePressAnyKey:
    def render(self):
        if len(g.keys) > 0:
            g.first_tick = pygame.time.get_ticks()
            g.now = 0.0
            g.scene = SceneFadeIn()


class g:
    scene = ScenePressAnyKey()
    first_tick = 0
    now = 0.0
    keys = set()


# g.first_tick = pygame.time.get_ticks()
# g.scene = SceneIntro()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            g.keys.add(f'mouse{event.button}')

        if event.type == pygame.MOUSEBUTTONUP:
            g.keys.discard(f'mouse{event.button}')

        if event.type == pygame.KEYDOWN:
            g.keys.add(event.key)

        if event.type == pygame.KEYUP:
            g.keys.discard(event.key)

    g.now = (pygame.time.get_ticks() - g.first_tick) / 1000.0

    ctx.new_frame()
    image.clear()
    depth.clear()

    g.scene.render()

    image.blit()
    ctx.end_frame()

    pygame.display.flip()
