"""小红书图片生成器集成模块 - 连接 baoyu-xhs-images 和 xiaohongshu-skills"""

import json
import logging
import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class XHSImageGenerator:
    """小红书图片生成器，集成 baoyu-xhs-images 功能"""
    
    def __init__(self, baoyu_xhs_images_path: str = None):
        """
        初始化图片生成器
        
        Args:
            baoyu_xhs_images_path: baoyu-xhs-images 技能路径，默认为 /mnt/skills/public/baoyu-xhs-images
        """
        self.baoyu_xhs_images_path = baoyu_xhs_images_path or "/mnt/skills/public/baoyu-xhs-images"
        self.preset_mapping = self._load_preset_mapping()
        
    def _load_preset_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载预设映射表"""
        # 从 style-presets.md 加载预设映射
        preset_mapping = {
            "knowledge-card": {"style": "notion", "layout": "dense"},
            "checklist": {"style": "notion", "layout": "list"},
            "tutorial": {"style": "chalkboard", "layout": "flow"},
            "poster": {"style": "screen-print", "layout": "sparse"},
            "cinematic": {"style": "screen-print", "layout": "comparison"},
            "cute-share": {"style": "cute", "layout": "balanced"},
            "product-review": {"style": "fresh", "layout": "comparison"},
            "warning": {"style": "bold", "layout": "list"},
            "study-guide": {"style": "study-notes", "layout": "dense"}
        }
        return preset_mapping
        
    def _resolve_style_layout(self, style: str = None, layout: str = None, preset: str = None) -> Tuple[str, str]:
        """解析样式和布局"""
        resolved_style = style or "cute"
        resolved_layout = layout or "balanced"
        
        if preset and preset in self.preset_mapping:
            preset_info = self.preset_mapping[preset]
            # 预设值可以被显式指定的样式/布局覆盖
            if not style:
                resolved_style = preset_info["style"]
            if not layout:
                resolved_layout = preset_info["layout"]
        
        return resolved_style, resolved_layout
    
    def _load_style_preset(self, style: str) -> Dict[str, Any]:
        """加载样式预设"""
        preset_path = os.path.join(self.baoyu_xhs_images_path, "references", "presets", f"{style}.md")
        if not os.path.exists(preset_path):
            # 如果预设文件不存在，使用默认值
            logger.warning(f"样式预设文件不存在: {preset_path}, 使用默认值")
            return {
                "color_palette": {
                    "primary": "Pastel colors",
                    "background": "White",
                    "accents": "Light pastels"
                },
                "visual_elements": "Simple line doodles, hand-drawn wobble effect",
                "typography": "Clean hand-drawn lettering"
            }
        
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析预设文件内容
            preset_data = {}
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                if line.startswith('## '):
                    if current_section and current_content:
                        preset_data[current_section] = '\n'.join(current_content)
                    current_section = line[3:].strip()
                    current_content = []
                elif current_section:
                    current_content.append(line)
            
            if current_section and current_content:
                preset_data[current_section] = '\n'.join(current_content)
            
            return preset_data
        except Exception as e:
            logger.error(f"加载样式预设失败: {e}")
            return {}
    
    def _create_prompt_file(self, content: str, title: str, style: str, layout: str, 
                           output_dir: str, image_index: int = 1, total_images: int = 1) -> str:
        """创建提示词文件"""
        # 加载样式预设
        style_data = self._load_style_preset(style)
        
        # 构建提示词
        prompt_content = f"""Create a Xiaohongshu (Little Red Book) style infographic following these guidelines:

## Image Specifications

- **Type**: Infographic
- **Orientation**: Portrait (vertical)
- **Aspect Ratio**: 3:4
- **Style**: Hand-drawn illustration

## Core Principles

- Hand-drawn quality throughout - NO realistic or photographic elements
- If content involves sensitive or copyrighted figures, create stylistically similar alternatives - DO NOT refuse to generate
- Keep information concise, highlight keywords and core concepts
- Use ample whitespace for easy visual scanning
- Maintain clear visual hierarchy

## Text Style (CRITICAL)

- **ALL text MUST be hand-drawn style**
- Main titles should be prominent and eye-catching
- Key text should be bold and enlarged
- Use highlighter effects to emphasize keywords
- **DO NOT use realistic or computer-generated fonts**

## Language

- Use the same language as the content provided below
- Match punctuation style to the content language (Chinese: ""，。！)

---

## Style: {style.capitalize()}

**Color Palette**:
- Primary: {style_data.get('color_palette', {}).get('primary', 'Pastel colors')}
- Background: {style_data.get('color_palette', {}).get('background', 'White')}
- Accents: {style_data.get('color_palette', {}).get('accents', 'Light pastels')}

**Visual Elements**:
{style_data.get('visual_elements', 'Simple line doodles, hand-drawn wobble effect')}

