import os

# 必须在 import paddleocr / paddlex 之前
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "1"
import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont
import requests

# ========= 全局缓存 =========
_ocr_result_cache = {}
_image_cache = {}
_font_cache = {}
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False)


def _get_font(font_path, font_size):
    key = (font_path, font_size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path, font_size)
    return _font_cache[key]

def _load_image(image_path_or_url):
    if image_path_or_url in _image_cache:
        return _image_cache[image_path_or_url].copy()

    if image_path_or_url.startswith("http"):
        resp = requests.get(image_path_or_url, timeout=5)
        img_array = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(image_path_or_url)

    if img is None:
        raise ValueError("无法读取图片")

    _image_cache[image_path_or_url] = img
    return img.copy()

def _get_ocr_result(image_path_or_url):
    if image_path_or_url not in _ocr_result_cache:
        _ocr_result_cache[image_path_or_url] = ocr.predict(image_path_or_url)[0]
    return _ocr_result_cache[image_path_or_url]

def text_extraction_image(image_path_or_url, output_path="text_only.png", white_background=True, font_path=None):
    # 1. OCR（缓存）
    res = _get_ocr_result(image_path_or_url)

    # 2. 图片（缓存）
    img = _load_image(image_path_or_url)

    h, w = img.shape[:2]
    if white_background:
        img[:] = 255  # 原地白底，避免新分配

    # OpenCV → PIL
    img_pil = Image.fromarray(img[:, :, ::-1])
    draw = ImageDraw.Draw(img_pil)

    # 字体（缓存）
    if font_path is None:
        font_path = "C:/Windows/Fonts/simhei.ttf"
    font = _get_font(font_path, 20)

    # 画文字
    for text, box in zip(res['rec_texts'], res['dt_polys']):
        x, y = box[0]
        draw.text((x, y - 10), text, font=font, fill=(0, 0, 0))

    # 保存
    cv2.imwrite(output_path, np.array(img_pil)[:, :, ::-1])
def ocr_to_txt_with_layout(image_path_or_url, output_txt="ocr_output.txt",
                           line_height_threshold=10, char_per_pixel=0.05):
    # OCR（缓存）
    res = _get_ocr_result(image_path_or_url)

    texts = res['rec_texts']
    boxes = res['dt_polys']

    positions = [(text, box[0][0], box[0][1]) for text, box in zip(texts, boxes)]
    positions.sort(key=lambda x: x[2])

    lines, current_line = [], []
    current_y = None

    for text, x, y in positions:
        if current_y is None or abs(y - current_y) <= line_height_threshold:
            current_line.append((x, text))
            current_y = y if current_y is None else current_y
        else:
            lines.append(sorted(current_line))
            current_line = [(x, text)]
            current_y = y

    if current_line:
        lines.append(sorted(current_line))

    with open(output_txt, "w", encoding="utf-8") as f:
        for line in lines:
            last_x = 0
            buf = []
            for x, text in line:
                spaces = max(int((x - last_x) * char_per_pixel), 0)
                buf.append(" " * spaces + text)
                last_x = x
            f.write("".join(buf) + "\n")

def batch_images_images(input_dir, output_dir,white_background):
    """
    遍历 input_dir 下的所有图片，并调用 process_image
    """
    # 支持的图片格式
    image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    # 如果输出目录不存在，则创建
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(image_exts):
            input_path = os.path.join(input_dir, filename)
            base, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, base + "_processed" + ext)

            text_extraction_image(input_path, output_path,white_background)
            print(f"Processed: {filename}")


def batch_images_txt(input_dir, output_dir,line_height_threshold=10, char_per_pixel=0.05):
    new_ext = ".txt"
    """
    遍历 input_dir 下的所有图片，并调用 process_image
    """
    # 支持的图片格式
    image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    # 如果输出目录不存在，则创建
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(image_exts):
            base, _ = os.path.splitext(filename)
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, (base + new_ext))

            ocr_to_txt_with_layout(input_path, output_path,line_height_threshold, char_per_pixel)
            print(f"Processed: {filename}")