#!/bin/bash

# 安装 v2ray
bash <(curl -L https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh)

# 创建配置目录
mkdir -p /usr/local/etc/v2ray

# 创建基本配置文件
cat > /usr/local/etc/v2ray/config.json << EOF
{
  "inbounds": [
    {
      "port": 7890,
      "protocol": "socks",
      "settings": {
        "auth": "noauth",
        "udp": true
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
EOF

# 启动 v2ray 服务
systemctl start v2ray
systemctl enable v2ray

# 检查服务状态
systemctl status v2ray
