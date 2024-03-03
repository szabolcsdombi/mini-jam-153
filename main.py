import random
import math
import os
import struct
import sys

import pygame
import zengl

import vmath
import sounds
from mesh import make_mesh
from shade import make_shade
from water import make_water
from particles import Particles
from smoke import Smoke

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

particles = Particles(uniform_buffer, 'assets/particle.bin', [image, depth])
smoke = Smoke(uniform_buffer, 'assets/particle.bin', [image, depth])

eye = (6.4, 0.0, 3.5)
light = (3.0, 4.0, 30.0)

def load_texture(name):
    img = pygame.image.load(name)
    pixels = pygame.image.tobytes(img, 'RGBA', True)
    return ctx.image(img.get_size(), 'rgba8unorm', pixels)

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


press_any_key = load_texture('assets/press-any-key.png')
game_over = load_texture('assets/game-over.png')
you_win = load_texture('assets/you-win.png')


class WaveSound:
    def __init__(self):
        self.wave_played = False

    def update(self):
        if math.sin(g.now) > -0.4 and not self.wave_played:
            sounds.wave.play()
            self.wave_played = True

        if math.sin(g.now) < -0.8:
            self.wave_played = False


wave = WaveSound()


class Fishes:
    def __init__(self):
        self.fishes = [
            (vmath.rand(-0.5, 0.5), vmath.rand(-0.5, 0.5), vmath.rand(-0.5, 0.5), vmath.rand(-0.5, 0.5))
            for _ in range(10)
        ]
        self.visible_fishes = [False] * 10
        self.rotations = [vmath.random_quaternion() for _ in range(10)]
        self.delta_rotations = [
            vmath.axis_angle(vmath.qtransform(vmath.random_quaternion(), (1.0, 0.0, 0.0)), 0.05)
            for _ in range(10)
        ]

    def render(self):
        self.rotations = [vmath.quatmul(self.delta_rotations[i], self.rotations[i]) for i in range(10)]
        for i in range(10):
            x, y, z, w = self.fishes[i]
            z += math.sin(g.now * 1.0 + w * 6.0) * 6.0
            if not self.visible_fishes[i]:
                if math.sin(g.now * 1.0 + w * 6.0) < -0.8:
                    self.visible_fishes[i] = True
            x, y, z = x * 10.0 - 16.0, y + (i - 4.5) * 3.0, z
            if self.visible_fishes[i]:
                render_model(fish, (x, y, z), self.rotations[i])

    def render_ending(self):
        self.rotations = [vmath.quatmul(self.delta_rotations[i], self.rotations[i]) for i in range(10)]
        for i in range(10):
            x, y, z, w = self.fishes[i]
            z += math.sin(g.now * 1.0 + w * 6.0) * 6.0
            if self.visible_fishes[i]:
                if math.sin(g.now * 1.0 + w * 6.0) < -0.8:
                    self.visible_fishes[i] = False
            x, y, z = x * 10.0 - 16.0, y + (i - 4.5) * 3.0, z
            if self.visible_fishes[i]:
                render_model(fish, (x, y, z), self.rotations[i])


