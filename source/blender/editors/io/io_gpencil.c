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
 * The Original Code is Copyright (C) 2020 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup editor/io
 */

/* needed for directory lookup */
#ifndef WIN32
#  include <dirent.h>
#else
#  include "BLI_winstuff.h"
#endif

#include <errno.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_report.h"

#include "BLI_listbase.h"
#include "BLI_math_vector.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "ED_object.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "WM_api.h"
#include "WM_types.h"

#include "io_gpencil.h"

#include "gpencil_io_exporter.h"

static int wm_gpencil_export_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  UNUSED_VARS(event);

  // if (!RNA_struct_property_is_set(op->ptr, "as_background_job")) {
  //  RNA_boolean_set(op->ptr, "as_background_job", true);
  //}

  RNA_boolean_set(op->ptr, "init_scene_frame_range", true);

  if (!RNA_struct_property_is_set(op->ptr, "filepath")) {
    Main *bmain = CTX_data_main(C);
    char filepath[FILE_MAX];

    if (BKE_main_blendfile_path(bmain)[0] == '\0') {
      BLI_strncpy(filepath, "untitled", sizeof(filepath));
    }
    else {
      BLI_strncpy(filepath, BKE_main_blendfile_path(bmain), sizeof(filepath));
    }

    BLI_path_extension_replace(filepath, sizeof(filepath), ".svg");
    RNA_string_set(op->ptr, "filepath", filepath);
  }

  WM_event_add_fileselect(C, op);

  return OPERATOR_RUNNING_MODAL;
}

static int wm_gpencil_export_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);

  if (!RNA_struct_property_is_set(op->ptr, "filepath")) {
    BKE_report(op->reports, RPT_ERROR, "No filename given");
    return OPERATOR_CANCELLED;
  }

  char filename[FILE_MAX];
  RNA_string_get(op->ptr, "filepath", filename);
  Object *ob = CTX_data_active_object(C);

  struct GpencilExportParams params = {
      .frame_start = (params.frame_start == INT_MIN) ? SFRA : RNA_int_get(op->ptr, "start"),
      .frame_end = (params.frame_end == INT_MIN) ? EFRA : RNA_int_get(op->ptr, "end"),
      .ob = ob,
  };

  gpencil_io_export(C, filename, &params);

  return OPERATOR_FINISHED;
}

static void ui_gpencil_export_settings(uiLayout *layout, PointerRNA *imfptr)
{

  uiLayout *box, *row, *col, *sub;

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  box = uiLayoutBox(layout);
  row = uiLayoutRow(box, false);
  uiItemL(row, IFACE_("Scene Options"), ICON_SCENE_DATA);

  col = uiLayoutColumn(box, false);

  sub = uiLayoutColumn(col, true);
  uiItemR(sub, imfptr, "start", 0, IFACE_("Frame Start"), ICON_NONE);
  uiItemR(sub, imfptr, "end", 0, IFACE_("End"), ICON_NONE);
}

static void wm_gpencil_export_draw(bContext *C, wmOperator *op)
{

  PointerRNA ptr;

  RNA_pointer_create(NULL, op->type->srna, op->properties, &ptr);

  /* Conveniently set start and end frame to match the scene's frame range. */
  Scene *scene = CTX_data_scene(C);

  if (scene != NULL && RNA_boolean_get(&ptr, "init_scene_frame_range")) {
    RNA_int_set(&ptr, "start", SFRA);
    RNA_int_set(&ptr, "end", EFRA);

    RNA_boolean_set(&ptr, "init_scene_frame_range", false);
  }

  ui_gpencil_export_settings(op->layout, &ptr);
}

static bool wm_gpencil_export_check(bContext *UNUSED(C), wmOperator *op)
{

  char filepath[FILE_MAX];
  RNA_string_get(op->ptr, "filepath", filepath);

  if (!BLI_path_extension_check(filepath, ".svg")) {
    BLI_path_extension_ensure(filepath, FILE_MAX, ".svg");
    RNA_string_set(op->ptr, "filepath", filepath);
    return true;
  }

  return false;
}

bool wm_gpencil_export_poll(bContext *C)
{
  if (CTX_wm_window(C) == NULL) {
    // TODO: Add GPencil check/layer, etc.
    return false;
  }

  return true;
}

void WM_OT_gpencil_export(wmOperatorType *ot)
{
  ot->name = "Export Grease Pencil";
  ot->description = "Export current grease pencil";
  ot->idname = "WM_OT_gpencil_export";

  ot->invoke = wm_gpencil_export_invoke;
  ot->exec = wm_gpencil_export_exec;
  ot->poll = wm_gpencil_export_poll;
  ot->ui = wm_gpencil_export_draw;
  ot->check = wm_gpencil_export_check;

  WM_operator_properties_filesel(ot,
                                 FILE_TYPE_FOLDER | FILE_TYPE_ALEMBIC,
                                 FILE_BLENDER,
                                 FILE_SAVE,
                                 WM_FILESEL_FILEPATH | WM_FILESEL_SHOW_PROPS,
                                 FILE_DEFAULTDISPLAY,
                                 FILE_SORT_ALPHA);

  RNA_def_int(ot->srna,
              "start",
              INT_MIN,
              INT_MIN,
              INT_MAX,
              "Start Frame",
              "Start frame of the export, use the default value to "
              "take the start frame of the current scene",
              INT_MIN,
              INT_MAX);

  RNA_def_int(ot->srna,
              "end",
              INT_MIN,
              INT_MIN,
              INT_MAX,
              "End Frame",
              "End frame of the export, use the default value to "
              "take the end frame of the current scene",
              INT_MIN,
              INT_MAX);

  /* This dummy prop is used to check whether we need to init the start and
   * end frame values to that of the scene's, otherwise they are reset at
   * every change, draw update. */
  RNA_def_boolean(ot->srna, "init_scene_frame_range", false, "", "");
}
