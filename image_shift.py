from PIL import Image
import numpy as np
from numpy.fft import rfft2, irfft2
import sys


# The smallest number for which squaring is meaningful
eps = np.sqrt(np.finfo(float).eps)


# Normalize the offset from [0, n-1] to [-n/2+1, n/2] 
def norm_offset(d: int, n: int) -> int:
    assert 0 <= d < n
    return d if d <= n // 2 else d - n


# Calculates the shift of the graph of the second real-valued discrete function of two variables relative to the first one.
# Returns (dy, dx)
def offset2real(f1: np.ndarray, f2: np.ndarray) -> tuple[int, int]:
    assert f1.ndim == 2
    assert f1.shape[0] > 0 and f1.shape[1] > 0
    assert f1.shape == f2.shape
    h, w = f1.shape
    # Fourier transform of functions
    F1 = rfft2(f1)
    F2 = rfft2(f2)
    # Only half of the coefficients were calculated, since the functions are real-valued
    w_ = w // 2 + 1
    assert F1.shape[1] == w_
    # Approximation of the complex exponential.
    # It is also the Fourier transform of a real-valued function, so we calculate half the Fourier coefficients.
    c = np.empty((h, w_), dtype=complex)
    for i in range(h):
        for j in range(w_):
            t = F2[i, j] * np.conj(F1[i, j])
            c[i, j] = t / np.abs(t) if np.abs(t.real) + np.abs(t.imag) > eps else 1
    # Approximation of the delta function
    c_inv = irfft2(c)
    # The sought for displacement
    d = np.unravel_index(c_inv.argmax(), c_inv.shape)
    d = (int(d[0]), int(d[1]))
    # Take the periodicity into account
    return norm_offset(d[0], h), norm_offset(d[1], w)


# Check command-line arguments
if len(sys.argv) < 3:
    print("Usage: python image_shift.py <image1> <image2> [output]")
    sys.exit(1)

img1_path = sys.argv[1]
img2_path = sys.argv[2]
output_path = sys.argv[3] if len(sys.argv) >= 4 else "output.jpg"  # default output    

with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
    arr1 = np.array(img1, dtype=np.uint8)
    arr2 = np.array(img2, dtype=np.uint8)
    d = 0, 0
    # Calculate the offset for each color channel and take the average
    for c in range(3):
        f1 = arr1[:, :, c]
        f2 = arr2[:, :, c]
        dd = offset2real(f1, f2)
        d = (d[0] + dd[0], d[1] + dd[1])
    d = (round(d[0] / 3), round(d[1] / 3))
    print("Offset:", d)
    img0 = img2.transform(img2.size, Image.Transform.AFFINE, (1, 0, d[1], 0, 1, d[0]))
    img0.save(output_path)
