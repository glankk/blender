/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup shdnodes
 */

#include "node_shader_util.h"

static bNodeSocketTemplate sh_node_rdp_tile_in[] =
{
  {SOCK_VECTOR, 1, N_("Vector"), .flag = SOCK_HIDE_VALUE},
  {-1, 0, ""},
};

static bNodeSocketTemplate sh_node_rdp_tile_out[] =
{
  {SOCK_RGBA, 0, N_("Color"), .flag = SOCK_NO_INTERNAL_LINK},
  {SOCK_FLOAT, 0, N_("Alpha"), .flag = SOCK_NO_INTERNAL_LINK},
  {-1, 0, ""},
};

static void node_shader_init_rdp_tile(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeRDPTile *tile = MEM_callocN(sizeof(NodeRDPTile), "NodeRDPTile");
  BKE_imageuser_default(&tile->iuser);
  tile->sh = 1023.75f;
  tile->th = 1023.75f;
  node->storage = tile;
}

static int gpu_shader_rdp_tile(GPUMaterial *mat,
                               bNode *node,
                               bNodeExecData *UNUSED(execdata),
                               GPUNodeStack *in,
                               GPUNodeStack *out)
{
  Image *ima = (Image *)node->id;
  if (!ima)
    return GPU_stack_link(mat, node, "node_tex_image_empty", in, out);

  NodeRDPTile *tile = node->storage;

  bNode *node_original = node->original ? node->original : node;
  NodeRDPTile *tile_original = node_original->storage;
  ImageUser *iuser = &tile_original->iuser;

  float sl = tile->sl;
  float tl = tile->tl;
  float sh = tile->sh;
  float th = tile->th;
  float mask_s = tile->mask_s;
  float mask_t = tile->mask_t;
  float shift_s = tile->shift_s;
  float shift_t = tile->shift_t;
  float cm_s = tile->cm_s;
  float cm_t = tile->cm_t;

  GPU_stack_link(mat, node, "node_rdp_tile", in, out,
                 GPU_image(ima, iuser),
                 GPU_constant(&sl), GPU_constant(&tl),
                 GPU_constant(&sh), GPU_constant(&th),
                 GPU_constant(&mask_s), GPU_constant(&mask_t),
                 GPU_constant(&shift_s), GPU_constant(&shift_t),
                 GPU_constant(&cm_s), GPU_constant(&cm_t));

  if (out[0].hasoutput) {
    if (ima->alpha_mode == IMA_ALPHA_IGNORE ||
        ima->alpha_mode == IMA_ALPHA_CHANNEL_PACKED ||
        IMB_colormanagement_space_name_is_data(ima->colorspace_settings.name))
    {
      GPU_link(mat, "color_alpha_clear", out[0].link, &out[0].link);
    }
    else {
      if (ima->alpha_mode == IMA_ALPHA_PREMUL) {
        if (out[1].hasoutput)
          GPU_link(mat, "color_alpha_unpremultiply", out[0].link, &out[0].link);
        else
          GPU_link(mat, "color_alpha_clear", out[0].link, &out[0].link);
      }
      else {
        if (out[1].hasoutput)
          GPU_link(mat, "color_alpha_clear", out[0].link, &out[0].link);
        else
          GPU_link(mat, "color_alpha_premultiply", out[0].link, &out[0].link);
      }
    }
  }

  return true;
}

void register_node_type_sh_rdp_tile(void)
{
  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_RDP_TILE, "RDP Tile", NODE_CLASS_TEXTURE, 0);
  node_type_socket_templates(&ntype, sh_node_rdp_tile_in, sh_node_rdp_tile_out);
  node_type_init(&ntype, node_shader_init_rdp_tile);
  node_type_storage(&ntype, "NodeRDPTile", node_free_standard_storage, node_copy_standard_storage);
  node_type_gpu(&ntype, gpu_shader_rdp_tile);
  node_type_label(&ntype, node_image_label);
  node_type_size_preset(&ntype, NODE_SIZE_LARGE);

  nodeRegisterType(&ntype);
}
