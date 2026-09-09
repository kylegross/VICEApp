"""Dynamic Discord battle cards drawn locally; no external image service."""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter


def font(size):
    for name in ('DejaVuSans.ttf', 'arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def headline(canvas, text, y, size=54, color='#59f5ef', max_width=None, x=None, glow_enabled=True):
    """Fit a bold neon headline without cropping long mode names."""
    max_width = max_width or canvas.width - 70
    while True:
        face = None
        for name in ('DejaVuSans-Bold.ttf', 'arialbd.ttf'):
            try:
                face = ImageFont.truetype(name, size)
                break
            except OSError:
                pass
        face = face or font(size)
        if ImageDraw.Draw(canvas).textlength(text, font=face) <= max_width or size <= 12:
            break
        size -= 1
    layer = Image.new('RGBA', canvas.size)
    d = ImageDraw.Draw(layer)
    position = (canvas.width // 2 if x is None else x, y)
    d.text(position, text, font=face, fill=color, anchor='mt', stroke_width=3, stroke_fill=color)
    glow = layer.filter(ImageFilter.GaussianBlur(9))
    if glow_enabled:
        canvas.paste(glow, (0, 0), glow)
    ImageDraw.Draw(canvas).text(position, text, font=face, fill='#f3ffff', anchor='mt', stroke_width=1, stroke_fill=color)


def render_lobby(path, mode):
    titles = {'classic': 'CLASSIC', 'sexes': 'BATTLE OF THE SEXES', 'winner': 'WINNER FLASHES', 'world': 'NORTH AMERICA VS. THE WORLD'}
    with Image.open(path) as original:
        art = original.convert('RGB')
        art.thumbnail((1200, 1000))
    width = max(800, art.width)
    canvas = Image.new('RGB', (width, art.height + 200), '#100f1d')
    canvas.paste(art, ((width-art.width)//2, 200))
    headline(canvas, 'VICE / AFTER DARK ARENA', 24, 30, '#d69bf5')
    headline(canvas, titles[mode], 80, 66)
    draw = ImageDraw.Draw(canvas)
    draw.line((45, 169, width-45, 169), fill='#59f5ef', width=2)
    draw.text((width//2, 181), 'JOIN THE ARENA', font=font(15), fill='#d1b9dc', anchor='mt')
    output = BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()


def centered(draw, text, x, y, size, color):
    f = font(size)
    while draw.textlength(text, font=f) > 270 and len(text) > 1:
        text = text[:-2] + '…'
    draw.text((x, y), text, font=f, fill=color, anchor='mt')


def portrait(canvas, data, name, x, y, dead, status=None):
    try:
        avatar = Image.open(BytesIO(data))
        avatar = ImageOps.fit(avatar.convert('RGB'), (240, 240))
    except (OSError, ValueError, TypeError):
        avatar = Image.new('RGB', (240, 240), '#514665')
        draw = ImageDraw.Draw(avatar)
        draw.ellipse((82, 38, 158, 114), fill='#d9cfdf')
        draw.ellipse((42, 132, 198, 292), fill='#d9cfdf')
    if dead:
        avatar = ImageEnhance.Brightness(ImageOps.grayscale(avatar).convert('RGB')).enhance(.52)
    mask = Image.new('L', (240, 240))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 239, 239), radius=25, fill=255)
    canvas.paste(avatar, (x, y), mask)
    if dead:
        cross = Image.new('RGBA', (240, 240))
        cross_draw = ImageDraw.Draw(cross)
        strokes = [((40, 40), (200, 200)), ((200, 40), (40, 200))]
        for stroke in strokes:
            cross_draw.line(stroke, fill='#ff3fbb', width=15)
        aura = cross.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(aura, (x, y), aura)
        canvas.paste(cross, (x, y), cross)
        cross_draw = ImageDraw.Draw(canvas)
        for start, end in strokes:
            cross_draw.line(((x+start[0], y+start[1]), (x+end[0], y+end[1])),
                            fill='#ffd0ef', width=4)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x, y, x+239, y+239), radius=25, outline='#797782' if dead else '#ef85c4', width=3)
    centered(draw, name, x+120, y+255, 23, '#c0bdc9' if dead else '#ffffff')
    if status:
        centered(draw, status, x+120, y+290, 17, '#ef85c4')
    else:
        draw.rounded_rectangle((x-40, y+282, x+280, y+337), radius=12, fill='#15121e')
        headline(canvas, 'ELIMINATED' if dead else 'SURVIVES', y+290, 42,
                 '#ff3fbb' if dead else '#39ffe2', max_width=310, x=x+120, glow_enabled=True)


def render_winner(name, avatar, rounds, kills):
    try:
        with Image.open(Path(__file__).resolve().parent / 'arena-background.png') as background:
            canvas = ImageOps.fit(background.convert('RGB'), (800, 640))
        canvas = ImageEnhance.Brightness(canvas).enhance(.6)
    except (OSError, ValueError):
        canvas = Image.new('RGB', (800, 640), '#14101e')
    halo = Image.new('RGBA', canvas.size)
    ImageDraw.Draw(halo).ellipse((225, 130, 575, 480), fill=(255, 190, 65, 65))
    halo = halo.filter(ImageFilter.GaussianBlur(45))
    canvas.paste(halo, (0, 0), halo)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((14, 14, 785, 625), radius=30, outline='#ffd166', width=4)
    headline(canvas, 'ARENA CHAMPION', 40, 58, '#ffd166')
    draw.polygon([(361,145),(350,112),(380,128),(400,102),(420,128),(450,112),(439,145)], fill='#ffd166')
    portrait(canvas, avatar, '', 280, 177, False, status='LAST PLAYER STANDING')
    headline(canvas, name, 432, 36, '#ffd166', max_width=700)
    draw.rounded_rectangle((276, 173, 523, 420), radius=28, outline='#ffd166', width=4)
    headline(canvas, f'{rounds} ROUNDS SURVIVED', 531, 38, '#ffd166', max_width=700)
    draw.text((400, 585), 'VICE / AFTER DARK ARENA', font=font(20), fill='#d4bbd8', anchor='mt')
    output = BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()


def render_results(lines, profiles, mode_name):
    """Render paginated results; Discord mentions remain in accompanying text."""
    import re
    pages, rows = [], []
    measure = ImageDraw.Draw(Image.new('RGB', (1000, 1)))
    face = font(24)
    for line in lines:
        if line.startswith('#'):
            continue
        line = re.sub(r'<@(\d+)>', lambda match: profiles.get(int(match[1]), 'Player'), line)
        line = line.replace('**', '')
        current = ''
        for char in line:
            if measure.textlength(current + char, font=face) > 870:
                rows.append(current)
                current = ''
            current += char
        rows.append(current)
        rows.append('')
    for offset in range(0, len(rows), 26):
        group = rows[offset:offset+26]
        height = max(400, 200 + len(group)*34)
        try:
            with Image.open(Path(__file__).resolve().parent / 'arena-background.png') as art:
                canvas = ImageOps.fit(art.convert('RGB'), (1000, height))
            canvas = ImageEnhance.Brightness(canvas).enhance(.45)
        except (OSError, ValueError):
            canvas = Image.new('RGB', (1000,height), '#14101e')
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((16,16,983,height-17), radius=25, outline='#59f5ef', width=3)
        headline(canvas, 'FINAL RESULTS', 32, 52, '#ffd166')
        headline(canvas, mode_name.upper(), 102, 30)
        for i, row in enumerate(group):
            draw.text((65, 170+i*34), row, font=face, fill='#f4f6ff', stroke_width=1, stroke_fill='#0a0d16')
        draw.text((950,height-28), f'{offset//26+1}', font=font(16), fill='#59f5ef', anchor='rt')
        output=BytesIO()
        canvas.save(output, format='PNG')
        pages.append(output.getvalue())
    return pages


def render_card(event, profiles, avatars, round_number):
    unexpected = event['kind'] == 'unexpected'
    width, height = (600, 600) if unexpected else (960, 480)
    try:
        with Image.open(Path(__file__).resolve().parent / 'arena-background.png') as background:
            canvas = ImageOps.fit(background.convert('RGB'), (width, height))
        canvas = ImageEnhance.Brightness(canvas).enhance(.45)
    except (OSError, ValueError):
        canvas = Image.new('RGB', (width, height), '#14101e')
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((12, 12, width-13, height-13), radius=28, outline='#44304e', width=2)
    header_font = font(24)
    for candidate in ('DejaVuSans-Bold.ttf', 'arialbd.ttf'):
        try:
            header_font = ImageFont.truetype(candidate, 24)
            break
        except OSError:
            pass
    draw.text((32, height-32), 'AFTER DARK / ARENA', font=header_font, fill='#f2ffff',
              anchor='lm', stroke_width=2, stroke_fill='#080b13')
    draw.text((width-32, height-32), f'ROUND {round_number}', font=header_font, fill='#69ffe7',
              anchor='rm', stroke_width=2, stroke_fill='#080b13')
    victim = event['eliminated']
    if unexpected:
        headline(canvas, 'UNEXPECTED DEATH', 30, 44, '#ef85c4')
        portrait(canvas, avatars.get(victim), profiles.get(victim, 'Player'), 180, 175, True)
        draw.text((width//2, 530), 'Nobody saw that coming.', font=font(20), fill='#a99caf', anchor='mt')
    else:
        # Swap sides by ID parity so survivors are not always on the left.
        winner = event['winner']
        left, right = (winner, victim) if victim % 2 else (victim, winner)
        portrait(canvas, avatars.get(left), profiles.get(left, 'Player'), 65, 100, left == victim)
        portrait(canvas, avatars.get(right), profiles.get(right, 'Player'), 655, 100, right == victim)
        # Two metal cuffs, hinged ratchet blocks, and connecting chain.
        for cx, cy in ((423, 205), (537, 250)):
            draw.ellipse((cx-38, cy-48, cx+38, cy+48), outline='#cbd0dc', width=12)
            draw.arc((cx-30, cy-40, cx+30, cy+40), 200, 320, fill='#ffffff', width=3)
            draw.rounded_rectangle((cx-15, cy-56, cx+15, cy-37), radius=4, fill='#919aaa')
            draw.ellipse((cx-3, cy-51, cx+3, cy-45), fill='#252333')
        for cx, cy in ((461, 220), (479, 229), (497, 238)):
            draw.ellipse((cx-13, cy-8, cx+13, cy+8), outline='#adb6c7', width=4)
        headline(canvas, 'BATTLE', 80, 52, '#ef85c4', max_width=280)
        headline(canvas, 'THE SHOWDOWN', 30, 44)
    output = BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()
