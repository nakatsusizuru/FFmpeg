#!/usr/bin/env python3
"""Patch libavcodec/libmpeghdec.c to default to stereo when no channel layout is given."""
import pathlib

p = pathlib.Path('libavcodec/libmpeghdec.c')
text = p.read_text(encoding='utf-8')

old = '''    if (avctx->ch_layout.nb_channels == 0) {
        av_log(avctx, AV_LOG_ERROR, "Channel layout needs to be specified\\n");
        return AVERROR(EINVAL);'''

new = '''    if (avctx->ch_layout.nb_channels == 0) {
        av_log(avctx, AV_LOG_WARNING,
               "No channel layout specified, defaulting to stereo. "
               "Use -ch_layout to override (e.g. -ch_layout 5.1).\\n");
        av_channel_layout_default(&avctx->ch_layout, 2);'''

if old not in text:
    raise SystemExit('patch target not found in libmpeghdec.c')

p.write_text(text.replace(old, new), encoding='utf-8')
print('libmpeghdec.c patched')
