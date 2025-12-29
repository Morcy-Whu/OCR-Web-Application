// ===== 全局状态 =====
let lastResultBlob = null;   // 保存最近一次处理结果
let lastResultType = null;   // "img" | "txt"


// ===== 原图预览 =====
function previewImage() {
    const fileInput = document.getElementById("imageInput");
    const preview = document.getElementById("inputPreview");

    if (fileInput.files.length === 0) {
        preview.src = "";
        return;
    }

    const file = fileInput.files[0];
    preview.src = URL.createObjectURL(file);
}


// ===== 提交图片并处理 =====
async function submitImage() {
    const fileInput = document.getElementById("imageInput");
    const status = document.getElementById("status");

    const outputImage = document.getElementById("outputImage");
    const outputText = document.getElementById("outputText");
    const downloadBtn = document.getElementById("downloadBtn");

    // 重置显示状态
    outputImage.style.display = "none";
    outputText.style.display = "none";
    downloadBtn.disabled = true;
    lastResultBlob = null;
    lastResultType = null;

    if (fileInput.files.length === 0) {
        alert("Please select a picture");
        return;
    }

    const file = fileInput.files[0];
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const whiteBg = document.getElementById("whiteBg").checked;

    const formData = new FormData();
    formData.append("image", file);

    if (mode === "img_img") {
        formData.append("white_background", whiteBg.toString());
    }

    status.innerText = "处理中，请稍候...";

    try {
        const response = await fetch(`/${mode}`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // ===== 根据模式展示结果 =====
        if (mode === "img_img") {
            outputImage.src = url;
            outputImage.style.display = "block";
            lastResultType = "img";
        } else {
            const text = await blob.text();
            outputText.innerText = text;
            outputText.style.display = "block";
            lastResultType = "txt";
        }

        lastResultBlob = blob;
        downloadBtn.disabled = false;
        status.innerText = "Completed ✅";

    } catch (err) {
        console.error(err);
        status.innerText = "Process failed ❌";
    }
}


// ===== 下载结果 =====
function downloadResult() {
    if (!lastResultBlob || !lastResultType) return;

    const url = URL.createObjectURL(lastResultBlob);
    const a = document.createElement("a");
    a.href = url;

    if (lastResultType === "img") {
        a.download = "ocr_result.png";
    } else {
        a.download = "ocr_result.txt";
    }

    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);
}

// ===== 缩放 & 拖拽状态 =====
let scale = 1;
let translateX = 0;
let translateY = 0;

let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;

const MIN_SCALE = 0.2;
const MAX_SCALE = 5;

const modal = document.getElementById("imgModal");
const modalImg = document.getElementById("modalImage");

// ===== 打开 modal =====
function openModal(imgElement) {
    if (!imgElement.src) return;

    modalImg.src = imgElement.src;

    resetTransform();
    modal.style.display = "flex";
}

// ===== 关闭 modal =====
function closeModal(e) {
    if (
        e.target.id === "imgModal" ||
        e.target.classList.contains("modal-close")
    ) {
        modal.style.display = "none";
        resetTransform();
        isDragging = false;
    }
}

// ===== 重置状态 =====
function resetTransform() {
    scale = 1;
    translateX = 0;
    translateY = 0;
    applyTransform();
}

// ===== 应用 transform =====
function applyTransform() {
    modalImg.style.transform =
        `translate(${translateX}px, ${translateY}px) scale(${scale})`;
}

// ===== 滚轮缩放 =====
modal.addEventListener("wheel", function (e) {
    if (modal.style.display !== "flex") return;

    e.preventDefault();

    const rect = modalImg.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale * zoomFactor));

    // 以鼠标为中心缩放
    translateX -= offsetX * (newScale / scale - 1);
    translateY -= offsetY * (newScale / scale - 1);

    scale = newScale;
    applyTransform();
}, { passive: false });

// ===== 拖拽开始 =====
modalImg.addEventListener("mousedown", function (e) {
    e.preventDefault();               // 🔥 非常关键
    isDragging = true;

    dragStartX = e.clientX - translateX;
    dragStartY = e.clientY - translateY;
});

// ===== 拖拽中 =====
window.addEventListener("mousemove", function (e) {
    if (!isDragging) return;

    translateX = e.clientX - dragStartX;
    translateY = e.clientY - dragStartY;
    applyTransform();
});

// ===== 拖拽结束 =====
window.addEventListener("mouseup", function () {
    isDragging = false;
});

// ===== ESC 关闭 =====
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        modal.style.display = "none";
        resetTransform();
        isDragging = false;
    }
});

// ===== 双击还原 =====
modalImg.addEventListener("dblclick", resetTransform);
