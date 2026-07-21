#!/usr/bin/env python3
"""Patch libavcodec/libmpeghdec.c to support 360RA decoding."""
import pathlib

p = pathlib.Path('libavcodec/libmpeghdec.c')
text = p.read_text(encoding='utf-8')

# 1. Make channel_layout_to_cicp accept layouts that contain the same channels
#    even if the order differs from FFmpeg's standard mask. This fixes cases
#    where -ch_layout 5.1 / -ch_layout 22.2 create a custom-ordered layout.
old_compare = '''    for (size_t i = 0; i < FF_ARRAY_ELEMS(channel_layout_masks); ++i) {
        if (channel_layout_masks[i]) {
            AVChannelLayout ch_layout;
            av_channel_layout_from_mask(&ch_layout, channel_layout_masks[i]);
            if (!av_channel_layout_compare(layout, &ch_layout))
                return i;
        }
    }

    return 0;'''

new_compare = '''    for (size_t i = 0; i < FF_ARRAY_ELEMS(channel_layout_masks); ++i) {
        if (channel_layout_masks[i]) {
            AVChannelLayout ch_layout;
            av_channel_layout_from_mask(&ch_layout, channel_layout_masks[i]);
            if (!av_channel_layout_compare(layout, &ch_layout))
                return i;
            if (layout->nb_channels == ch_layout.nb_channels &&
                av_channel_layout_subset(layout, channel_layout_masks[i]))
                return i;
        }
    }

    return 0;'''

if old_compare not in text:
    raise SystemExit('channel_layout_to_cicp loop not found')
text = text.replace(old_compare, new_compare)

# 2. Default to 22.2 when no layout is specified, because 360RA content is
#    typically 22.2 and the library is most likely to init successfully with
#    the original content layout. Users can still override with -ch_layout.
old_init = '''    if (avctx->ch_layout.nb_channels == 0) {
        av_log(avctx, AV_LOG_ERROR, "Channel layout needs to be specified\\n");
        return AVERROR(EINVAL);'''

new_init = '''    if (avctx->ch_layout.nb_channels == 0) {
        av_log(avctx, AV_LOG_WARNING,
               "No channel layout specified, defaulting to 22.2. "
               "Use -ch_layout to override (e.g. -ch_layout 5.1).\\n");
        av_channel_layout_from_mask(&avctx->ch_layout, AV_CH_LAYOUT_22POINT2);'''

if old_init not in text:
    raise SystemExit('mpegh3dadec_init nb_channels check not found')
text = text.replace(old_init, new_init)

p.write_text(text, encoding='utf-8')
print('libmpeghdec.c patched')
