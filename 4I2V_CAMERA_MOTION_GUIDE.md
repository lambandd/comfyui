# 4I2V Camera Motion + Consistency Guide

This workflow is already functional, but if motion feels "floaty"/inconsistent, the best upgrade is to separate **consistency control** from **camera movement control**.

## 1) Improve consistency first

- Keep **IPAdapter weight high** (typically `0.85 - 1.00`) so structure stays locked to source images.
- Keep **CFG low** (`1.0 - 1.5`) to reduce style drift/flicker.
- Start with moderate **motion scale** (`1.05 - 1.25`) and only increase after framing is stable.
- While tuning, randomize seed. Once happy, **fix seed** for repeatability.

## 2) Replace the single ring video with directional camera masks

Your current ring video is great for generic push/pull, but limited for perspective variety. Build/use three loopable grayscale guidance videos and swap based on desired move:

- **Zoom**: radial gradient / expanding rings
- **Rotate up (tilt up)**: vertical flow (bright-to-dark from bottom->top)
- **Rotate left (pan left)**: horizontal flow (bright-to-dark from right->left)

Feed each into the existing `VHS_LoadVideoPath -> VHS_SplitImages -> ControlNet` path.

## 3) Per-photo camera movement (recommended structure)

To pick a unique movement per photo, the most robust approach is:

1. Render each photo as a short clip (8-24 frames) with its own selected mask video.
2. Use the same checkpoint/vae/ipadapter settings across clips.
3. Concatenate clips afterward.

This is more stable than trying to hard-switch movement inside one long denoise pass.

## 4) Suggested ControlNet ranges for movement strength

Use these as starting points in `ACN_AdvancedControlNetApply`:

- **Zoom**: strength `0.50 - 0.60`, end percent `0.40 - 0.50`
- **Rotate up**: strength `0.55 - 0.70`, end percent `0.50 - 0.65`
- **Rotate left**: strength `0.55 - 0.70`, end percent `0.50 - 0.65`

If you see warping: lower strength first, then lower motion scale.

## 5) High-confidence tuning order

1. Lock consistency (IPAdapter, seed, CFG).
2. Tune one camera motion clip at a time.
3. Increase perspective strength gradually.
4. Only then upscale/interpolate.
