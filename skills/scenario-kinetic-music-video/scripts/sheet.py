"""Contact sheet with time labels. usage: python tools/sheet.py out.jpg cols img1 img2 ... [--fps N [--start S]] [--force]
Labels: still.mjs's t_<seconds>.png names give their time. Frames ffmpeg wrote as f_0001.jpg, f_0002.jpg ... at --fps N
give S + (n - 1) / N seconds, S being the song time of the video's first frame (default 0). Other files show their name.
Refuses to replace an existing out.jpg unless --force is given, and never writes over one of its inputs."""
import os, sys, re


def label(path, fps=None, start=0.0):
    name = os.path.basename(path)
    m = re.match(r't_([\d.]+)\.png$', name)
    if m:
        return f'{float(m.group(1)):g}'
    m = re.match(r'f_(\d+)\.\w+$', name)
    if m and fps:
        return f'{start + (int(m.group(1)) - 1) / fps:.1f}'
    return name


def option(argv, flag):
    """The value after flag, removed from argv with it, or None."""
    if flag not in argv:
        return None
    i = argv.index(flag)
    if i + 1 >= len(argv):
        sys.exit(f'{flag} needs a number')
    value = argv[i + 1]
    del argv[i:i + 2]
    try:
        return float(value)
    except ValueError:
        sys.exit(f'{flag} needs a number, not {value}')


def main(argv):
    force = '--force' in argv
    argv = [a for a in argv if a != '--force']
    fps, start = option(argv, '--fps'), option(argv, '--start') or 0.0
    if len(argv) < 3: sys.exit(__doc__)
    from PIL import Image, ImageDraw, ImageFont
    out, cols, files = argv[0], int(argv[1]), argv[2:]
    if os.path.abspath(out) in {os.path.abspath(f) for f in files}: sys.exit(f'{out} is also an input; choose another output path')
    if os.path.exists(out) and not force: sys.exit(f'{out} exists; pass --force to replace it')
    ims = [Image.open(f).convert('RGB') for f in files]; w, h = ims[0].size; rows = (len(ims)+cols-1)//cols
    S = Image.new('RGB', (w*cols, h*rows)); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype('assets/fonts/JetBrainsMono-VF.ttf', max(14, h//18))
    except OSError: font = None
    for i, (im, f) in enumerate(zip(ims, files)):
        x, y = (i % cols)*w, (i//cols)*h; S.paste(im, (x, y)); lab = label(f, fps, start)
        d.rectangle([x, y, x+len(lab)*h//28+16, y+h//14], fill=(0,0,0)); d.text((x+6, y+2), lab, fill=(255,200,80), font=font)
    S.save(out, quality=88); print(out)


if __name__ == '__main__':
    main(sys.argv[1:])
