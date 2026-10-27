"""Flatten a screen filmed by a handheld phone into a straight-on video, so its motion can be measured.
usage: python tools/rectify_screen.py <phone.mp4> <out.mp4> [--quad auto|"x,y x,y x,y x,y"] [--at S] [--from S]
                                      [--to S] [--band y0:y1] [--size WxH] [--fps 30] [--check FILE.jpg] [--force]
The camera is tracked on the static room around the screen (feature matches outside the screen), and the screen's
quadrilateral at --at follows it into every frame. --quad auto finds the screen as the brightest changing
quadrilateral over the 0.2 s after --at; otherwise give its corners at --at, top left, top right, bottom right,
bottom left, in pixels of the decoded frame (read them off the --check image). --band rows (a burnt-in caption) are
kept out of the tracking. The output is 1280x720, or 720x1280 for a tall screen, at --fps, without audio.
Exit 0: written; 2: bad input, no screen found or no frames."""
import argparse, os, subprocess, sys
import numpy as np

STACK_S = 0.2        # auto detection reads this much after --at: longer, and handheld drift smears the outline
MIN_AREA = 0.05      # the screen covers at least 5% of the frame
GROW = 1.08          # tracking ignores the screen and a margin around it: its content moves, the room does not
SCALE = 0.5          # features are found at half resolution
MIN_MATCHES, MIN_INLIERS = 25, 20
TRACKED_WARN = 0.8


class BadInput(Exception):
    pass


def frame_size(src):
    """The decoded frame size, rotation applied, from one frame's PPM header (phone clips carry a rotation tag)."""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', src, '-frames:v', '1', '-f', 'image2pipe',
                        '-c:v', 'ppm', '-'], capture_output=True)
    head = r.stdout[:64].split()
    if r.returncode != 0 or len(head) < 3 or head[0] != b'P6':
        raise BadInput(f'{src}: no video frames')
    return int(head[1]), int(head[2])


