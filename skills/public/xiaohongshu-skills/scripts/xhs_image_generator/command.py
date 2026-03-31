"""图片生成子命令实现"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def cmd_generate_images(args):
    """生成小红书信息图系列"""
    from xhs_image_generator import XHSImageGenerator
    
    # 读取内容
    with open(args.content_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    generator = XHSImageGenerator()
    result = generator.generate_infographic_series(
        content=content,
        title=args.title,
        style=args.style,
        layout=args.layout,
        preset=args.preset,
        image_count=args.image_count,
        output_dir=args.output_dir
    )
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success", False) else 2)

def cmd_generate_for_publish(args):
    """为发布流程生成图片"""
    from xhs_image_generator import XHSImageGenerator
    
    # 读取标题和内容
    with open(args.title_file, "r", encoding="utf-8") as f:
        title = f.read().strip()
    with open(args.content_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    generator = XHSImageGenerator()
    result = generator.generate_for_publish(
        title=title,
        content=content,
        style=args.style,
        layout=args.layout,
        image_count=args.image_count
    )
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success", False) else 2)

def cmd_list_styles(args):
    """列出可用风格"""
    from xhs_image_generator import XHSImageGenerator
    
    generator = XHSImageGenerator()
    styles = generator.get_available_styles()
    print(json.dumps({"styles": styles}, ensure_ascii=False, indent=2))

def cmd_list_layouts(args):
    """列出可用布局"""
    from xhs_image_generator import XHSImageGenerator
    
    generator = XHSImageGenerator()
    layouts = generator.get_available_layouts()
    print(json.dumps({"layouts": layouts}, ensure_ascii=False, indent=2))

def cmd_list_presets(args):
    """列出可用预设"""
    from xhs_image_generator import XHSImageGenerator
    
    generator = XHSImageGenerator()
    presets = generator.get_available_presets()
    print(json.dumps({"presets": presets}, ensure_ascii=False, indent=2))