"""发布编排器：下载 → 登录检查 → 发布 → 报告。"""

from __future__ import annotations

import json
import logging
import os
import sys

from image_downloader import process_images
from title_utils import calc_title_length
from xhs.cdp import Browser
from xhs.login import check_login_status
from xhs.publish import publish_image_content
from xhs.publish_video import publish_video_content
from xhs.types import PublishImageContent, PublishVideoContent

# 导入图片生成器
try:
    from xhs_image_generator import XHSImageGenerator
    IMAGE_GENERATOR_AVAILABLE = True
except ImportError:
    IMAGE_GENERATOR_AVAILABLE = False
    logger.warning("图片生成器模块不可用，请确保已正确安装")

logger = logging.getLogger(__name__)


def run_publish_pipeline(
    title: str,
    content: str,
    images: list[str] | None = None,
    video: str | None = None,
    tags: list[str] | None = None,
    schedule_time: str | None = None,
    is_original: bool = False,
    visibility: str = "",
    host: str = "127.0.0.1",
    port: int = 9222,
    account: str = "",
    headless: bool = False,
    generate_images: bool = False,
    image_style: str = None,
    image_layout: str = None,
    image_preset: str = None,
    image_count: int = 3,
) -> dict:
    """执行完整发布流水线。

    当 headless=True 且未登录时，自动降级到有窗口模式。

    Args:
        title: 标题
        content: 正文内容
        images: 图片路径或URL列表
        video: 视频文件路径
        tags: 标签列表
        schedule_time: 定时发布时间
        is_original: 是否声明原创
        visibility: 可见范围
        host: 浏览器主机地址
        port: 浏览器端口
        account: 账户标识
        headless: 是否无头模式
        generate_images: 是否自动生成图片
        image_style: 图片风格（cute, fresh, warm, bold, minimal, retro, pop, notion, chalkboard, study-notes, screen-print）
        image_layout: 图片布局（sparse, balanced, dense, list, comparison, flow, mindmap, quadrant）
        image_preset: 图片预设（knowledge-card, checklist, tutorial, poster, cinematic, etc.）
        image_count: 图片数量（2-10）

    Returns:
        发布结果字典。
    """
    # 标题长度校验
    title_len = calc_title_length(title)
    if title_len > 20:
        return {"success": False, "error": f"标题长度超限: {title_len}/20"}

    # 处理图片（下载 URL / 验证本地路径）
    local_images: list[str] = []
    
    # 如果启用了图片生成，则生成图片
    if generate_images:
        if not IMAGE_GENERATOR_AVAILABLE:
            return {"success": False, "error": "图片生成器模块不可用，无法生成图片"}
        
        try:
            generator = XHSImageGenerator()
            result = generator.generate_infographic_series(
                content=content,
                title=title,
                style=image_style,
                layout=image_layout,
                preset=image_preset,
                image_count=image_count
            )
            
            if result["success"]:
                local_images = result["images"]
                logger.info(f"成功生成 {len(local_images)} 张图片")
            else:
                return {"success": False, "error": f"图片生成失败: {result.get('error', '未知错误')}"}
    elif images:
        local_images = process_images(images)
        if not local_images:
            return {"success": False, "error": "没有有效的图片"}

    # 连接浏览器
    browser = Browser(host=host, port=port)
    browser.connect()

    try:
        page = browser.new_page()
        try:
            # 登录检查
            if not check_login_status(page):
                browser.close_page(page)
                browser.close()

                # Headless 自动降级：切换到有窗口模式
                if headless:
                    from chrome_launcher import restart_chrome

                    logger.info("Headless 模式未登录，切换到有窗口模式...")
                    restart_chrome(port=port, headless=False)
                    return {
                        "success": False,
                        "error": "未登录",
                        "action": "switched_to_headed",
                        "message": "已切换到有窗口模式，请在浏览器中扫码登录",
                        "exit_code": 1,
                    }

                return {
                    "success": False,
                    "error": "未登录",
                    "exit_code": 1,
                }

            # 发布
            if video:
                publish_video_content(
                    page,
                    PublishVideoContent(
                        title=title,
                        content=content,
                        tags=tags or [],
                        video_path=video,
                        schedule_time=schedule_time,
                        visibility=visibility,
                    ),
                )
            else:
                publish_image_content(
                    page,
                    PublishImageContent(
                        title=title,
                        content=content,
                        tags=tags or [],
                        image_paths=local_images,
                        schedule_time=schedule_time,
                        is_original=is_original,
                        visibility=visibility,
                    ),
                )

            return {
                "success": True,
                "title": title,
                "content_length": len(content),
                "images": len(local_images),
                "video": video or "",
                "status": "发布完成",
            }

        finally:
            browser.close_page(page)
    finally:
        browser.close()


def main() -> None:
    """CLI 入口（被 cli.py 的 publish/publish-video 子命令调用时使用）。"""
    import argparse

    parser = argparse.ArgumentParser(description="小红书发布流水线")
    parser.add_argument("--title-file", required=True, help="标题文件路径")
    parser.add_argument("--content-file", required=True, help="正文文件路径")
    parser.add_argument("--images", nargs="*", help="图片路径或 URL 列表")
    parser.add_argument("--video", help="视频文件路径")
    parser.add_argument("--tags", nargs="*", help="标签列表")
    parser.add_argument("--schedule-at", help="定时发布时间 (ISO8601)")
    parser.add_argument("--original", action="store_true", help="声明原创")
    parser.add_argument("--visibility", default="", help="可见范围")
    parser.add_argument("--headless", action="store_true", help="无头模式（未登录自动降级）")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--account", default="")
    
    # 图片生成参数
    parser.add_argument("--generate-images", action="store_true", help="自动生成图片")
    parser.add_argument("--image-style", help="图片风格（cute, fresh, warm, bold, minimal, retro, pop, notion, chalkboard, study-notes, screen-print）")
    parser.add_argument("--image-layout", help="图片布局（sparse, balanced, dense, list, comparison, flow, mindmap, quadrant）")
    parser.add_argument("--image-preset", help="图片预设（knowledge-card, checklist, tutorial, poster, cinematic, etc.）")
    parser.add_argument("--image-count", type=int, default=3, help="图片数量（2-10）")
    
    args = parser.parse_args()

    # 读取标题和正文
    with open(args.title_file, encoding="utf-8") as f:
        title = f.read().strip()
    with open(args.content_file, encoding="utf-8") as f:
        content = f.read().strip()

    result = run_publish_pipeline(
        title=title,
        content=content,
        images=args.images,
        video=args.video,
        tags=args.tags,
        schedule_time=args.schedule_at,
        is_original=args.original,
        visibility=args.visibility,
        host=args.host,
        port=args.port,
        account=args.account,
        headless=args.headless,
        generate_images=args.generate_images,
        image_style=args.image_style,
        image_layout=args.image_layout,
        image_preset=args.image_preset,
        image_count=args.image_count,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    exit_code = result.get("exit_code", 0 if result["success"] else 2)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
