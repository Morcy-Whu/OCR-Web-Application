import os
from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
from utility import ocr_to_txt_with_layout,text_extraction_image

# ===== 引入你已有的函数 =====
# 假设这些函数就在同一个文件，或已被正确 import
# text_extraction_image
# ocr_to_txt_with_layout

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/img_txt", methods=["POST"])
def img_to_txt():
    """
    图像 -> 文本
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = secure_filename(file.filename)

    input_path = os.path.join(UPLOAD_DIR, filename)
    base, _ = os.path.splitext(filename)
    output_path = os.path.join(OUTPUT_DIR, base + ".txt")

    file.save(input_path)

    # OCR -> txt
    ocr_to_txt_with_layout(
        input_path,
        output_path,
        line_height_threshold=10,
        char_per_pixel=0.05
    )

    return send_file(
        output_path,
        as_attachment=True,
        download_name=base + ".txt"
    )


@app.route("/img_img", methods=["POST"])
def img_to_img():
    """
    图像 -> 图像
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    white_background = request.form.get("white_background", "true").lower() == "true"

    file = request.files["image"]
    filename = secure_filename(file.filename)

    input_path = os.path.join(UPLOAD_DIR, filename)
    base, ext = os.path.splitext(filename)
    output_path = os.path.join(OUTPUT_DIR, base + "_text" + ext)

    file.save(input_path)

    # OCR -> image
    text_extraction_image(
        input_path,
        output_path,
        white_background=white_background
    )

    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
