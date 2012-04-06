#!/usr/bin/env python

import argparse
import yaml
import fontforge
import psMat

# returns list of tuples:
# [(code1, {'resize': 1.0, 'offset': '0.0'}), (code2, {}), ...]
def get_transform_config(config):
    font_transform = config.get('transform', {})

    def get_transform_item(glyph):
        name, glyph = glyph.items()[0]
        transform = font_transform.copy()
        glyph_transform = glyph.get('transform', {})
        if 'offset' in glyph_transform:
            transform['offset'] = (transform.get('offset', 0)
                + glyph_transform.get('offset'))
        return (glyph.get('code'), transform)

    return [get_transform_item(glyph) for glyph in config['glyphs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Font transform tool')
    parser.add_argument('-c', '--config',   type=str, required=True,
        help='Config example: ../config.yml')
    parser.add_argument('-i', '--src_font', type=str, required=True,
        help='Input font')
    parser.add_argument('-o', '--dst_font', type=str, required=True,
        help='Output font')

    args = parser.parse_args()

    config = yaml.load(open(args.config, 'r'))

    transform_config = get_transform_config(config)
    #print "transform_config=", transform_config

    codes = zip(*transform_config)[0]

    # validate config: codes
    if len(codes) > len(set(codes)):
        print "Error: codes have duplicates"   # FIXME
        exit(1)

    has_transform = lambda x: 'resize' in x or 'offset' in x
    codes_to_transform = [i for i in transform_config if has_transform(i)]
    #print "codes_to_transform=", codes_to_transform

    font = fontforge.open(args.src_font)

    # set ascent/descent
    ascent = config.get('font', {}).get('ascent', None)
    descent = config.get('font', {}).get('descent', None)

    if ascent:
        font.ascent = ascent
    if descent:
        font.descent = descent

    # apply transformations
    for code, transform in codes_to_transform:
        font.selection.select(("unicode",), code)

        if 'resize' in transform:
            # bbox: a tuple representing a rectangle (xmin,ymin, xmax,ymax)
            bbox = font[code].boundingBox()

            # center of bbox
            x, y = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

            # move center of bbox to (0, 0)
            translate_matrix = psMat.translate(-x, -y)
            font.transform(translate_matrix)

            # scale around (0, 0)
            scale_matrix = psMat.scale(transform['resize'])
            font.transform(scale_matrix)

            # move center of bbox back to its old position
            translate_matrix = psMat.translate(x, y)
            font.transform(translate_matrix)

        if 'offset' in transform:
            # shift the selected glyph vertically
            offset = transform['offset'] * (font.ascent + font.descent)
            translate_matrix = psMat.translate(0, offset)
            font.transform(translate_matrix)

    font.generate(args.dst_font)

    exit(0)
