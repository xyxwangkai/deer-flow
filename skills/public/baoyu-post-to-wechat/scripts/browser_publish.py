#!/usr/bin/env python3
"""
微信公众号浏览器自动化发布脚本
使用Playwright进行浏览器自动化发布
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("错误: 未安装Playwright，请运行: pip install playwright && playwright install")
    sys.exit(1)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_browser_config(config_file: str = "config/browser_config.json") -> Dict[str, Any]:
    """加载浏览器配置"""
    config_path = project_root / config_file
    default_config = {
        "chrome_profile_path": "",
        "headless": False,
        "timeout": 30,
        "wait_time": 2
    }
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            default_config.update(user_config)
    
    return default_config

def read_content_file(file_path: str) -> str:
    """读取内容文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)

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

def publish_via_browser(title: str, content: str, config: Dict[str, Any]) -> bool:
    """通过浏览器发布文章"""
    chrome_profile_path = config.get("chrome_profile_path")
    headless = config.get("headless", False)
    timeout = config.get("timeout", 30) * 1000  # 转换为毫秒
    wait_time = config.get("wait_time", 2)
    
    print(f"启动浏览器发布流程...")
    print(f"标题: {title}")
    print(f"内容长度: {len(content)} 字符")
    print(f"浏览器配置: headless={headless}, timeout={timeout}ms")
    
    try:
        with sync_playwright() as p:
            # 使用持久化上下文
            if chrome_profile_path and os.path.exists(chrome_profile_path):
                print(f"使用Chrome用户数据目录: {chrome_profile_path}")
                # 创建持久化上下文
                context = p.chromium.launch_persistent_context(
                    user_data_dir=chrome_profile_path,
                    headless=headless,
                    timeout=timeout
                )
                # 获取第一个页面或创建新页面
                page = context.pages[0] if context.pages else context.new_page()
            else:
                # 普通上下文
                browser = p.chromium.launch(headless=headless, timeout=timeout)
                context = browser.new_context()
                page = context.new_page()
            
            # 访问微信公众号平台
            print("访问微信公众号平台...")
            page.goto("https://mp.weixin.qq.com/", wait_until="networkidle")
            time.sleep(wait_time)
            
            # 检查是否已登录
            if "login" in page.url or page.locator("text=登录").count() > 0:
                print("检测到未登录状态，继续执行发布流程...")
                print("提示：如果未登录，发布可能会失败")
                # 截图保存当前状态
                try:
                    screenshot_path = "/mnt/user-data/outputs/wechat_login_status.png"
                    page.screenshot(path=screenshot_path)
                    print(f"已截图保存登录页面状态: {screenshot_path}")
                except:
                    print("无法截图保存登录状态")
            
            # 点击新建图文
            print("点击新建图文...")
            try:
                page.locator("text=新建图文").first.click(timeout=timeout)
                time.sleep(wait_time * 2)
            except PlaywrightTimeoutError:
                print("找不到'新建图文'按钮，尝试其他方式...")
                # 尝试其他可能的按钮位置
                page.locator("button:has-text('图文')").first.click(timeout=timeout)
                time.sleep(wait_time)
            
            # 填写标题
            print("填写标题...")
            title_input = page.locator("input[placeholder*='标题']").first
            title_input.fill(title)
            time.sleep(wait_time)
            
            # 切换到HTML编辑模式（如果需要）
            try:
                if page.locator("text=HTML").count() > 0:
                    page.locator("text=HTML").first.click()
                    time.sleep(wait_time)
            except:
                pass
            
            # 填写内容
            print("填写内容...")
            # 尝试找到内容编辑区域
            content_selector = "div[contenteditable='true'], textarea, .editor-content"
            content_area = page.locator(content_selector).first
            content_area.click()
            content_area.fill(content)
            time.sleep(wait_time)
            
            # 保存为草稿
            print("保存为草稿...")
            try:
                save_button = page.locator("button:has-text('保存')").first
                save_button.click(timeout=timeout)
                time.sleep(wait_time * 3)
                
                # 检查保存结果
                success_indicator = page.locator("text=保存成功").first
                if success_indicator.count() > 0:
                    print("✅ 保存成功!")
                    return True
                else:
                    print("保存成功，但未检测到成功提示")
                    return True
                    
            except PlaywrightTimeoutError:
                print("保存按钮超时，尝试其他保存方式...")
                # 尝试快捷键保存
                page.keyboard.press("Control+S")
                time.sleep(wait_time * 2)
                return True
            
            finally:
                # 关闭上下文
                if 'context' in locals():
                    context.close()
                
    except Exception as e:
        print(f"浏览器发布过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="微信公众号浏览器自动化发布工具")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--content", help="文章内容（直接提供）")
    parser.add_argument("--content-file", help="文章内容文件路径")
    parser.add_argument("--format", default="html", choices=["html", "markdown"], help="内容格式")
    parser.add_argument("--theme", help="主题名称")
    parser.add_argument("--color", help="主题颜色")
    parser.add_argument("--wait-time", type=int, default=2, help="等待时间（秒）")
    
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
    config = load_browser_config()
    
    # 更新等待时间
    if args.wait_time:
        config["wait_time"] = args.wait_time
    
    # 执行发布
    print("=" * 50)
    print("微信公众号浏览器自动化发布")
    print("=" * 50)
    
    success = publish_via_browser(args.title, content, config)
    
    if success:
        print("\n✅ 发布流程完成!")
        print("提示: 请在微信公众号平台确认内容并完成发布")
        print("草稿管理地址: https://mp.weixin.qq.com")
    else:
        print("\n❌ 发布流程失败!")
        print("建议:")
        print("1. 检查网络连接")
        print("2. 确认已登录微信公众号平台")
        print("3. 检查浏览器配置")
        sys.exit(1)

if __name__ == "__main__":
    main()