#version 330 core

layout (std140) uniform Common {
    mat4 camera_matrix;
    vec4 camera_position;
    vec4 light_position;
};

layout (location = 0) in vec3 in_vertex;
layout (location = 1) in vec3 in_normal;

layout (location = 2) in vec3 in_position;
layout (location = 3) in vec4 in_rotation;
layout (location = 4) in float in_scale;
layout (location = 5) in vec3 in_color;

out vec3 v_vertex;
out vec3 v_normal;
out vec3 v_color;

vec3 qtransform(vec4 q, vec3 v) {
    return v + 2.0 * cross(cross(v, q.xyz) - q.w * v, q.xyz);
}

void main() {
    v_vertex = in_position + qtransform(in_rotation, in_vertex * in_scale);
    v_normal = qtransform(in_rotation, in_normal);
    v_color = in_color;
    gl_Position = camera_matrix * vec4(v_vertex, 1.0);
}
