# 4I2V Camera Motion + Consistency Guide

This repo now includes a **high-level wrapper script** so you can keep the existing `4I2V Flow` as-is and generate 2-frame transition jobs from simple inputs.

## High-level entrypoint

Use `build_4i2v_segment_workflow.py` with:
- `start-image`
- `end-image`
- `motion` (`zoom`, `rotate_left`, `rotate_right`, `up`, `down`)
- `quality` (`sample`, `full`)

Example:

```bash
python build_4i2v_segment_workflow.py \
  --start-image frames/0001.png \
  --end-image frames/0002.png \
  --motion rotate_left \
  --quality sample \
  --output generated/segment_0001_0002_sample.json
```

Then load `generated/segment_0001_0002_sample.json` in ComfyUI and run it.

---

## What the wrapper changes in the base flow

- Sets the 4 image slots used by IPAdapter stack to represent a 2-frame transition:
  - start/start/end/end
- Sets motion guidance video (`VHS_LoadVideoPath` node)
- Applies motion-specific defaults:
  - ControlNet strength/end range
  - AnimateDiff motion scale
- Switches output mode by quality:
  - `sample`: enables preview output only
  - `full`: enables final output only

---

## Motion presets (defaults)

- `zoom`: stronger radial push/pull
- `rotate_left` / `rotate_right`: lateral perspective shift
- `up` / `down`: tilt-like motion

If you want custom mask videos, use `--motion-video` to override the preset path/URL.

---

## Building longer videos from many photos

For a sequence of photos:
1. Generate one segment workflow per adjacent pair.
2. Run each segment.
3. Concatenate resulting clips with ffmpeg.

This keeps the process modular, testable, and scalable.
