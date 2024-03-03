#version 330 core

vec2 vertices[3] = vec2[](
    vec2(-1.0, -1.0),
    vec2(3.0, -1.0),
    vec2(-1.0, 3.0)
);

out vec2 v_vertex;

void main() {
    v_vertex = vertices[gl_VertexID];
    gl_Position = vec4(v_vertex, 0.0, 1.0);
}
