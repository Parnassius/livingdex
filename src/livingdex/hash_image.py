"""
This file was adapted from ImageHash by Johannes Buchner, copyright information below:


Copyright (c) 2013-2022, Johannes Buchner
https://github.com/JohannesBuchner/imagehash

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import math
from collections.abc import Iterable

from PIL import Image


class ImageHash:
    def __init__(self, hash_: Iterable[bool]):
        self.hash = tuple(hash_)

    def __sub__(self, other: object) -> int:
        if not isinstance(other, ImageHash):
            return NotImplemented
        if len(self.hash) != len(other.hash):
            msg = "ImageHashes must be of the same size."
            raise TypeError(msg)
        return sum(a != b for a, b in zip(self.hash, other.hash, strict=True))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageHash):
            return NotImplemented
        return self.hash == other.hash

    def __len__(self) -> int:
        return math.ceil(len(self.hash) / 8)

    def __hash__(self) -> int:
        return hash(self.hash)

    def __str__(self) -> str:
        bitstring = "".join(str(int(x)) for x in self.hash)
        return int(bitstring, 2).to_bytes(len(self)).hex()


def dhash(im: Image.Image) -> ImageHash:
    im = im.convert("L").resize((16, 16))
    pixels = list(im.getdata())
    diff = []
    for row in range(im.height):
        row_start_index = row * im.width
        for col in range(im.width - 1):
            left_pixel_index = row_start_index + col
            diff.append(pixels[left_pixel_index] < pixels[left_pixel_index + 1])

    return ImageHash(diff)
