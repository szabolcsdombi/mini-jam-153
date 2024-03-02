#version 330 core

layout (std140) uniform Common {
    mat4 camera_matrix;
    vec4 camera_position;
    vec4 light_position;
};

layout (location = 0) in vec3 in_vertex;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;

out vec3 v_vertex;
out vec3 v_normal;
out vec3 v_color;

void main() {
    gl_Position = camera_matrix * vec4(in_vertex, 1.0);
    v_vertex = in_vertex;
    v_normal = in_normal;
    v_color = in_color;
}
