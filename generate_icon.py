#!/usr/bin/env python3
"""Generate a beautiful green tree app icon for Farm Tree Manager."""

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024


def rounded_gradient_background(size):
    """Soft vertical green gradient with rounded corners."""
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base, "RGBA")
    top = (76, 175, 80, 255)      # light green
    bottom = (27, 94, 32, 255)    # deep green
    for y in range(size):
        t = y / size
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    # rounded corners mask
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size, size], radius=int(size * 0.22), fill=255)
    base.putalpha(mask)
    return base


def add_foliage(draw, cx, base_y, scale):
    """Layered overlapping circles forming a rounded canopy."""
    layers = [
        (int(150 * scale), (102, 187, 106, 255)),  # light
        (int(120 * scale), (67, 160, 71, 255)),    # mid
        (int(95 * scale), (46, 125, 50, 255)),     # dark
    ]
    # bottom row of blobs
    positions = [
        (cx - 110 * scale, base_y - 60 * scale),
        (cx + 110 * scale, base_y - 60 * scale),
        (cx, base_y - 150 * scale),
        (cx - 70 * scale, base_y - 200 * scale),
        (cx + 70 * scale, base_y - 200 * scale),
        (cx, base_y - 300 * scale),
    ]
    # draw larger lighter blobs first, then smaller darker on top for depth
    for radius, color in layers:
        for (x, y) in positions:
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color,
            )


def main():
    img = rounded_gradient_background(SIZE)
    draw = ImageDraw.Draw(img, "RGBA")

    cx = SIZE // 2
    trunk_bottom = int(SIZE * 0.82)
    trunk_top = int(SIZE * 0.60)
    trunk_w = int(SIZE * 0.085)
    # trunk
    draw.rounded_rectangle(
        [cx - trunk_w // 2, trunk_top, cx + trunk_w // 2, trunk_bottom],
        radius=trunk_w // 3,
        fill=(121, 85, 72, 255),
    )
    # a little grass mound under the tree
    draw.ellipse(
        [cx - 200, int(SIZE * 0.80), cx + 200, int(SIZE * 0.92)],
        fill=(129, 199, 132, 255),
    )

    add_foliage(draw, cx, trunk_top, 1.0)

    # subtle highlight on canopy
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hld = ImageDraw.Draw(hl, "RGBA")
    hld.ellipse(
        [cx - 150, int(SIZE * 0.18), cx + 10, int(SIZE * 0.42)],
        fill=(255, 255, 255, 40),
    )
    hl = hl.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img, hl)

    out = "assets/icon.png"
    img.save(out, "PNG")
    print(f"Icon written to {out} ({img.size})")


if __name__ == "__main__":
    main()
