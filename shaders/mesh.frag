#version 330 core

layout (std140) uniform Common {
    mat4 camera_matrix;
    vec4 camera_position;
    vec4 light_position;
};

in vec3 v_vertex;
in vec3 v_normal;
in vec3 v_color;

layout (location = 0) out vec4 out_color;

void main() {
    vec3 light_direction = normalize(light_position.xyz - v_vertex);
    float lum = clamp(dot(light_direction, normalize(v_normal)), 0.0, 1.0);
    lum = lum * 0.3 + 0.7;
    vec3 color = v_color;
    out_color = vec4(color * lum, 1.0);
    out_color.rgb = pow(out_color.rgb, vec3(1.0 / 2.2));
}
