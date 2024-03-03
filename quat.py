from math import sin, cos


def quatmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        ax * bw + aw * bx + ay * bz - az * by,
        ay * bw + aw * by + az * bx - ax * bz,
        az * bw + aw * bz + ax * by - ay * bx,
        aw * bw - ax * bx - ay * by - az * bz
    )


def rx(a):
    return (sin(a * 0.5), 0.0, 0.0, cos(a * 0.5))


def ry(a):
    return (0.0, sin(a * 0.5), 0.0, cos(a * 0.5))


def rz(a):
    return (0.0, 0.0, sin(a * 0.5), cos(a * 0.5))