def frames(src, w, h, fps, t0=0.0, t1=None):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t0:.3f}', '-i', src]
    if t1 is not None:
        cmd += ['-t', f'{t1 - t0:.3f}']
    p = subprocess.Popen(cmd + ['-vf', f'fps={fps}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    n = w * h * 3
    try:
        while True:
            b = p.stdout.read(n)
            if len(b) < n:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    finally:
        p.kill()
        p.wait()
        p.stdout.close()


def order(q):
    """Corners as top left, top right, bottom right, bottom left."""
    q = np.float32(q)
    s, d = q.sum(1), np.diff(q, axis=1)[:, 0]
    return np.float32([q[np.argmin(s)], q[np.argmin(d)], q[np.argmax(s)], q[np.argmax(d)]])


def find_screen(stack, w, h):
    """The brightest changing region of the stack, reduced to four corners, or None."""
    import cv2
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in stack])
    score = cv2.normalize(g.std(0), None, 0, 1, cv2.NORM_MINMAX) + cv2.normalize(g.mean(0), None, 0, 1, cv2.NORM_MINMAX)
    u8 = cv2.normalize(cv2.GaussianBlur(score, (0, 0), 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, m = cv2.threshold(u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < MIN_AREA * w * h:
        return None
    hull = cv2.convexHull(c)
    per = cv2.arcLength(hull, True)
    for eps in np.linspace(0.01, 0.08, 15):
        p = cv2.approxPolyDP(hull, eps * per, True)
        if len(p) == 4:
            return order(p[:, 0])
    return None


def parse_quad(text, w, h):
    try:
        pts = [[float(v) for v in p.split(',')] for p in text.split()]
        if len(pts) != 4 or any(len(p) != 2 for p in pts):
            raise ValueError
    except ValueError:
        raise BadInput(f'--quad {text!r}: expected four corners "x,y x,y x,y x,y"')
    if any(not (0 <= x <= w and 0 <= y <= h) for x, y in pts):
        raise BadInput(f'--quad {text!r}: a corner is outside the {w}x{h} frame')
    return order(pts)


def parse_pair(text, sep, what):
    try:
        a, b = (int(v) for v in text.split(sep))
    except ValueError:
        raise BadInput(f'{what} {text!r}: expected two integers separated by {sep!r}')
    return a, b


def mask_for(q, band, w, h):
    import cv2
    m = np.full((int(h * SCALE), int(w * SCALE)), 255, np.uint8)
    c = q.mean(0)
    cv2.fillPoly(m, [np.int32(((q - c) * GROW + c) * SCALE)], 0)
    if band:
        m[int(band[0] * SCALE):int(band[1] * SCALE), :] = 0
    return m


def check_image(path, ref, q, flat):
    import cv2
    img = ref.copy()
    cv2.polylines(img, [np.int32(q)], True, (0, 255, 0), 2)
    for (x, y), name in zip(q, ('TL', 'TR', 'BR', 'BL')):
        cv2.circle(img, (int(x), int(y)), 6, (0, 0, 255), -1)
        cv2.putText(img, f'{name} {int(x)},{int(y)}', (int(x) + 8, int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 0, 255), 2)
    side = cv2.resize(flat, (max(2, round(flat.shape[1] * img.shape[0] / flat.shape[0])), img.shape[0]))
    cv2.imwrite(path, np.hstack([img, side]))


def run(a):
    import cv2
    for path in (a.out, a.check):
        if path and os.path.abspath(path) == os.path.abspath(a.src):
            raise BadInput(f'{path} is the source video; pick another output path')
        if path and os.path.exists(path) and not a.force:
            raise BadInput(f'{path} exists; pass --force to replace it')
    if not os.path.isfile(a.src):
        raise BadInput(f'{a.src}: no such file')
    w, h = frame_size(a.src)
    band = parse_pair(a.band, ':', '--band') if a.band else None
    stack = [f for _, f in zip(range(max(2, round(STACK_S * a.fps))), frames(a.src, w, h, a.fps, a.at))]
    if not stack:
        raise BadInput(f'{a.src}: no frames at --at {a.at:g}')
    if a.quad == 'auto':
        q = find_screen(stack, w, h)
        if q is None:
            raise BadInput('no screen found: pass --quad "x,y x,y x,y x,y" (TL TR BR BL at --at)')
    else:
        q = parse_quad(a.quad, w, h)
    print('corners at --at (TL TR BR BL): ' + ' '.join(f'{x:.0f},{y:.0f}' for x, y in q))
    if a.size:
        ow, oh = parse_pair(a.size, 'x', '--size')
    else:
        wide = np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])
        tall = np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])
        ow, oh = (1280, 720) if wide >= tall else (720, 1280)
    if ow < 2 or oh < 2 or ow % 2 or oh % 2:
        raise BadInput(f'--size {ow}x{oh}: sides must be even and at least 2')
    sift, bf = cv2.SIFT_create(4000), cv2.BFMatcher()

    def small(f):
        return cv2.cvtColor(cv2.resize(f, (int(w * SCALE), int(h * SCALE))), cv2.COLOR_BGR2GRAY)

    kr, dr = sift.detectAndCompute(small(stack[0]), mask_for(q, band, w, h))
    if dr is None or len(kr) < MIN_MATCHES:
        raise BadInput('too little texture around the screen to track the camera (fill less of the frame with it)')
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s',
                            f'{ow}x{oh}', '-r', f'{a.fps:g}', '-i', '-', '-c:v', 'libx264', '-crf', '14', '-pix_fmt',
                            'yuv420p', '-an', a.out], stdin=subprocess.PIPE)
    dst = np.float32([[0, 0], [ow, 0], [ow, oh], [0, oh]])
    hm, n, tracked, first = np.eye(3), 0, 0, None
    for fr in frames(a.src, w, h, a.fps, a.start, a.end):
        k, d = sift.detectAndCompute(small(fr), mask_for(cv2.perspectiveTransform(q[None], hm)[0], band, w, h))
        if d is not None and len(k) > MIN_MATCHES:
            good = [m for m, o in (x for x in bf.knnMatch(dr, d, k=2) if len(x) == 2) if m.distance < 0.7 * o.distance]
            if len(good) > MIN_MATCHES:
                p0 = np.float32([kr[m.queryIdx].pt for m in good]) / SCALE
                p1 = np.float32([k[m.trainIdx].pt for m in good]) / SCALE
                hn, inl = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)
                if hn is not None and int(inl.sum()) > MIN_INLIERS:
                    hm, tracked = hn, tracked + 1  # otherwise the last good camera estimate holds
        cur = cv2.perspectiveTransform(q[None], hm)[0]
        flat = cv2.warpPerspective(fr, cv2.getPerspectiveTransform(cur, dst), (ow, oh), flags=cv2.INTER_CUBIC)
        enc.stdin.write(flat.tobytes())
        first = flat if first is None else first
        n += 1
    enc.stdin.close()
    if enc.wait() != 0 or not n:
        raise BadInput(f'{a.src}: no frames from --from {a.start:g}' + (f' to --to {a.end:g}' if a.end else '')
                       if not n else f'ffmpeg could not write {a.out}')
    if a.check:
        check_image(a.check, stack[0], q, first)
    share = tracked / n
    print(f'wrote {a.out}: {n} frames at {a.fps:g} fps, {ow}x{oh}, tracked {share:.0%}')
    if share < TRACKED_WARN:
        print(f'WARN tracked under {TRACKED_WARN:.0%}: too little static texture, or the screen fills the frame; '
              'flatten a steadier stretch (--from, --to)')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='rectify_screen.py', usage=__doc__.split('usage: ', 1)[1].split('\nThe ')[0])
    ap.add_argument('src', nargs='?')
    ap.add_argument('out', nargs='?')
    ap.add_argument('--quad', default='auto')
    ap.add_argument('--at', type=float, default=0.0)
    ap.add_argument('--from', dest='start', type=float, default=0.0)
    ap.add_argument('--to', dest='end', type=float)
    ap.add_argument('--band')
    ap.add_argument('--size')
    ap.add_argument('--fps', type=float, default=30.0)
    ap.add_argument('--check')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if not a.src or not a.out:
        ap.print_usage(sys.stderr)
        return 2
    try:
        return run(a)
    except BadInput as e:
        print(f'error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
