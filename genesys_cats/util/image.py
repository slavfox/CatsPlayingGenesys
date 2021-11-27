# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Image-related utilities."""
from typing import List, Optional, Tuple, cast

import numpy as np
from numpy.typing import ArrayLike
from PIL import Image, ImageColor


def hsl_to_rgb(
    hue: int, saturation: int, lightness: int
) -> Tuple[int, int, int]:
    """Convert a HSL color to RGB."""
    return cast(
        Tuple[int, int, int],
        ImageColor.getrgb(f"hsl({hue}" f",{saturation}%" f",{lightness}%)"),
    )


def color_image(
    color: Tuple[int, int, int], image_data: ArrayLike
) -> Image.Image:
    """Change the color of an image, preserving the alpha channel."""
    body = np.copy(image_data)
    body[..., :-1] = color
    return Image.fromarray(body)


def combine_images(images: List[Image.Image]) -> Optional[Image.Image]:
    """Combine multiple images side by side."""
    if not images:
        return None
    dst = Image.new("RGBA", (sum(im.width for im in images), images[0].height))
    offset = 0
    for image in images:
        dst.paste(image, (offset, 0))
        offset += image.width
    return dst
