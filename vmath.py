import random
from math import sin, cos, sqrt, pi
import numpy as np
import zengl


def quatmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        ax * bw + aw * bx + ay * bz - az * by,
        ay * bw + aw * by + az * bx - ax * bz,
        az * bw + aw * bz + ax * by - ay * bx,
        aw * bw - ax * bx - ay * by - az * bz
    )


def qtransform(q, v):
    rx, ry, rz, rw = q
    x, y, z = v
    return (
        (rw * rw + rx * rx - ry * ry - rz * rz) * x + 2.0 * (rx * ry - rw * rz) * y + 2.0 * (rx * rz + rw * ry) * z,
        2.0 * (rx * ry + rw * rz) * x + (rw * rw - rx * rx + ry * ry - rz * rz) * y + 2.0 * (ry * rz - rw * rx) * z,
        2.0 * (rx * rz - rw * ry) * x + 2.0 * (ry * rz + rw * rx) * y + (rw * rw - rx * rx - ry * ry + rz * rz) * z,
    )


def rx(a):
    return (sin(a * 0.5), 0.0, 0.0, cos(a * 0.5))


def ry(a):
    return (0.0, sin(a * 0.5), 0.0, cos(a * 0.5))


def rz(a):
    return (0.0, 0.0, sin(a * 0.5), cos(a * 0.5))


def add(a, b):
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def axis_angle(axis, angle):
    x, y, z = axis
    s = sin(angle * 0.5)
    c = cos(angle * 0.5)
    return x * s, y * s, z * s, c


def point_line_distance(p, a, b):
    px, py, pz = p
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = bx - ax, by - ay, bz - az
    d = cx * cx + cy * cy + cz * cz
    t = ((px - ax) * cx + (py - ay) * cy + (pz - az) * cz) / d
    ux, uy, uz = px - ax - cx * t, py - ay - cy * t, pz - az - cz * t
    return sqrt(ux * ux + uy * uy + uz * uz)


def random_vector():
    return random.random(), random.random(), random.random()


def random_quaternion():
    u1, u2, u3 = random.random(), random.random(), random.random()
    return (
        sqrt(1.0 - u1) * sin(2.0 * pi * u2),
        sqrt(1.0 - u1) * cos(2.0 * pi * u2),
        sqrt(u1) * sin(2.0 * pi * u3),
        sqrt(u1) * cos(2.0 * pi * u3),
    )


def rand(a, b):
    return random.uniform(a, b)


def unproject(eye, target, aspect, fov, x, y):
    mat = zengl.camera(eye, target, aspect=aspect, fov=fov)
    mat = np.frombuffer(mat, dtype='f4').reshape(4, 4).T
    mat = np.linalg.inv(mat)
    a = mat @ (x, y, -1.0, 1.0)
    b = mat @ (x, y, 1.0, 1.0)
    return tuple(a[:3] / a[3]), tuple(b[:3] / b[3])
