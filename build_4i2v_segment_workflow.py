#!/usr/bin/env python3
"""Generate a 2-frame 4I2V workflow from the base `4I2V Flow` graph.

This is a high-level wrapper that sets:
- start frame image
- end frame image
- camera motion preset
- quality mode (sample/full)

The generated workflow can be loaded directly in ComfyUI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BASE_WORKFLOW = "4I2V Flow"

# Node ids in the base graph
LOAD_IMAGE_START_IDS = (142, 135)
LOAD_IMAGE_END_IDS = (680, 683)
MOTION_VIDEO_NODE_ID = 568
CONTROLNET_APPLY_NODE_ID = 125
MOTION_SCALE_NODE_ID = 256
VIDEO_PREVIEW_NODE_ID = 53
VIDEO_FINAL_NODE_ID = 205
VIDEO_INTERPOLATED_NODE_ID = 219
VIDEO_UPSCALED_MODEL_NODE_ID = 272

MOTION_PRESETS = {
    "zoom": {
        "video": "motions/zoom.mp4",
        "controlnet_strength": 0.55,
        "controlnet_end": 0.45,
        "motion_scale": 1.15,
    },
    "rotate_left": {
        "video": "motions/rotate_left.mp4",
        "controlnet_strength": 0.60,
        "controlnet_end": 0.55,
        "motion_scale": 1.12,
    },
    "rotate_right": {
        "video": "motions/rotate_right.mp4",
        "controlnet_strength": 0.60,
        "controlnet_end": 0.55,
        "motion_scale": 1.12,
    },
    "up": {
        "video": "motions/tilt_up.mp4",
        "controlnet_strength": 0.60,
        "controlnet_end": 0.55,
        "motion_scale": 1.10,
    },
    "down": {
        "video": "motions/tilt_down.mp4",
        "controlnet_strength": 0.60,
        "controlnet_end": 0.55,
        "motion_scale": 1.10,
    },
}


def find_node(nodes: list[dict[str, Any]], node_id: int) -> dict[str, Any]:
    for node in nodes:
        if node.get("id") == node_id:
            return node
    raise ValueError(f"Node id {node_id} not found in workflow")


def set_load_image(nodes: list[dict[str, Any]], node_id: int, image_path: str) -> None:
    node = find_node(nodes, node_id)
    widgets = node.setdefault("widgets_values", ["", "image"])
    if not widgets:
        widgets.extend(["", "image"])
    widgets[0] = image_path
    if len(widgets) == 1:
        widgets.append("image")


def set_motion_settings(nodes: list[dict[str, Any]], motion: str, override_video: str | None) -> None:
    preset = MOTION_PRESETS[motion]

    video_node = find_node(nodes, MOTION_VIDEO_NODE_ID)
    widgets = video_node.setdefault("widgets_values", {})
    video_value = override_video if override_video else preset["video"]
    widgets["video"] = video_value
    if isinstance(widgets.get("videopreview"), dict):
        params = widgets["videopreview"].setdefault("params", {})
        params["filename"] = video_value

    controlnet_node = find_node(nodes, CONTROLNET_APPLY_NODE_ID)
    cn_widgets = controlnet_node.setdefault("widgets_values", [0.45, 0, 0.35])
    cn_widgets[0] = preset["controlnet_strength"]
    if len(cn_widgets) < 3:
        while len(cn_widgets) < 3:
            cn_widgets.append(0)
    cn_widgets[2] = preset["controlnet_end"]

    motion_node = find_node(nodes, MOTION_SCALE_NODE_ID)
    motion_widgets = motion_node.setdefault("widgets_values", [1.0])
    motion_widgets[0] = preset["motion_scale"]


def set_quality(nodes: list[dict[str, Any]], quality: str) -> None:
    # mode 0 = enabled, mode 2 = bypass (as used in the existing graph)
    preview = find_node(nodes, VIDEO_PREVIEW_NODE_ID)
    final = find_node(nodes, VIDEO_FINAL_NODE_ID)
    interp = find_node(nodes, VIDEO_INTERPOLATED_NODE_ID)
    upscaled_model = find_node(nodes, VIDEO_UPSCALED_MODEL_NODE_ID)

    if quality == "sample":
        preview["mode"] = 0
        final["mode"] = 2
        interp["mode"] = 2
        upscaled_model["mode"] = 2
    else:  # full
        preview["mode"] = 2
        final["mode"] = 0
        interp["mode"] = 2
        upscaled_model["mode"] = 2


def set_output_prefix(nodes: list[dict[str, Any]], motion: str, quality: str) -> None:
    suffix = f"{motion}_{quality}"
    for node_id in (VIDEO_PREVIEW_NODE_ID, VIDEO_FINAL_NODE_ID):
        node = find_node(nodes, node_id)
        widgets = node.get("widgets_values", {})
        if isinstance(widgets, dict):
            widgets["filename_prefix"] = f"%date:yyyy-MM-dd%/{quality}/{suffix}/AD"


def build_workflow(
    base_workflow_path: Path,
    start_image: str,
    end_image: str,
    motion: str,
    quality: str,
    motion_video: str | None,
) -> dict[str, Any]:
    data = json.loads(base_workflow_path.read_text(encoding="utf-8"))
    nodes = data["nodes"]

    for node_id in LOAD_IMAGE_START_IDS:
        set_load_image(nodes, node_id, start_image)
    for node_id in LOAD_IMAGE_END_IDS:
        set_load_image(nodes, node_id, end_image)

    set_motion_settings(nodes, motion, motion_video)
    set_quality(nodes, quality)
    set_output_prefix(nodes, motion, quality)
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-image", required=True)
    parser.add_argument("--end-image", required=True)
    parser.add_argument("--motion", choices=sorted(MOTION_PRESETS), required=True)
    parser.add_argument("--quality", choices=["sample", "full"], default="sample")
    parser.add_argument("--motion-video", default=None, help="Override motion video path/URL")
    parser.add_argument("--base-workflow", default=BASE_WORKFLOW)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workflow = build_workflow(
        base_workflow_path=Path(args.base_workflow),
        start_image=args.start_image,
        end_image=args.end_image,
        motion=args.motion,
        quality=args.quality,
        motion_video=args.motion_video,
    )
    Path(args.output).write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    print(f"Generated workflow: {args.output}")


if __name__ == "__main__":
    main()
