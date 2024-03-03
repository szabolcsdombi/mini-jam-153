#version 330 core

layout (std140) uniform Common {
    mat4 camera_matrix;
    vec4 camera_position;
    vec4 light_position;
};

in vec2 v_vertex;

uniform sampler2D Depth;

layout (location = 0) out vec4 out_color;

uniform float Time;
uniform float WaterLevel;

#define DRAG_MULT 0.2
#define WATER_DEPTH 0.5
#define ITERATIONS_RAYMARCH 5
#define ITERATIONS_NORMAL 10

vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);
    float dx = wave * cos(x);
    return vec2(wave, -dx);
}

float get_waves(vec2 position, int iterations) {
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 1.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; ++i) {
        vec2 p = vec2(sin(iter), cos(iter));
        vec2 res = wavedx(position, p, frequency, Time * timeMultiplier);
        position += p * res.y * weight * DRAG_MULT;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight *= 0.82;
        frequency *= 1.18;
        timeMultiplier *= 1.07;
        iter += 1232.399963;
    }
    return sumOfValues / sumOfWeights;
}

float raymarch_water(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < 64; ++i) {
        float height = get_waves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.0002 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);
    }
    return distance(pos, camera);
}

vec3 normal(vec2 pos, float e, float depth) {
    vec2 ex = vec2(e, 0);
    float H = get_waves(pos.xy, ITERATIONS_NORMAL) * depth;
    vec3 a = vec3(pos.x, H, pos.y);
    return normalize(
        cross(
            a - vec3(pos.x - e, get_waves(pos.xy - ex.xy, ITERATIONS_NORMAL) * depth, pos.y),
            a - vec3(pos.x, get_waves(pos.xy + ex.yx, ITERATIONS_NORMAL) * depth, pos.y + e)
        )
    );
}

float intersect_plane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    sundir.y = max(sundir.y, -0.07);
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4), special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002 * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0)) + mymie * suncolor;
}

vec3 sun_direction() {
    return vec3(-0.93068, 0.193892, -0.310227);
}

vec3 get_atmosphere(vec3 dir) {
    return extra_cheap_atmosphere(dir, sun_direction()) * 0.5;
}

float getSun(vec3 dir) {
    return pow(max(0.0, dot(dir, sun_direction())), 720.0) * 210.0;
}

vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(0.59719, 0.07600, 0.02840, 0.35458, 0.90834, 0.13383, 0.04823, 0.01566, 0.83777);
    mat3 m2 = mat3(1.60475, -0.10208, -0.00327, -0.53108, 1.10813, -0.07276, -0.07367, -0.00605, 1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return pow(clamp(m2 * (a / b), 0.0, 1.0), vec3(1.0 / 2.2));
}

vec3 to_scene(vec3 v) {
    return vec3(v.x, v.z, -v.y);
}

vec3 from_scene(vec3 v) {
    return vec3(v.x, -v.z, v.y);
}

void main() {
    float depth_ref = texture(Depth, v_vertex * 0.5 + 0.5).r;
    float cut_alpha = depth_ref > 0.9999 ? 1.0 : 0.0;

    mat4 inv_camera_matrix = inverse(camera_matrix);
    vec4 position_temp = inv_camera_matrix * vec4(v_vertex, -1.0, 1.0);
    vec4 target_temp = inv_camera_matrix * vec4(v_vertex, 1.0, 1.0);
    vec3 position = position_temp.xyz / position_temp.w;
    vec3 target = target_temp.xyz / target_temp.w;
    vec3 direction = normalize(target - position);

    vec3 origin = to_scene(position);
    vec3 ray = to_scene(direction);
    if (ray.y >= 0.0) {
        vec3 C = get_atmosphere(ray) + getSun(ray);
        out_color = vec4(aces_tonemap(C * 2.0), cut_alpha);
        return;
    }
    float water_level_multiplier = smoothstep(-0.1, -0.4, ray.y);
    origin.y -= WaterLevel * water_level_multiplier;
    vec3 waterPlaneHigh = vec3(0.0, 0.0, 0.0);
    vec3 waterPlaneLow = vec3(0.0, -WATER_DEPTH, 0.0);
    float highPlaneHit = intersect_plane(origin, ray, waterPlaneHigh, vec3(0.0, 1.0, 0.0));
    float lowPlaneHit = intersect_plane(origin, ray, waterPlaneLow, vec3(0.0, 1.0, 0.0));
    vec3 highHitPos = origin + ray * highPlaneHit;
    vec3 lowHitPos = origin + ray * lowPlaneHit;
    float dist = raymarch_water(origin, highHitPos, lowHitPos, WATER_DEPTH);
    vec3 waterHitPos = origin + ray * dist;
    vec3 N = normal(waterHitPos.xz, 0.01, WATER_DEPTH);
    N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
    float fresnel = (0.04 + (1.0 - 0.04) * (pow(1.0 - max(0.0, dot(-N, ray)), 5.0)));
    vec3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);
    vec3 reflection = get_atmosphere(R) + getSun(R);
    vec3 scattering = vec3(0.0293, 0.0698, 0.1717) * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);
    vec3 C = fresnel * reflection + (1.0 - fresnel) * scattering;
    out_color = vec4(aces_tonemap(C * 2.0), cut_alpha);

    if (dist > 100.0) {
        return;
    }

    waterHitPos.y += WaterLevel * water_level_multiplier;
    vec3 vertex_position = from_scene(waterHitPos);
    vec4 vertex = camera_matrix * vec4(vertex_position, 1.0);
    float depth = (vertex.z / vertex.w) * 0.5 + 0.5;

    float alpha = smoothstep(0.0, 0.0004, depth_ref - depth);
    alpha *= 1.0 - smoothstep(-3.0, 0.0, vertex_position.x) * 0.5;

    out_color.rgb += vec3(1.0 - smoothstep(0.1, 0.4, alpha)) * 2.0;
    out_color.a = alpha;
}
