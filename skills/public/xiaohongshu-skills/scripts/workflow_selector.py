#!/usr/bin/env python3
"""
小红书标准化工作流选择器
用于列出可用模板并让用户选择要执行的标准化流程
"""

import json
import os
import sys
from pathlib import Path

class WorkflowSelector:
    def __init__(self, templates_dir=None):
        """初始化工作流选择器"""
        if templates_dir is None:
            # 默认模板目录
            self.templates_dir = Path(__file__).parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        # 确保模板目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self):
        """列出所有可用的模板文件"""
        templates = []
        
        if not self.templates_dir.exists():
            print(f"❌ 模板目录不存在: {self.templates_dir}")
            return templates
        
        for file_path in self.templates_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template_info = {
                    'id': template_data.get('id', file_path.stem),
                    'name': template_data.get('name', file_path.stem),
                    'description': template_data.get('description', ''),
                    'status': template_data.get('status', 'unknown'),
                    'file_path': str(file_path),
                    'version': template_data.get('version', '1.0'),
                    'created_date': template_data.get('created_date', ''),
                    'last_updated': template_data.get('last_updated', '')
                }
                templates.append(template_info)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  无法读取模板文件 {file_path}: {e}")
                continue
        
        return templates
    
    def get_template(self, template_id):
        """根据ID获取模板内容"""
        template_file = self.templates_dir / f"{template_id}.json"
        
        if not template_file.exists():
            # 尝试查找匹配的文件
            for file_path in self.templates_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    if template_data.get('id') == template_id:
                        template_file = file_path
                        break
                except (json.JSONDecodeError, IOError):
                    continue
        
        if not template_file.exists():
            return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ 无法读取模板文件 {template_file}: {e}")
            return None
    
    def display_template_table(self, templates):
        """以表格形式显示模板列表"""
        if not templates:
            print("📭 没有找到可用的模板")
            return
        
        print("\n📋 可用标准化工作流模板:")
        print("=" * 100)
        print(f"{'ID':<15} {'名称':<25} {'状态':<10} {'描述':<40}")
        print("-" * 100)
        
        for template in templates:
            # 状态显示符号
            status_symbol = "✅" if template['status'] == 'verified' else "🟡" if template['status'] == 'ready' else "⚪"
            
            # 截断过长的描述
            description = template['description']
            if len(description) > 37:
                description = description[:34] + "..."
            
            print(f"{template['id']:<15} {template['name']:<25} {status_symbol} {template['status']:<8} {description:<40}")
        
        print("=" * 100)
        print(f"📁 模板目录: {self.templates_dir}")
    
    def display_template_details(self, template):
        """显示模板详细信息"""
        if not template:
            print("❌ 模板不存在或无法加载")
            return
        
        print(f"\n📄 模板详情: {template.get('name', '未知模板')}")
        print("=" * 80)
        print(f"ID: {template.get('id', 'N/A')}")
        print(f"版本: {template.get('version', 'N/A')}")
        print(f"状态: {template.get('status', 'N/A')}")
        print(f"创建日期: {template.get('created_date', 'N/A')}")
        print(f"最后更新: {template.get('last_updated', 'N/A')}")
        print(f"描述: {template.get('description', 'N/A')}")
        
        # 显示工作流步骤
        workflow_steps = template.get('workflow_steps', [])
        if workflow_steps:
            print(f"\n🔄 工作流步骤 ({len(workflow_steps)}步):")
            for step in workflow_steps:
                step_num = step.get('step', '?')
                step_name = step.get('name', '未知步骤')
                print(f"  {step_num}. {step_name}")
        
        # 显示配置
        config = template.get('configuration', {})
        if config:
            print(f"\n⚙️  配置参数:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        
        # 显示相关模板
        related = template.get('related_templates', [])
        if related:
            print(f"\n🔗 相关模板: {', '.join(related)}")
        
        print("=" * 80)
    
    def interactive_select(self):
        """交互式选择模板"""
        templates = self.list_templates()
        
        if not templates:
            print("❌ 没有可用的模板，请先创建模板文件")
            return None
        
        self.display_template_table(templates)
        
        print("\n🤔 请选择要执行的工作流模板:")
        print("1. 输入模板ID (例如: ai_hot_topic)")
        print("2. 输入模板序号 (1, 2, 3...)")
        print("3. 输入 'q' 退出")
        
        while True:
            choice = input("\n请输入选择: ").strip()
            
            if choice.lower() == 'q':
                print("👋 退出选择")
                return None
            
            # 检查是否输入了序号
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    selected_template = templates[index]
                    print(f"✅ 选择了: {selected_template['name']}")
                    return self.get_template(selected_template['id'])
                else:
                    print(f"❌ 序号无效，请输入 1-{len(templates)} 之间的数字")
                    continue
            
            # 检查是否输入了模板ID
            selected_template = None
            for template in templates:
                if template['id'] == choice:
                    selected_template = template
                    break
            
            if selected_template:
                print(f"✅ 选择了: {selected_template['name']}")
                return self.get_template(selected_template['id'])
            else:
                print(f"❌ 未找到ID为 '{choice}' 的模板")
                print("可用的模板ID:")
                for template in templates:
                    print(f"  - {template['id']}")

def main():
    """主函数"""
    selector = WorkflowSelector()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 如果提供了模板ID，直接显示详情
        template_id = sys.argv[1]
        template = selector.get_template(template_id)
        
        if template:
            selector.display_template_details(template)
        else:
            print(f"❌ 未找到模板: {template_id}")
            templates = selector.list_templates()
            if templates:
                print("可用的模板:")
                for template in templates:
                    print(f"  - {template['id']}: {template['name']}")
            sys.exit(1)
    else:
        # 交互式选择
        template = selector.interactive_select()
        if template:
            selector.display_template_details(template)
            print(f"\n🎯 已选择模板: {template.get('name')}")
            print("💡 下一步: 执行标准化工作流")
            print(f"    python standard_workflow.py --template {template.get('id')}")

if __name__ == "__main__":
    main()