#version 330 core

layout (std140) uniform Common {
    mat4 camera_matrix;
    vec4 camera_position;
    vec4 light_position;
};

uniform vec3 Position;
uniform vec4 Rotation;

layout (location = 0) in vec3 in_vertex;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;

out vec3 v_vertex;
out vec3 v_normal;
out vec3 v_color;

vec3 qtransform(vec4 q, vec3 v) {
    return v + 2.0 * cross(cross(v, q.xyz) - q.w * v, q.xyz);
}

void main() {
    v_vertex = Position + qtransform(Rotation, in_vertex);
    v_normal = qtransform(Rotation, in_normal);
    v_color = in_color;
    gl_Position = camera_matrix * vec4(v_vertex, 1.0);
}
