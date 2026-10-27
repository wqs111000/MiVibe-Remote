"""A small, scalable remote-and-voice mark used by the Windows application."""

from PIL import Image, ImageDraw


def make_icon(size: int = 256, status_color: str | None = None) -> Image.Image:
    # Draw at a fixed high resolution so small tray icons remain anti-aliased.
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=62, fill="#205bdd")
    draw.rounded_rectangle((83, 34, 173, 220), radius=43, fill="#ffffff")
    draw.ellipse((108, 61, 148, 101), fill="#d9e9ff")
    draw.ellipse((116, 69, 140, 93), fill="#205bdd")
    draw.rounded_rectangle((110, 122, 146, 173), radius=18, fill="#205bdd")
    draw.arc((102, 133, 154, 184), 0, 180, fill="#205bdd", width=6)
    draw.line((128, 181, 128, 193), fill="#205bdd", width=6)
    draw.line((117, 193, 139, 193), fill="#205bdd", width=6)
    if status_color:
        draw.ellipse((179, 179, 241, 241), fill="#ffffff")
        draw.ellipse((186, 186, 234, 234), fill=status_color)
    return image.resize((size, size), Image.Resampling.LANCZOS)
