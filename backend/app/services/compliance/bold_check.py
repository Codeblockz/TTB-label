import logging
import re

import cv2
import numpy as np

from app.services.ocr.base import OCRLine

logger = logging.getLogger(__name__)

MIN_BODY_LINE_LENGTH = 10
BOLD_RATIO_THRESHOLD = 1.25
CROP_PADDING_PX = 5


def _crop_line_region(
    image: np.ndarray,
    polygon: list[tuple[int, int]],
) -> np.ndarray | None:
    """Crop a rectangular region from image using bounding polygon + padding."""
    if len(polygon) < 2:
        return None

    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    h, w = image.shape[:2]

    x_min = max(0, min(xs) - CROP_PADDING_PX)
    x_max = min(w, max(xs) + CROP_PADDING_PX)
    y_min = max(0, min(ys) - CROP_PADDING_PX)
    y_max = min(h, max(ys) + CROP_PADDING_PX)

    if x_max <= x_min or y_max <= y_min:
        return None

    return image[y_min:y_max, x_min:x_max]


def _median_run_length(crop: np.ndarray) -> float:
    """Compute median horizontal run length of foreground pixels.

    For each row, measures lengths of consecutive foreground pixel runs.
    Bold text produces longer runs due to thicker strokes. Returns 0.0
    if no foreground pixels exist.
    """
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    padded = np.pad(binary // 255, ((0, 0), (1, 1)), constant_values=0).astype(np.int16)
    diffs = np.diff(padded, axis=1)
    starts = np.argwhere(diffs > 0)
    ends = np.argwhere(diffs < 0)

    if len(starts) == 0 or len(ends) == 0:
        return 0.0

    min_len = min(len(starts), len(ends))
    if min_len == 0:
        return 0.0
    run_lengths = ends[:min_len, 1] - starts[:min_len, 1]
    return float(np.median(run_lengths))


def _crop_header_portion(
    image: np.ndarray,
    header_line: "OCRLine",
) -> np.ndarray | None:
    """Crop just the 'GOVERNMENT WARNING:' portion from the header line.

    When the header shares a line with body text (e.g. "GOVERNMENT WARNING: (1) According..."),
    we estimate the x-position where the header ends based on character proportion.
    """
    match = re.search(r"government\s+warning:?", header_line.text, re.IGNORECASE)
    if not match:
        return None

    header_end_char = match.end()
    total_chars = len(header_line.text)

    if total_chars == 0:
        return None

    polygon = header_line.bounding_polygon
    if len(polygon) < 2:
        return None

    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    h, w = image.shape[:2]

    x_min = max(0, min(xs) - CROP_PADDING_PX)
    x_max_full = min(w, max(xs) + CROP_PADDING_PX)
    y_min = max(0, min(ys) - CROP_PADDING_PX)
    y_max = min(h, max(ys) + CROP_PADDING_PX)

    if x_max_full <= x_min or y_max <= y_min:
        return None

    # Estimate x position where header text ends
    line_width = x_max_full - x_min
    header_fraction = header_end_char / total_chars
    x_max_header = x_min + int(line_width * header_fraction)

    return image[y_min:y_max, x_min:x_max_header]


def _find_header_line(ocr_lines: list[OCRLine]) -> OCRLine | None:
    """Find the OCR line containing 'GOVERNMENT WARNING'."""
    for line in ocr_lines:
        if re.search(r"government\s+warning", line.text, re.IGNORECASE):
            return line
    return None


def _find_body_line(
    ocr_lines: list[OCRLine],
    header_line: OCRLine,
) -> OCRLine | None:
    """Find the first substantive body text line after the header."""
    found_header = False
    for line in ocr_lines:
        if line is header_line:
            found_header = True
            continue
        if not found_header:
            continue
        # Must be substantive text (>10 chars, has letters)
        if len(line.text) > MIN_BODY_LINE_LENGTH and re.search(r"[a-zA-Z]", line.text):
            return line
    return None


def check_bold_opencv(
    image_path: str,
    ocr_lines: list[OCRLine],
) -> bool | None:
    """Check if GOVERNMENT WARNING header is bold compared to body text.

    Returns True if bold, False if not bold, None if unable to determine.
    """
    header_line = _find_header_line(ocr_lines)
    if header_line is None:
        logger.info("Bold check: GOVERNMENT WARNING header not found in OCR lines")
        return None

    body_line = _find_body_line(ocr_lines, header_line)
    if body_line is None:
        logger.info("Bold check: no substantive body text found after header")
        return None

    image = cv2.imread(image_path)
    if image is None:
        logger.warning("Bold check: failed to load image %s", image_path)
        return None

    header_crop = _crop_header_portion(image, header_line)
    body_crop = _crop_line_region(image, body_line.bounding_polygon)

    if header_crop is None or body_crop is None:
        logger.info("Bold check: failed to crop text regions")
        return None

    header_run = _median_run_length(header_crop)
    body_run = _median_run_length(body_crop)

    if body_run == 0:
        logger.info("Bold check: body run length is zero")
        return None

    ratio = header_run / body_run
    is_bold = ratio >= BOLD_RATIO_THRESHOLD

    logger.info(
        "Run-length ratio: %.2f (header=%.2f, body=%.2f) → %s",
        ratio, header_run, body_run, "BOLD" if is_bold else "NOT BOLD",
    )

    return is_bold
