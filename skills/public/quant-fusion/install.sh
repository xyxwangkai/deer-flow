#!/bin/bash

# 量化融合系统安装脚本
# 融合Qlib、AlphaCouncil、TradingAgents三大项目

set -e

echo "🚀 开始安装量化融合系统..."
echo "========================================"

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo "❌ 需要Python 3.8或更高版本"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "SKILL.md" ]; then
    echo "❌ 请在技能根目录运行此脚本"
    exit 1
fi

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境？(y/n): " create_venv
if [[ "$create_venv" == "y" || "$create_venv" == "Y" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已激活"
fi

# 安装依赖
echo "安装Python依赖..."
pip install --upgrade pip

# 安装核心依赖
echo "安装核心依赖..."
pip install -r requirements.txt

# 安装可选依赖
echo "安装可选依赖..."
read -p "是否安装Qlib相关依赖？(y/n): " install_qlib
if [[ "$install_qlib" == "y" || "$install_qlib" == "Y" ]]; then
    echo "安装Qlib..."
    pip install pyqlib
fi

read -p "是否安装TradingAgents相关依赖？(y/n): " install_trading
if [[ "$install_trading" == "y" || "$install_trading" == "Y" ]]; then
    echo "安装交易相关依赖..."
    pip install ccxt
    pip install alpaca-trade-api
fi

# 创建必要目录
echo "创建必要目录..."
mkdir -p logs
mkdir -p data/cache
mkdir -p data/historical
mkdir -p data/realtime
mkdir -p outputs/reports
mkdir -p outputs/backtests

# 初始化配置文件
echo "初始化配置文件..."
if [ ! -f "config/config.yaml" ]; then
    cp "config/config.example.yaml" "config/config.yaml"
    echo "✅ 配置文件已创建，请编辑 config/config.yaml 进行配置"
else
    echo "✅ 配置文件已存在"
fi

# 设置权限
echo "设置执行权限..."
chmod +x scripts/*.py
chmod +x scripts/main.py

# 测试安装
echo "测试安装..."
python3 -c "import yaml, asyncio, aiohttp, pandas, numpy; print('✅ 核心依赖测试通过')"

# 运行简单测试
echo "运行系统测试..."
if [ -f "scripts/test_quant_fusion.py" ]; then
    python3 scripts/test_quant_fusion.py
    if [ $? -eq 0 ]; then
        echo "✅ 系统测试通过"
    else
        echo "⚠️ 系统测试失败，请检查安装"
    fi
fi

echo "========================================"
echo "🎉 量化融合系统安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 config/config.yaml 配置系统"
echo "2. 运行 python scripts/main.py --help 查看使用说明"
echo "3. 查看 docs/USAGE_GUIDE.md 获取详细指南"
echo ""
echo "快速开始："
echo "  python scripts/main.py analyze --symbols 000001 000002 --days 30"
echo ""