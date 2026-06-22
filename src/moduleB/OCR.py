"""模块 B 操作说明 OCR 工具。

用法示例：
    python3 src/moduleB/OCR.py src/moduleB/samples/operation_instruction.jpg
    python3 src/moduleB/OCR.py image.jpg --paragraph --gpu
"""

from __future__ import annotations

import argparse
from pathlib import Path


def extract_text(image_path: Path, gpu: bool = False, paragraph: bool = False) -> list[str]:
    """使用 EasyOCR 识别图片中的中文/英文操作说明。"""
    try:
        import easyocr
    except ImportError as exc:
        raise SystemExit(
            "未安装 easyocr。请先执行：python3 -m pip install -r src/moduleB/requirements.txt"
        ) from exc

    if not image_path.exists():
        raise SystemExit(f"图片不存在：{image_path}")

    reader = easyocr.Reader(["ch_sim", "en"], gpu=gpu)
    result = reader.readtext(str(image_path), detail=0, paragraph=paragraph)
    return [text.strip() for text in result if text.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="识别模块 B 操作说明图片中的文字")
    parser.add_argument(
        "image",
        nargs="?",
        default=str(Path(__file__).with_name("test.jpg")),
        help="待识别图片路径；默认读取 src/moduleB/test.jpg",
    )
    parser.add_argument("--gpu", action="store_true", help="使用 GPU 加速 OCR")
    parser.add_argument("--paragraph", action="store_true", help="合并相邻文本块为段落")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    lines = extract_text(Path(args.image), gpu=args.gpu, paragraph=args.paragraph)
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
