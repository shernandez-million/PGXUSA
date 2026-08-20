#!/usr/bin/env python3
"""Refit the PGX wordmark outline with true curves.

The supplied SVG is a bitmap trace: 364 straight segments on integer coordinates
and no curve commands at all. That is fine at nav size but at footer size each
unit is over a pixel, so the polygon facets and the +/-0.5 unit quantisation read
as a wobbly, hand-drawn edge.

This detects genuine corners (serif terminals, stroke junctions) and keeps them
sharp, then replaces the polygonal runs between them with fitted cubic Beziers.
"""
import math
import re
import sys

CORNER_DEG = 32.0     # turn sharper than this is a real corner, not trace noise
SMOOTH_PASSES = 2     # gentle averaging to take out integer quantisation
SMOOTH_W = 0.26


def parse(d):
    subs = []
    for chunk in d.split('M'):
        chunk = chunk.strip()
        if not chunk:
            continue
        closed = chunk.rstrip().endswith('Z')
        nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', chunk)]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts.pop()
        subs.append((pts, closed))
    return subs


def turn_angle(a, b, c):
    v1 = (b[0]-a[0], b[1]-a[1]); v2 = (c[0]-b[0], c[1]-b[1])
    n1 = math.hypot(*v1); n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cosv = max(-1.0, min(1.0, (v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))
    return math.degrees(math.acos(cosv))


def corners(pts):
    n = len(pts)
    return [i for i in range(n)
            if turn_angle(pts[(i-1) % n], pts[i], pts[(i+1) % n]) > CORNER_DEG]


def smooth(pts, keep):
    """Average out quantisation noise, but never move a detected corner."""
    pts = list(pts); n = len(pts)
    for _ in range(SMOOTH_PASSES):
        out = list(pts)
        for i in range(n):
            if i in keep:
                continue
            p, c, q = pts[(i-1) % n], pts[i], pts[(i+1) % n]
            out[i] = (c[0] + SMOOTH_W*((p[0]+q[0])/2 - c[0]),
                      c[1] + SMOOTH_W*((p[1]+q[1])/2 - c[1]))
        pts = out
    return pts


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def run_to_bezier(run):
    """Catmull-Rom through the run, emitted as cubic Beziers."""
    if len(run) < 2:
        return ''
    ext = [run[0]] + list(run) + [run[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i-1], ext[i], ext[i+1], ext[i+2]
        c1 = (p1[0] + (p2[0]-p0[0])/6, p1[1] + (p2[1]-p0[1])/6)
        c2 = (p2[0] - (p3[0]-p1[0])/6, p2[1] - (p3[1]-p1[1])/6)
        out.append(f'C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}')
    return ''.join(out)


def rebuild(d):
    parts = []
    stats = {'corners': 0, 'pts': 0}
    for pts, closed in parse(d):
        stats['pts'] += len(pts)
        keep = set(corners(pts))
        stats['corners'] += len(keep)
        pts = smooth(pts, keep)
        n = len(pts)
        idx = sorted(keep) if keep else [0]
        seg = [f'M{fmt(pts[idx[0]][0])} {fmt(pts[idx[0]][1])}']
        for k in range(len(idx)):
            a = idx[k]; b = idx[(k+1) % len(idx)]
            run = []
            i = a
            while True:
                run.append(pts[i])
                if i == b:
                    break
                i = (i+1) % n
            if len(run) == 2:                      # corner to corner: real straight edge
                seg.append(f'L{fmt(run[1][0])} {fmt(run[1][1])}')
            else:
                seg.append(run_to_bezier(run))
        seg.append('Z')
        parts.append(''.join(seg))
    return ' '.join(parts), stats


if __name__ == '__main__':
    src = open('images/pgx-wordmark.svg').read()
    d = re.search(r'\sd="([^"]+)"', src).group(1)
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    nd, st = rebuild(d)
    print(f"points {st['pts']}, corners kept sharp {st['corners']}, "
          f"path {len(d)} -> {len(nd)} chars")
    open('images/pgx-wordmark.svg', 'w').write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="PGX logo">\n'
        f'  <title>PGX logo</title>\n'
        f'  <path d="{nd}" fill="#111111" fill-rule="evenodd"/>\n</svg>\n')
    open('images/pgx-wordmark-outline.svg', 'w').write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">\n'
        f'  <path d="{nd}" fill="none" stroke="#000000" stroke-width="1.4" fill-rule="evenodd"/>\n</svg>\n')
    print('rewrote images/pgx-wordmark.svg and images/pgx-wordmark-outline.svg')
