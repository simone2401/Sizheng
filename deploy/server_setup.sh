#!/usr/bin/env bash
# 服务器初始化脚本 —— 在服务器上以 ubuntu 用户执行: bash deploy/server_setup.sh
# 前提:代码已 rsync 上传到 /data/sizheng2,.env.production 已填好
set -euo pipefail

BASE=/data/sizheng2/teaching_model_service

echo "==> 1/5 安装系统依赖 (python3-venv, nginx)"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx

echo "==> 2/5 创建虚拟环境并安装依赖(清华镜像加速)"
cd "$BASE"
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U pip
.venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
mkdir -p logs data

echo "==> 3/5 检查 .env.production"
if [ ! -f "$BASE/.env.production" ]; then
  echo "!! 缺少 $BASE/.env.production,请先: cp deploy/env.production.example .env.production 并填入 ZHIPU_API_KEY"
  exit 1
fi
chmod 600 "$BASE/.env.production"
if ! grep -q '^ZHIPU_API_KEY=.\+' "$BASE/.env.production"; then
  echo "!! .env.production 里 ZHIPU_API_KEY 还是空的,请填入后重跑本脚本"
  exit 1
fi

echo "==> 4/5 安装 systemd 服务并启动"
sudo cp "$BASE/deploy/sizheng-resource.service" "$BASE/deploy/sizheng-model.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sizheng-resource sizheng-model
sleep 2

echo "==> 5/5 配置 nginx"
sudo cp "$BASE/deploy/nginx-sizheng.conf" /etc/nginx/sites-available/sizheng
sudo ln -sf /etc/nginx/sites-available/sizheng /etc/nginx/sites-enabled/sizheng
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "==> 自检"
for port in 9001 9000; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:$port/health/ready || true)
  echo "  :$port /health/ready -> $code"
done
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1/sizheng2/ || true)
echo "  nginx /sizheng2/ -> $code"
echo "完成。浏览器访问 http://82.156.215.199/sizheng2/ 验证联调页面。"
