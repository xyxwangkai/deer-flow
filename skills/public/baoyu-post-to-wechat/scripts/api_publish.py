#!/usr/bin/env python3
"""
微信公众号API发布脚本
支持通过微信公众号API发布文章和图文内容
"""

import argparse
import json
import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_config(config_file: str = "config/api_credentials.json") -> Dict[str, Any]:
    """加载API配置，优先使用环境变量"""
    config = {}
    
    # 优先从环境变量读取
    app_id = os.getenv("WECHAT_APP_ID")
    app_secret = os.getenv("WECHAT_APP_SECRET")
    access_token = os.getenv("WECHAT_ACCESS_TOKEN")
    
    if app_id and app_secret:
        config["app_id"] = app_id
        config["app_secret"] = app_secret
        if access_token:
            config["access_token"] = access_token
        print("使用环境变量配置")
        return config
    
    # 如果环境变量不存在，回退到配置文件
    config_path = project_root / config_file
    if not config_path.exists():
        print(f"错误: 配置文件不存在且环境变量未设置: {config_path}")
        print("请设置环境变量 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
        print("或者创建配置文件，包含以下字段:")
        print(json.dumps({
            "app_id": "YOUR_APP_ID",
            "app_secret": "YOUR_APP_SECRET",
            "access_token": "YOUR_ACCESS_TOKEN"
        }, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        print("使用配置文件")
        return json.load(f)

def get_access_token(app_id: str, app_secret: str) -> str:
    """获取微信公众号access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "access_token" in data:
            return data["access_token"]
        else:
            print(f"获取access_token失败: {data}")
            sys.exit(1)
    except Exception as e:
        print(f"获取access_token时出错: {e}")
        sys.exit(1)

def upload_image(access_token: str, image_path: str) -> Optional[str]:
    """上传图片到微信公众号素材库"""
    if not os.path.exists(image_path):
        print(f"图片文件不存在: {image_path}")
        return None
    
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("url"):
                return data["url"]
            else:
                print(f"上传图片失败: {data}")
                return None
    except Exception as e:
        print(f"上传图片时出错: {e}")
        return None

def upload_cover_image_to_material(access_token: str, image_path: str) -> Optional[str]:
    """上传封面图片到素材库并返回media_id"""
    if not os.path.exists(image_path):
        print(f"封面图片文件不存在: {image_path}")
        return None
    
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("media_id"):
                return data["media_id"]
            else:
                print(f"上传封面图片到素材库失败: {data}")
                return None
    except Exception as e:
        print(f"上传封面图片到素材库时出错: {e}")
        return None

def create_draft(access_token: str, title: str, content: str, 
                 author: str = "", digest: str = "", 
                 cover_media_id: str = "", need_open_comment: int = 0,
                 only_fans_can_comment: int = 0) -> Dict[str, Any]:
    """创建草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    # 构建文章数据
    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": "",
        "thumb_media_id": cover_media_id,
        "need_open_comment": need_open_comment,
        "only_fans_can_comment": only_fans_can_comment,
        "show_cover_pic": 1 if cover_media_id else 0
    }
    
    payload = {"articles": [article]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"创建草稿时出错: {e}")
        return {"errcode": -1, "errmsg": str(e)}

def publish_draft(access_token: str, media_id: str) -> Dict[str, Any]:
    """发布草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
    
    payload = {"media_id": media_id}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"发布草稿时出错: {e}")
        return {"errcode": -1, "errmsg": str(e)}

def convert_markdown_to_html(markdown_content: str) -> str:
    """将Markdown转换为HTML（简化版）"""
    # 这里可以使用第三方库如markdown2或mistune
    # 简化实现：基本转换
    html = markdown_content
    html = html.replace('\n', '<br>')
    html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
    html = html.replace('*', '<em>', 1).replace('*', '</em>', 1)
    html = html.replace('# ', '<h1>').replace('\n', '</h1>', 1)
    html = html.replace('## ', '<h2>').replace('\n', '</h2>', 1)
    html = html.replace('### ', '<h3>').replace('\n', '</h3>', 1)
    return f"<div>{html}</div>"

def read_content_file(file_path: str) -> str:
    """读取内容文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)

def save_access_token_to_config(access_token: str, config_file: str = "config/api_credentials.json"):
    """将access_token保存到配置文件"""
    config_path = project_root / config_file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["access_token"] = access_token
        config["access_token_timestamp"] = int(time.time())
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("access_token已保存到配置文件")
    except Exception as e:
        print(f"保存access_token时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="微信公众号API发布工具")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--content", help="文章内容（直接提供）")
    parser.add_argument("--content-file", help="文章内容文件路径")
    parser.add_argument("--type", default="article", choices=["article", "image-text"], help="内容类型")
    parser.add_argument("--format", default="html", choices=["html", "markdown"], help="内容格式")
    parser.add_argument("--cover", help="封面图片路径")
    parser.add_argument("--summary", default="", help="文章摘要")
    parser.add_argument("--author", default="", help="作者")
    parser.add_argument("--tags", help="标签，逗号分隔")
    parser.add_argument("--draft", action="store_true", help="保存为草稿")
    parser.add_argument("--publish", action="store_true", help="直接发布")
    parser.add_argument("--comments", default="open", choices=["open", "fans-only", "closed"], 
                       help="评论设置")
    
    args = parser.parse_args()
    
    # 读取内容
    if args.content_file:
        content = read_content_file(args.content_file)
    elif args.content:
        content = args.content
    else:
        print("错误: 必须提供--content或--content-file参数")
        sys.exit(1)
    
    # 转换格式
    if args.format == "markdown":
        content = convert_markdown_to_html(content)
    
    # 加载配置
    config = load_config()
    
    # 获取access_token（如果配置中没有）
    access_token = config.get("access_token")
    app_id = config.get("app_id")
    app_secret = config.get("app_secret")
    if not app_id or not app_secret:
        print("错误: 配置文件中缺少app_id和app_secret")
        sys.exit(1)
    access_token = get_access_token(app_id, app_secret)
        
    # 上传封面图片
    cover_media_id = ""
    if args.cover:
        # 简化处理，实际需要调用素材管理接口
        # 补充：上传封面图片到素材库并获取media_id
        cover_media_id = upload_cover_image_to_material(access_token, args.cover)
        if cover_media_id:
            print(f"封面图片素材ID: {cover_media_id}")
        else:
            print("警告: 封面图片上传到素材库失败，将使用默认封面")            
    
    # 设置评论参数
    need_open_comment = 1
    only_fans_can_comment = 0
    if args.comments == "fans-only":
        only_fans_can_comment = 1
    elif args.comments == "closed":
        need_open_comment = 0
    
    # 创建草稿
    print(f"创建草稿: {args.title}")
    result = create_draft(
        access_token=access_token,
        title=args.title,
        content=content,
        author=args.author,
        digest=args.summary,
        cover_media_id=cover_media_id,
        need_open_comment=need_open_comment,
        only_fans_can_comment=only_fans_can_comment
    )
    
    if result.get("media_id") != "":
        media_id = result.get("media_id")
        print(f"草稿创建成功! media_id: {media_id}")
        
        # 如果需要直接发布
        if args.publish:
            print("发布草稿...")
            publish_result = publish_draft(access_token, media_id)
            if publish_result.get("errcode") == 0:
                print("发布成功!")
                print(f"发布ID: {publish_result.get('publish_id')}")
            else:
                print(f"发布失败: {publish_result}")
        else:
            print("已保存为草稿")
            print(f"草稿管理地址: https://mp.weixin.qq.com")
    else:
        print(f"创建草稿失败: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()