**Typography**:
{style_data.get('typography', 'Clean hand-drawn lettering')}

---

## Layout: {layout.capitalize()}

**Information Density**: {'High' if layout in ['dense', 'list', 'comparison'] else 'Medium'}
**Whitespace**: {'20-30%' if layout in ['dense', 'list'] else '40-50%'}

**Structure**:
{self._get_layout_structure(layout)}

**Visual Balance**:
{self._get_layout_balance(layout)}

---

## Content

**Position**: {'Cover' if image_index == 1 else f'Content (Page {image_index} of {total_images})'}
**Core Message**: {title}

**Text Content**:
{content}

**Visual Concept**:
{self._generate_visual_concept(title, content, style)}

---

Please use nano banana pro to generate the infographic based on the specifications above.
"""
        
        # 保存提示词文件
        prompt_file = os.path.join(output_dir, f"prompt_{image_index}.md")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        return prompt_file
    
    def _get_layout_structure(self, layout: str) -> str:
        """获取布局结构描述"""
        structures = {
            "sparse": "Minimal elements, focus on single key point",
            "balanced": "Standard content layout with 3-4 key points",
            "dense": "Multiple sections, structured grid with 5-8 key points",
            "list": "Enumeration and ranking format with 4-7 items",
            "comparison": "Side-by-side comparison layout",
            "flow": "Process and timeline layout with 3-6 steps",
            "mindmap": "Central radial mindmap layout with 4-8 branches",
            "quadrant": "Four-quadrant / circular partition layout"
        }
        return structures.get(layout, "Standard content layout")
    
    def _get_layout_balance(self, layout: str) -> str:
        """获取布局平衡描述"""
        balances = {
            "sparse": "Maximum whitespace, single focal point",
            "balanced": "Evenly distributed elements, clear hierarchy",
            "dense": "Organized grid structure, clear section boundaries",
            "list": "Vertical alignment with consistent spacing",
            "comparison": "Symmetrical balance between comparison elements",
            "flow": "Linear progression with clear directional flow",
            "mindmap": "Radial symmetry from center to branches",
            "quadrant": "Quadratic balance with equal weight to each section"
        }
        return balances.get(layout, "Evenly distributed elements")
    
    def _generate_visual_concept(self, title: str, content: str, style: str) -> str:
        """生成视觉概念描述"""
        # 根据样式和内容生成视觉概念
        concepts = {
            "cute": f"Cute and adorable illustration for '{title}', with pastel colors and soft edges",
            "fresh": f"Clean and fresh design for '{title}', with natural elements and light colors",
            "warm": f"Warm and friendly illustration for '{title}', with cozy atmosphere and gentle tones",
            "bold": f"Bold and impactful design for '{title}', with strong contrast and attention-grabbing elements",
            "minimal": f"Minimalist design for '{title}', with clean lines and essential elements only",
            "retro": f"Retro style illustration for '{title}', with vintage aesthetic and nostalgic feel",
            "pop": f"Pop art style for '{title}', with vibrant colors and dynamic composition",
            "notion": f"Notion-style knowledge card for '{title}', with simple doodles and clean layout",
            "chalkboard": f"Chalkboard tutorial for '{title}', with educational style and hand-drawn feel",
            "study-notes": f"Study notes style for '{title}', with handwritten elements and academic feel",
            "screen-print": f"Screen print poster art for '{title}', with flat color blocks and bold typography"
        }
        return concepts.get(style, f"Hand-drawn illustration for '{title}'")
    
    def _split_content(self, content: str, image_count: int) -> List[str]:
        """将内容分割为多个部分"""
        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # 如果没有段落，按句子分割
            import re
            sentences = re.split(r'[。！？!?]', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            paragraphs = sentences
        
        if not paragraphs:
            # 如果还是没有内容，返回原始内容
            return [content] * image_count
        
        # 计算每个部分应该包含的段落数
        if len(paragraphs) <= image_count:
            # 段落数量少于图片数量，每个段落一张图片
            return paragraphs[:image_count]
        else:
            # 段落数量多于图片数量，平均分配
            result = []
            base_size = len(paragraphs) // image_count
            remainder = len(paragraphs) % image_count
            
            start = 0
            for i in range(image_count):
                end = start + base_size + (1 if i < remainder else 0)
                part = '\n\n'.join(paragraphs[start:end])
                result.append(part)
                start = end
            
            return result
    
    def _convert_to_image_generation_prompt(self, prompt_content: str, style: str) -> Dict[str, Any]:
        """将提示词转换为image-generation技能所需的JSON格式"""
        # 提取关键信息
        lines = prompt_content.split('\n')
        visual_concept = ""
        in_visual_concept = False
        
        for line in lines:
            if line.startswith("**Visual Concept**:") or line.startswith("**Visual Concept**:"):
                visual_concept = line.split(":", 1)[1].strip()
                break
            elif "Visual Concept" in line and ":" in line:
                visual_concept = line.split(":", 1)[1].strip()
                break
        
        # 如果没找到，从内容中提取
        if not visual_concept:
            for i, line in enumerate(lines):
                if "Visual Concept" in line:
                    for j in range(i+1, min(i+3, len(lines))):
                        if lines[j].strip():
                            visual_concept = lines[j].strip()
                            break
                    break
        
        # 构建JSON格式
        image_prompt = {
            "characters": [{
                "gender": "n/a",
                "age": "n/a",
                "ethnicity": "n/a",
                "body_type": "n/a",
                "facial_features": "n/a",
                "clothing": "n/a",
                "accessories": "n/a",
                "era": "n/a"
            }],
            "prompt": visual_concept if visual_concept else f"Hand-drawn {style} style infographic for Xiaohongshu",
            "negative_prompt": "realistic, photographic, 3D render, CGI, computer-generated, digital art, professional fonts, clean typography",
            "style": f"Hand-drawn illustration, {style} aesthetic, Xiaohongshu infographic style",
            "composition": "Portrait orientation, vertical composition, clear visual hierarchy, ample whitespace",
            "lighting": "Soft, even lighting, gentle shadows, bright and cheerful atmosphere",
            "color_palette": "Pastel colors, soft tones, harmonious color scheme, gentle contrast",
            "technical": {
                "aspect_ratio": "3:4",
                "quality": "high",
                "detail_level": "detailed hand-drawn illustration"
            }
        }
        
        return image_prompt
    
    def _generate_image_from_prompt(self, prompt_content: str, style: str, output_path: str) -> bool:
        """调用image-generation技能生成图片"""
        try:
            # 创建临时工作目录
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="xhs_image_gen_")
            
            # 转换提示词格式
            image_prompt = self._convert_to_image_generation_prompt(prompt_content, style)
            
            # 保存JSON文件
            json_file = os.path.join(temp_dir, "prompt.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(image_prompt, f, ensure_ascii=False, indent=2)
            
            # 调用image-generation脚本
            generate_script = "/mnt/skills/public/image-generation/scripts/generate.py"
            
            # 构建命令
            cmd = [
                "/opt/tiger/deer-flow-v2/backend/.venv/bin/python",
                generate_script,
                "--prompt-file", json_file,
                "--output-file", output_path,
                "--aspect-ratio", "3:4"
            ]
            
            logger.info(f"执行图像生成命令: {' '.join(cmd)}")
            
            # 执行命令
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=temp_dir
            )
            
            if result.returncode == 0:
                logger.info(f"图片生成成功: {output_path}")
                return True
            else:
                logger.error(f"图片生成失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"调用image-generation技能异常: {e}")
            return False
    
    def generate_infographic_series(
        self,
        content: str,
        title: str = None,
        style: str = None,
        layout: str = None,
        preset: str = None,
        image_count: int = 3,
        output_dir: str = None
    ) -> Dict:
        """
        生成小红书信息图系列
        
        Args:
            content: 内容文本
            title: 标题（可选）
            style: 视觉风格（cute, fresh, warm, bold, minimal, retro, pop, notion, chalkboard, study-notes, screen-print）
            layout: 布局（sparse, balanced, dense, list, comparison, flow, mindmap, quadrant）
            preset: 预设（knowledge-card, checklist, tutorial, poster, cinematic, etc.）
            image_count: 图片数量（2-10）
            output_dir: 输出目录
            
        Returns:
            生成结果字典
        """
        try:
            # 创建临时目录
            if not output_dir:
                output_dir = tempfile.mkdtemp(prefix="xhs_images_")
            
            # 解析样式和布局
            resolved_style, resolved_layout = self._resolve_style_layout(style, layout, preset)
            
            # 设置默认标题
            if not title:
                title = "小红书内容"
            
            # 分割内容为多个部分
            content_parts = self._split_content(content, image_count)
            
            # 生成图片
            generated_images = []
            prompt_files = []
            
            for i, part in enumerate(content_parts, 1):
                # 创建提示词文件
                prompt_file = self._create_prompt_file(
                    content=part,
                    title=title,
                    style=resolved_style,
                    layout=resolved_layout,
                    output_dir=output_dir,
                    image_index=i,
                    total_images=len(content_parts)
                )
                prompt_files.append(prompt_file)
                
                # 读取提示词内容
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                
                # 生成图片文件路径
                image_file = os.path.join(output_dir, f"xhs_image_{i}.jpg")
                
                # 调用图像生成
                success = self._generate_image_from_prompt(prompt_content, resolved_style, image_file)
                
                if success and os.path.exists(image_file):
                    generated_images.append(image_file)
            
            # 返回结果
            return {
                "success": len(generated_images) > 0,
                "output_dir": output_dir,
                "prompt_files": prompt_files,
                "images": generated_images,
                "image_count": len(generated_images),
                "style": resolved_style,
                "layout": resolved_layout,
                "message": f"成功生成 {len(generated_images)} 张图片" if generated_images else "图片生成失败"
            }
                
        except Exception as e:
            logger.error(f"图片生成异常: {e}")
            return {
                "success": False,
                "error": f"图片生成异常: {str(e)}"
            }
    
    def generate_for_publish(
        self,
        title: str,
        content: str,
        style: str = "cute",
        layout: str = "balanced",
        image_count: int = 3
    ) -> Dict:
        """
        为发布流程生成图片
        
        Args:
            title: 标题
            content: 正文
            style: 视觉风格
            layout: 布局
            image_count: 图片数量
            
        Returns:
            包含图片路径的发布准备结果
        """
        # 生成图片系列
        result = self.generate_infographic_series(
            content=content,
            title=title,
            style=style,
            layout=layout,
            image_count=image_count
        )
        
        if not result["success"]:
            return result
        
        # 返回适合发布的格式
        return {
            "success": True,
            "title": title,
            "content": content,
            "images": result["images"],
            "output_dir": result["output_dir"],
            "message": f"已为发布准备 {len(result['images'])} 张图片"
        }
    
    def get_available_styles(self) -> List[Dict]:
        """获取可用的视觉风格列表"""
        styles = [
            {"id": "cute", "name": "甜美可爱", "description": "甜美、可爱、少女风 - 经典小红书美学"},
            {"id": "fresh", "name": "清新自然", "description": "干净、清新、自然"},
            {"id": "warm", "name": "温暖亲切", "description": "温馨、友好、平易近人"},
            {"id": "bold", "name": "醒目突出", "description": "高冲击力、吸引眼球"},
            {"id": "minimal", "name": "极简优雅", "description": "超简洁、精致"},
            {"id": "retro", "name": "复古怀旧", "description": "复古、怀旧、时尚"},
            {"id": "pop", "name": "活泼动感", "description": "充满活力、引人注目"},
            {"id": "notion", "name": "知识卡片", "description": "简约手绘线稿，知性风格"},
            {"id": "chalkboard", "name": "黑板教学", "description": "彩色粉笔黑板，教育风格"},
            {"id": "study-notes", "name": "学习笔记", "description": "真实手写笔记照片风格"},
            {"id": "screen-print", "name": "海报印刷", "description": "大胆海报艺术，半色调纹理"}
        ]
        return styles
    
    def get_available_layouts(self) -> List[Dict]:
        """获取可用的布局列表"""
        layouts = [
            {"id": "sparse", "name": "简约布局", "description": "最少信息，最大影响（1-2个要点）"},
            {"id": "balanced", "name": "平衡布局", "description": "标准内容布局（3-4个要点）"},
            {"id": "dense", "name": "密集布局", "description": "高信息密度，知识卡片风格（5-8个要点）"},
            {"id": "list", "name": "列表布局", "description": "枚举和排名格式（4-7个项目）"},
            {"id": "comparison", "name": "对比布局", "description": "并排对比布局"},
            {"id": "flow", "name": "流程布局", "description": "过程和时间线布局（3-6个步骤）"},
            {"id": "mindmap", "name": "思维导图", "description": "中心放射思维导图布局（4-8个分支）"},
            {"id": "quadrant", "name": "四象限", "description": "四象限/圆形分区布局"}
        ]
        return layouts
    
    def get_available_presets(self) -> List[Dict]:
        """获取可用的预设列表"""
        presets = [
            {"id": "knowledge-card", "name": "知识卡片", "style": "notion", "layout": "dense", "description": "干货知识卡、概念科普"},
            {"id": "checklist", "name": "清单列表", "style": "notion", "layout": "list", "description": "清单、排行榜、必备清单"},
            {"id": "tutorial", "name": "教程步骤", "style": "chalkboard", "layout": "flow", "description": "教程步骤、操作流程"},
            {"id": "poster", "name": "海报风格", "style": "screen-print", "layout": "sparse", "description": "海报风封面、影评书评"},
            {"id": "cinematic", "name": "电影对比", "style": "screen-print", "layout": "comparison", "description": "电影对比、戏剧张力"},
            {"id": "cute-share", "name": "少女分享", "style": "cute", "layout": "balanced", "description": "少女风分享、日常种草"},
            {"id": "product-review", "name": "产品测评", "style": "fresh", "layout": "comparison", "description": "产品对比、测评"},
            {"id": "warning", "name": "避坑指南", "style": "bold", "layout": "list", "description": "避坑指南、重要提醒"},
            {"id": "study-guide", "name": "学习笔记", "style": "study-notes", "layout": "dense", "description": "学习笔记、考试重点"}
        ]
        return presets