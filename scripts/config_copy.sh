#!/bin/bash

# 创建符号链接，如果目标已存在则跳过
create_symlink_if_not_exists() {
    local source="$1"
    local target="$2"
    
    if [ ! -e "$target" ]; then
        echo "创建符号链接: $target -> $source"
        ln -s "$source" "$target"
    else
        echo "跳过: $target 已存在"
    fi
}

# 创建配置文件的符号链接
create_symlink_if_not_exists "../project_env/deer-flow/config.yaml" "config.yaml"
create_symlink_if_not_exists "../project_env/deer-flow/.env" ".env"
create_symlink_if_not_exists "../../project_env/deer-flow/frontend/.env" "frontend/.env"

cp -r ../project_env/deer-flow/docker/nginx/nginx.local.conf docker/nginx/nginx.local.conf

create_symlink_if_not_exists "../../project_env/deer-flow/skills/custom" "skills/custom"

echo "符号链接创建完成"