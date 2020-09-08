#if 0
void node_rdp_tile_old
(
	in vec3 uv_in,

	in float norm_u,
	in float norm_v,
	in float sl_,
	in float tl_,
	in float sh_,
	in float th_,
	in float mask_s_,
	in float mask_t_,
	in float shift_s_,
	in float shift_t_,
	in float cm_s_,
	in float cm_t_,

	out vec3 uv_out
)
{
	if (norm_u < 1.0)
	{
		norm_u = 1.0;
	}
	if (norm_v < 1.0)
	{
		norm_v = 1.0;
	}

	int sl = (int(sl_ * float(1 << 2)) << 3) & 0xFFFF;
	int tl = (int(tl_ * float(1 << 2)) << 3) & 0xFFFF;
	int sh = (int(sh_ * float(1 << 2)) << 3) & 0xFFFF;
	int th = (int(th_ * float(1 << 2)) << 3) & 0xFFFF;
	int mask_s = int(mask_s_) & 0xF;
	int mask_t = int(mask_t_) & 0xF;
	int shift_s = int(shift_s_) & 0xF;
	int shift_t = int(shift_t_) & 0xF;
	bool mirror_s = bool(int(cm_s_) & 0x1);
	bool mirror_t = bool(int(cm_t_) & 0x1);
	bool clamp_s = bool(int(cm_s_) & 0x2);
	bool clamp_t = bool(int(cm_t_) & 0x2);

	int s = int(uv_in.x * float(1 << 2 << 3) * norm_u);
	int t = int((1.0 - uv_in.y) * float(1 << 2 << 3) * norm_v);

	if (shift_s > 10)
	{
		s = s << (16 - shift_s);
	}
	else
	{
		s = s >> shift_s;
	}
	s = s - sl;
	sh = sh - sl;
	if (mask_s == 0 || clamp_s)
	{
		if (s < 0)
		{
			s = 0;
		}
		else if (s > sh)
		{
			s = sh;
		}
	}
	if (mask_s != 0)
	{
		int mirror_bit = (1 << 2 << 3) << mask_s;
		int mask_value = mirror_bit - 1;
		if (mirror_s && (s & mirror_bit) != 0)
		{
			s = ~s;
		}
		s = s & mask_value;
	}

	if (shift_t > 10)
	{
		t = t << (16 - shift_t);
	}
	else
	{
		t = t >> shift_t;
	}
	t = t - tl;
	th = th - tl;
	if (mask_t == 0 || clamp_t)
	{
		if (t < 0)
		{
			t = 0;
		}
		else if (t > th)
		{
			t = th;
		}
	}
	if (mask_t != 0)
	{
		int mirror_bit = (1 << 2 << 3) << mask_t;
		int mask_value = mirror_bit - 1;
		if (mirror_t && (t & mirror_bit) != 0)
		{
			t = ~t;
		}
		t = t & mask_value;
	}

	uv_out.x = float(s) / float(1 << 2 << 3) / norm_u;
	uv_out.y = 1.0 - float(t) / float(1 << 2 << 3) / norm_v;
	uv_out.z = uv_in.z;
}
#endif

#define safe_color(a) (clamp(a, -65520.0, 65520.0))

void node_rdp_tile
(
	in vec3 uv,

	in sampler2D ima,
	in float sl,
	in float tl,
	in float sh,
	in float th,
	in float mask_s,
	in float mask_t,
	in float shift_s,
	in float shift_t,
	in float cm_s,
	in float cm_t,

	out vec4 color,
	out float alpha
)
{
	vec2 tex_size = vec2(textureSize(ima, 0).xy);

	bool mirror_s = bool(int(cm_s) & 0x1);
	bool mirror_t = bool(int(cm_t) & 0x1);
	bool clamp_s = bool(int(cm_s) & 0x2);
	bool clamp_t = bool(int(cm_t) & 0x2);

	uv.y = 1.0 - uv.y;
	uv.xy *= tex_size;

	vec2 lo = vec2(sl, tl);
	vec2 hi = vec2(sh, th);

	if (shift_s > 10.0)
	{
		uv.x *= pow(2.0, 16.0 - shift_s);
	}
	else
	{
		uv.x /= pow(2.0, shift_s);
	}
	if (shift_t > 10.0)
	{
		uv.y *= pow(2.0, 16.0 - shift_t);
	}
	else
	{
		uv.y /= pow(2.0, shift_t);
	}
	uv.xz -= lo;
	hi -= lo;

	vec4 st = vec4(floor(uv.xy), ceil(uv.xy));

	if (mask_s == 0.0 || clamp_s)
	{
		st.xz = clamp(st.xz, 0.0, hi.x);
	}
	if (mask_s != 0.0)
	{
		float d = pow(2.0, mask_s);
		vec2 q = floor(st.xz / d);
		st.xz -= q.xy * d;
		if (mirror_s)
		{
			vec2 c = mod(q, 2.0);
			if (c.x != 0.0)
			{
				st.x = d - st.x;
			}
			if (c.y != 0.0)
			{
				st.z = d - st.z;
			}
		}
	}

	if (mask_t == 0.0 || clamp_t)
	{
		st.yw = clamp(st.yw, 0.0, hi.y);
	}
	if (mask_t != 0.0)
	{
		float d = pow(2.0, mask_t);
		vec2 q = floor(st.yw / d);
		st.yw -= q.xy * d;
		if (mirror_t)
		{
			vec2 c = mod(q, 2.0);
			if (c.x != 0.0)
			{
				st.y = d - st.y;
			}
			if (c.y != 0.0)
			{
				st.w = d - st.w;
			}
		}
	}

	st.yw = tex_size.y - 1.0 - st.yw;

	vec2 s1 = fract(uv.xy);
	vec2 s0 = 1.0 - s1;
	color = safe_color(texelFetch(ima, ivec2(st.xy), 0)) * s0.x * s0.y;
	color += safe_color(texelFetch(ima, ivec2(st.zy), 0)) * s1.x * s0.y;
	color += safe_color(texelFetch(ima, ivec2(st.xw), 0)) * s0.x * s1.y;
	color += safe_color(texelFetch(ima, ivec2(st.zw), 0)) * s1.x * s1.y;
	alpha = color.a;
}
