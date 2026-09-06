from pathlib import Path
import struct

SIZE = 32

repo_root = Path(__file__).resolve().parents[1]
icon_dir = repo_root / "src-tauri" / "icons"
icon_path = icon_dir / "icon.ico"

icon_dir.mkdir(parents=True, exist_ok=True)

# Colors are BGRA because Windows DIB icon pixels use B,G,R,A order.
BACKGROUND = (18, 14, 9, 255)
ACCENT = (255, 141, 109, 255)
WHITE = (245, 245, 245, 255)

pixels = [[BACKGROUND for _ in range(SIZE)] for _ in range(SIZE)]

# Blue inset square.
for y in range(5, SIZE - 5):
    for x in range(5, SIZE - 5):
        pixels[y][x] = ACCENT

# Simple dark "M" mark.
for y in range(9, 24):
    left = 9
    right = 22

    pixels[y][left] = BACKGROUND
    pixels[y][left + 1] = BACKGROUND
    pixels[y][right] = BACKGROUND
    pixels[y][right - 1] = BACKGROUND

for i in range(7):
    y = 10 + i
    pixels[y][11 + i // 2] = BACKGROUND
    pixels[y][12 + i // 2] = BACKGROUND
    pixels[y][20 - i // 2] = BACKGROUND
    pixels[y][19 - i // 2] = BACKGROUND

# Windows icon DIBs are stored bottom-up.
xor_bitmap = bytearray()

for row in reversed(pixels):
    for b, g, r, a in row:
        xor_bitmap.extend((b, g, r, a))

# 1-bit transparency mask.
mask_row_bytes = ((SIZE + 31) // 32) * 4
and_mask = bytes(mask_row_bytes * SIZE)

bitmap_info_header = struct.pack(
    "<IIIHHIIIIII",
    40,             # header size
    SIZE,
    SIZE * 2,       # XOR + AND mask height
    1,              # planes
    32,             # bits per pixel
    0,              # BI_RGB
    len(xor_bitmap),
    0,
    0,
    0,
    0,
)

image_data = bitmap_info_header + xor_bitmap + and_mask

icon_dir_header = struct.pack(
    "<HHH",
    0,  # reserved
    1,  # icon
    1,  # image count
)

icon_entry = struct.pack(
    "<BBBBHHII",
    SIZE,
    SIZE,
    0,
    0,
    1,
    32,
    len(image_data),
    6 + 16,
)

icon_path.write_bytes(icon_dir_header + icon_entry + image_data)

print(f"Created {icon_path}")