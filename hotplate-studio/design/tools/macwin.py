"""Captura de una ventana propia en macOS vía CoreGraphics (ctypes, sin pyobjc).

Funciona aunque la ventana no esté visible (otro Space, tapada por el editor).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
from typing import Optional

from PIL import Image

_cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))
_cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation"))

_vp = ctypes.c_void_p
_cf.CFArrayGetCount.restype = ctypes.c_long
_cf.CFArrayGetCount.argtypes = [_vp]
_cf.CFArrayGetValueAtIndex.restype = _vp
_cf.CFArrayGetValueAtIndex.argtypes = [_vp, ctypes.c_long]
_cf.CFDictionaryGetValue.restype = _vp
_cf.CFDictionaryGetValue.argtypes = [_vp, _vp]
_cf.CFStringCreateWithCString.restype = _vp
_cf.CFStringCreateWithCString.argtypes = [_vp, ctypes.c_char_p, ctypes.c_uint32]
_cf.CFNumberGetValue.restype = ctypes.c_bool
_cf.CFNumberGetValue.argtypes = [_vp, ctypes.c_int, _vp]
_cf.CFRelease.argtypes = [_vp]
_cf.CFDataGetLength.restype = ctypes.c_long
_cf.CFDataGetLength.argtypes = [_vp]
_cf.CFDataGetBytePtr.restype = ctypes.POINTER(ctypes.c_uint8)
_cf.CFDataGetBytePtr.argtypes = [_vp]

_cg.CGWindowListCopyWindowInfo.restype = _vp
_cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]


class _CGRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double),
                ("w", ctypes.c_double), ("h", ctypes.c_double)]


_cg.CGWindowListCreateImage.restype = _vp
_cg.CGWindowListCreateImage.argtypes = [_CGRect, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
for name in ("CGImageGetWidth", "CGImageGetHeight", "CGImageGetBytesPerRow",
             "CGImageGetBitsPerPixel"):
    getattr(_cg, name).restype = ctypes.c_size_t
    getattr(_cg, name).argtypes = [_vp]
_cg.CGImageGetDataProvider.restype = _vp
_cg.CGImageGetDataProvider.argtypes = [_vp]
_cg.CGDataProviderCopyData.restype = _vp
_cg.CGDataProviderCopyData.argtypes = [_vp]
_cg.CGImageRelease.argtypes = [_vp]

_UTF8 = 0x08000100
_SINT64 = 4
_LIST_ALL = 0
_INCLUDING_WINDOW = 1 << 3
_BOUNDS_IGNORE_FRAMING = 1 << 0
_NOMINAL_RESOLUTION = 1 << 4
_NULL_RECT = _CGRect(float("inf"), float("inf"), 0.0, 0.0)


def _key(text: str) -> int:
    return _cf.CFStringCreateWithCString(None, text.encode(), _UTF8)


_K_PID = _key("kCGWindowOwnerPID")
_K_NUM = _key("kCGWindowNumber")
_K_LAYER = _key("kCGWindowLayer")


def _num(d: int, key: int) -> Optional[int]:
    ref = _cf.CFDictionaryGetValue(d, key)
    if not ref:
        return None
    out = ctypes.c_int64()
    _cf.CFNumberGetValue(ref, _SINT64, ctypes.byref(out))
    return out.value


def own_window_ids() -> list[int]:
    arr = _cg.CGWindowListCopyWindowInfo(_LIST_ALL, 0)
    ids = []
    pid = os.getpid()
    try:
        for i in range(_cf.CFArrayGetCount(arr)):
            d = _cf.CFArrayGetValueAtIndex(arr, i)
            if _num(d, _K_PID) == pid:
                ids.append(_num(d, _K_NUM))
    finally:
        _cf.CFRelease(arr)
    return [i for i in ids if i is not None]


def grab_window(wid: int) -> Optional[Image.Image]:
    img = _cg.CGWindowListCreateImage(
        _NULL_RECT, _INCLUDING_WINDOW, wid, _BOUNDS_IGNORE_FRAMING | _NOMINAL_RESOLUTION
    )
    if not img:
        return None
    try:
        w, h = _cg.CGImageGetWidth(img), _cg.CGImageGetHeight(img)
        stride = _cg.CGImageGetBytesPerRow(img)
        data = _cg.CGDataProviderCopyData(_cg.CGImageGetDataProvider(img))
        try:
            n = _cf.CFDataGetLength(data)
            raw = ctypes.string_at(_cf.CFDataGetBytePtr(data), n)
        finally:
            _cf.CFRelease(data)
    finally:
        _cg.CGImageRelease(img)
    if w == 0 or h == 0:
        return None
    return Image.frombuffer("RGBA", (w, h), raw, "raw", "BGRA", stride, 1).convert("RGB")