class SceneFadeOutLoose:
    def __init__(self, fishes):
        self.fishes = fishes
        self.start = g.now

    def render(self):
        elapsed = g.now - self.start

        shade_alpha = smoothstep(elapsed, 0.0, 3.0)

        camera_target = (5.68, 0.0, 2.9 + 0.55)
        update_camera(camera_target, fov=50.0)

        sand.render()
        self.fishes.render_ending()
        render_water()

        shade.uniforms['Color'][:] = struct.pack('4f', 0.0, 0.0, 0.0, shade_alpha)
        shade.render()

        if elapsed > 3.0:
            w, h = image.size
            game_over.blit(image, ((w - 600) // 2, (h - 400) // 2))

        if elapsed > 4.0:
            if len(g.keys) > 0:
                g.first_tick = pygame.time.get_ticks()
                g.now = 0.0
                g.scene = SceneFadeIn()


class SceneFadeOutWin:
    def __init__(self, fishes):
        self.fishes = fishes
        self.start = g.now

    def render(self):
        elapsed = g.now - self.start

        shade_alpha = smoothstep(elapsed, 0.0, 1.0)

        camera_target = (5.68, 0.0, 2.9 + 0.55)
        update_camera(camera_target, fov=50.0)

        sand.render()
        self.fishes.render_ending()
        render_water()

        shade.uniforms['Color'][:] = struct.pack('4f', 0.0, 0.0, 0.0, shade_alpha)
        shade.render()

        if elapsed > 3.0:
            w, h = image.size
            you_win.blit(image, ((w - 600) // 2, (h - 400) // 2))

        if elapsed > 4.0:
            if len(g.keys) > 0:
                g.first_tick = pygame.time.get_ticks()
                g.now = 0.0
                g.scene = SceneFadeIn()


class ScenePlay:
    def __init__(self):
        pygame.mixer.music.play()
        self.fishes = Fishes()
        self.start = g.now
        self.shot = False
        self.hits = 0

    def render(self):
        elapsed = g.now - self.start
        mouse = pygame.mouse.get_pos()
        mx = mouse[0] / size[0] * 2.0 - 1.0
        my = 1.0 - mouse[1] / size[1] * 2.0
        camera_target = (5.68, 0.0, 2.9 + 0.55)
        gun_position = (5.96, 0.38, 3.25)
        gun_rotation = vmath.quatmul(vmath.rz(-mx * 0.65), vmath.ry(my * 0.5))
        update_camera(camera_target, fov=50.0)
        sand.render()
        render_model(shotgun, gun_position, gun_rotation)
        if self.hits > 99:
            self.fishes.render_ending()
        else:
            self.fishes.render()
        particles.update()
        smoke.update()
        particles.render()
        smoke.render()
        render_water()

        if elapsed > 60.0 or (self.hits >= 100 and not any(self.fishes.visible_fishes)):
            if self.hits >= 100:
                g.scene = SceneFadeOutWin(self.fishes)
            else:
                g.scene = SceneFadeOutLoose(self.fishes)

        if 'mouse1' in g.keys and not self.shot:
            self.shot = True
            sounds.shooting.play()
            aspect = size[0] / size[1]
            a, b = vmath.unproject(eye, camera_target, aspect=aspect, fov=50.0, x=mx, y=my)
            x, y, z = gun_position
            smoke_position = list(vmath.add(gun_position, vmath.qtransform(gun_rotation, (-0.5, 0.0, 0.05))))
            smoke_direction = vmath.qtransform(gun_rotation, (-0.2, 0.0, 0.0))

            for _ in range(30):
                velocity = list(vmath.qtransform(vmath.random_quaternion(), (vmath.rand(0.02, 0.023), 0.0, 0.0)))
                velocity = vmath.add(velocity, smoke_direction)
                smoke.add(smoke_position, velocity, vmath.random_quaternion(), vmath.rand(0.1, 0.2), (0.5, 0.5, 0.5), random.randint(10, 14))

            hit = False
            for i in range(10):
                if not self.fishes.visible_fishes[i]:
                    continue
                x, y, z, w = self.fishes.fishes[i]
                z += math.sin(g.now * 1.0 + w * 6.0) * 6.0
                x, y, z = x * 10.0 - 16.0, y + (i - 4.5) * 3.0, z
                if vmath.point_line_distance((x, y, z), a, b) < 2.0:
                    hit = True
                    for _ in range(100):
                        rotation = vmath.random_quaternion()
                        scale = vmath.rand(0.5, 1.0)
                        velocity = list(vmath.qtransform(vmath.random_quaternion(), (vmath.rand(0.03, 0.12), 0.0, 0.0)))
                        velocity[2] += 0.1
                        particles.add([x, y, z], velocity, rotation, scale, (0.8, 0.0, 0.0))
                    x, y, z = vmath.rand(-0.5, 0.5), vmath.rand(-0.5, 0.5), vmath.rand(-0.5, 0.5)
                    w = vmath.rand(-0.1, 0.1) - (g.now * 1.0 + math.pi / 2.0) / 6.0
                    self.fishes.fishes[i] = x, y, z, w
                    self.fishes.rotations[i] = vmath.random_quaternion()

            if hit:
                self.hits += 1
                if self.hits == 1:
                    sounds.fishing.play()

                if self.hits == 10:
                    sounds.red_sea.play()

                if self.hits == 20:
                    sounds.reload.play()

                if self.hits == 30:
                    sounds.hobby.play()

                if self.hits == 40:
                    sounds.feeding_fish.play()

                if self.hits == 55:
                    sounds.endangered.play()

                if self.hits == 65:
                    sounds.not_fair.play()

                if self.hits == 75:
                    sounds.fisherman.play()

                if self.hits == 85:
                    sounds.new_specie.play()

                if self.hits == 99:
                    sounds.i_am_out.play()

                if self.hits == 105:
                    sounds.come_back.play()

        if 'mouse1' not in g.keys:
            self.shot = False


class SceneIntro:
    def __init__(self):
        self.start = g.now
        self.voice_sign = sounds.sign
        self.voice_fish_music = sounds.fish_music

    def render(self):
        elapsed = g.now - self.start
        wave.update()

        if elapsed > 9.0 and self.voice_sign:
            self.voice_sign.play()
            self.voice_sign = None

        if elapsed > 13.0 and self.voice_fish_music:
            self.voice_fish_music.play()
            self.voice_fish_music = None

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
        wave.update()

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
            pygame.mixer.music.stop()
            pygame.mixer.music.rewind()
            g.scene = SceneIntro()


class ScenePressAnyKey:
    def render(self):
        w, h = image.size
        press_any_key.blit(image, ((w - 600) // 2, (h - 400) // 2))

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
# g.scene = ScenePlay()


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
