#!/usr/bin/env python3
"""小红书图片生成器 CLI"""

import argparse
import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from xhs_image_generator import XHSImageGenerator

def main():
    parser = argparse.ArgumentParser(description="小红书图片生成器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # generate 命令
    generate_parser = subparsers.add_parser("generate", help="生成图片系列")
    generate_parser.add_argument("--content-file", required=True, help="内容文件路径")
    generate_parser.add_argument("--title", help="标题")
    generate_parser.add_argument("--style", help="视觉风格")
    generate_parser.add_argument("--layout", help="布局")
    generate_parser.add_argument("--preset", help="预设")
    generate_parser.add_argument("--image-count", type=int, help="图片数量")
    generate_parser.add_argument("--output-dir", help="输出目录")
    
    # styles 命令
    subparsers.add_parser("styles", help="列出可用风格")
    
    # layouts 命令
    subparsers.add_parser("layouts", help="列出可用布局")
    
    # presets 命令
    subparsers.add_parser("presets", help="列出可用预设")
    
    # generate-for-publish 命令
    publish_parser = subparsers.add_parser("generate-for-publish", help="为发布生成图片")
    publish_parser.add_argument("--title-file", required=True, help="标题文件路径")
    publish_parser.add_argument("--content-file", required=True, help="内容文件路径")
    publish_parser.add_argument("--style", default="cute", help="视觉风格")
    publish_parser.add_argument("--layout", default="balanced", help="布局")
    publish_parser.add_argument("--image-count", type=int, default=3, help="图片数量")
    
    args = parser.parse_args()
    
    generator = XHSImageGenerator()
    
    if args.command == "generate":
        # 读取内容
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        result = generator.generate_infographic_series(
            content=content,
            title=args.title,
            style=args.style,
            layout=args.layout,
            preset=args.preset,
            image_count=args.image_count,
            output_dir=args.output_dir
        )
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.command == "styles":
        styles = generator.get_available_styles()
        print(json.dumps({"styles": styles}, ensure_ascii=False, indent=2))
        
    elif args.command == "layouts":
        layouts = generator.get_available_layouts()
        print(json.dumps({"layouts": layouts}, ensure_ascii=False, indent=2))
        
    elif args.command == "presets":
        presets = generator.get_available_presets()
        print(json.dumps({"presets": presets}, ensure_ascii=False, indent=2))
        
    elif args.command == "generate-for-publish":
        # 读取标题和内容
        with open(args.title_file, "r", encoding="utf-8") as f:
            title = f.read().strip()
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        result = generator.generate_for_publish(
            title=title,
            content=content,
            style=args.style,
            layout=args.layout,
            image_count=args.image_count
        )
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()