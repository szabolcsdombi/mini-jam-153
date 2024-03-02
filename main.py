import itertools
import math
import os
import struct
import sys

import pygame
import zengl

from mesh import make_mesh
from water import make_water

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
start = make_mesh(uniform_buffer, 'assets/start.bin', [image, depth])
sign = make_mesh(uniform_buffer, 'assets/sign.bin', [image, depth])
fish = make_mesh(uniform_buffer, 'assets/fish.bin', [image, depth])
shotgun = make_mesh(uniform_buffer, 'assets/shotgun.bin', [image, depth])

eye = (6.4, 0.0, 3.5)
light = (3.0, 4.0, 30.0)

def update_camera(target, fov):
    aspect = size[0] / size[1]
    camera = zengl.camera(eye, target, aspect=aspect, fov=fov)
    uniform_buffer.write(struct.pack('64s3f4x3f4x', camera, *eye, *light))

def render_water():
    water.uniforms['Time'][:] = struct.pack('f', now)
    water.uniforms['WaterLevel'][:] = struct.pack('f', 1.0 + math.sin(now) * 0.5)
    water.render()

def scene1():
    update_camera((5.68, 0.0, 2.9), fov=45.0)
    sand.render()
    start.render()
    render_water()

def scene2():
    update_camera((5.55, -0.31, 3.32), fov=45.0)
    sand.render()
    sign.render()
    render_water()

def scene3():
    update_camera((5.5, 0.0, 3.4), fov=50.0)
    sand.render()
    shotgun.render()
    fish.render()
    render_water()

scenes = itertools.cycle([scene1, scene2, scene3])
scene = next(scenes)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                scene = next(scenes)

    now = pygame.time.get_ticks() / 1000.0

    ctx.new_frame()
    image.clear()
    depth.clear()

    scene()

    image.blit()
    ctx.end_frame()

    pygame.display.flip()
