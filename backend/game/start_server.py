import json
import time
import subprocess
import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.cvm.v20170312 import cvm_client, models
from typing import List, Dict


class CS2MatchServer:
    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou"):
        """
        初始化CS2比赛服务器管理器

        Args:
            secret_id: 腾讯云SecretId
            secret_key: 腾讯云SecretKey
            region: 腾讯云地域
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.instance_id = None
        self.server_ip = None
        self.server_port = 27015

        # 初始化腾讯云客户端
        cred = credential.Credential(secret_id, secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "cvm.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        self.client = cvm_client.CvmClient(cred, region, clientProfile)

    def create_spot_instance(self,
                             instance_type: str = "S5.LARGE8",
                             image_id: str = "img-22trbn9x",  # Ubuntu 20.04
                             vpc_id: str = None,
                             subnet_id: str = None) -> str:
        """
        创建腾讯云抢占式实例

        Args:
            instance_type: 实例类型
            image_id: 镜像ID
            vpc_id: VPC ID
            subnet_id: 子网ID

        Returns:
            实例ID
        """
        try:
            # 创建抢占式实例请求
            req = models.RunInstancesRequest()

            # 基础配置
            req.InstanceType = instance_type
            req.ImageId = image_id
            req.InstanceCount = 1
            req.InstanceName = "cs2-match-server"

            # 抢占式实例配置
            req.InstanceMarketOptions = models.InstanceMarketOptionsRequest()
            req.InstanceMarketOptions.MarketType = "spot"
            req.InstanceMarketOptions.SpotOptions = models.SpotMarketOptions()
            req.InstanceMarketOptions.SpotOptions.MaxPrice = "0.1"  # 最高价格
            req.InstanceMarketOptions.SpotOptions.SpotInstanceType = "one-time"

            # 网络配置
            if vpc_id and subnet_id:
                req.VirtualPrivateCloud = models.VirtualPrivateCloud()
                req.VirtualPrivateCloud.VpcId = vpc_id
                req.VirtualPrivateCloud.SubnetId = subnet_id

            # 安全组配置（需要开放27015端口）
            req.SecurityGroupIds = ["sg-cs2server"]  # 请替换为实际的安全组ID

            # 启动脚本
            user_data = self._generate_user_data()
            req.UserData = user_data

            # 发送请求
            resp = self.client.RunInstances(req)
            self.instance_id = resp.InstanceIdSet[0]

            print(f"实例创建成功，实例ID: {self.instance_id}")

            # 等待实例启动
            self._wait_instance_running()

            return self.instance_id

        except Exception as e:
            print(f"创建实例失败: {e}")
            raise

    def _generate_user_data(self) -> str:
        """
        生成实例启动脚本
        """
        script = """#!/bin/bash
# 更新系统
apt-get update

# 安装必要软件
apt-get install -y wget curl lib32gcc-s1 lib32stdc++6

# 创建Steam用户
useradd -m steam
cd /home/steam

# 下载SteamCMD
wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz
tar -xvzf steamcmd_linux.tar.gz
chown -R steam:steam /home/steam

# 创建CS2服务器目录
mkdir -p /home/steam/cs2-server
chown -R steam:steam /home/steam/cs2-server

# 设置防火墙
ufw allow 27015/tcp
ufw allow 27015/udp
ufw allow 27016/tcp
ufw allow 27016/udp

# 创建启动脚本
cat > /home/steam/start_cs2.sh << 'EOF'
#!/bin/bash
cd /home/steam
./steamcmd.sh +force_install_dir /home/steam/cs2-server +login anonymous +app_update 730 +quit
cd /home/steam/cs2-server
./srcds_run -game csgo -console -usercon +game_type 0 +game_mode 1 +mapgroup mg_de_dust2 +map de_dust2 -port 27015 +sv_setsteamaccount GSLT_TOKEN
EOF

chmod +x /home/steam/start_cs2.sh
chown steam:steam /home/steam/start_cs2.sh

# 创建Python环境用于插件管理
apt-get install -y python3 python3-pip
pip3 install websockets asyncio

# 创建插件目录
mkdir -p /home/steam/cs2-server/csgo/addons/sourcemod
mkdir -p /home/steam/cs2-server/csgo/cfg
chown -R steam:steam /home/steam/cs2-server/csgo
"""
        return script

    def _wait_instance_running(self):
        """
        等待实例启动完成
        """
        print("等待实例启动...")
        while True:
            try:
                req = models.DescribeInstancesRequest()
                req.InstanceIds = [self.instance_id]
                resp = self.client.DescribeInstances(req)

                if resp.InstanceSet[0].InstanceState == "RUNNING":
                    self.server_ip = resp.InstanceSet[0].PublicIpAddresses[0]
                    print(f"实例启动成功，IP: {self.server_ip}")
                    break

                time.sleep(10)

            except Exception as e:
                print(f"查询实例状态失败: {e}")
                time.sleep(10)

    def generate_match_config(self, t_team_ids: List[str], ct_team_ids: List[str]) -> Dict:
        """
        生成比赛配置文件

        Args:
            t_team_ids: T队Steam 64位ID列表
            ct_team_ids: CT队Steam 64位ID列表

        Returns:
            配置字典
        """
        config = {
            "match_id": f"match_{int(time.time())}",
            "teams": {
                "t": {
                    "name": "Team T",
                    "players": t_team_ids
                },
                "ct": {
                    "name": "Team CT",
                    "players": ct_team_ids
                }
            },
            "server_config": {
                "mp_maxrounds": 30,
                "mp_startmoney": 800,
                "mp_freezetime": 15,
                "mp_roundtime": 1.92,
                "mp_buytime": 20,
                "mp_restartgame": 1,
                "sv_cheats": 0,
                "sv_lan": 0,
                "sv_password": f"match_{int(time.time())}"
            }
        }

        return config

    def deploy_server_config(self, config: Dict):
        """
        部署服务器配置

        Args:
            config: 比赛配置字典
        """
        # 生成服务器配置文件
        server_cfg = self._generate_server_cfg(config)

        # 生成队伍分配插件
        team_plugin = self._generate_team_plugin(config)

        # 通过SSH部署到服务器
        self._deploy_files_to_server(server_cfg, team_plugin, config)

    def _generate_server_cfg(self, config: Dict) -> str:
        """
        生成服务器配置文件内容
        """
        cfg_content = f"""
// CS2 Match Server Configuration
hostname "CS2 Match Server - {config['match_id']}"
sv_password "{config['server_config']['sv_password']}"

// Match Settings
mp_maxrounds {config['server_config']['mp_maxrounds']}
mp_startmoney {config['server_config']['mp_startmoney']}
mp_freezetime {config['server_config']['mp_freezetime']}
mp_roundtime {config['server_config']['mp_roundtime']}
mp_buytime {config['server_config']['mp_buytime']}
sv_cheats {config['server_config']['sv_cheats']}
sv_lan {config['server_config']['sv_lan']}

// Competition Settings
mp_overtime_enable 1
mp_overtime_maxrounds 6
mp_overtime_startmoney 10000

// Other Settings
sv_alltalk 0
sv_full_alltalk 0
sv_deadtalk 1
mp_teammates_are_enemies 0
mp_friendlyfire 1
mp_autokick 0
mp_autoteambalance 0
mp_limitteams 0

exec match_plugin.cfg
"""
        return cfg_content

    def _generate_team_plugin(self, config: Dict) -> str:
        """
        生成队伍分配插件（Python脚本）
        """
        plugin_content = f"""
import asyncio
import websockets
import json
import logging

# 队伍配置
TEAM_CONFIG = {json.dumps(config, indent=2)}

class CS2MatchPlugin:
    def __init__(self):
        self.t_team = set(TEAM_CONFIG['teams']['t']['players'])
        self.ct_team = set(TEAM_CONFIG['teams']['ct']['players'])
        self.all_players = self.t_team | self.ct_team

    async def handle_player_connect(self, steam_id: str):
        \"\"\"处理玩家连接\"\"\"
        if steam_id not in self.all_players:
            # 踢出不在列表中的玩家
            await self.kick_player(steam_id, "Not authorized for this match")
            return

        # 分配到正确队伍
        if steam_id in self.t_team:
            await self.assign_team(steam_id, 2)  # T队
        elif steam_id in self.ct_team:
            await self.assign_team(steam_id, 3)  # CT队

    async def kick_player(self, steam_id: str, reason: str):
        \"\"\"踢出玩家\"\"\"
        # 这里需要实现与CS2服务器的通信
        print(f"Kicking player {{steam_id}}: {{reason}}")
        # 实际实现中需要使用RCON或其他方式与服务器通信

    async def assign_team(self, steam_id: str, team_id: int):
        \"\"\"分配队伍\"\"\"
        print(f"Assigning player {{steam_id}} to team {{team_id}}")
        # 实际实现中需要使用RCON命令分配队伍

if __name__ == "__main__":
    plugin = CS2MatchPlugin()
    # 启动插件服务
    print("CS2 Match Plugin started")
"""
        return plugin_content

    def _deploy_files_to_server(self, server_cfg: str, team_plugin: str, config: Dict):
        """
        部署文件到服务器
        """
        # 这里需要实现SSH连接和文件传输
        # 为了简化，我们假设已经有了SSH连接
        print(f"部署配置到服务器 {self.server_ip}")

        # 保存配置到本地临时文件
        with open('/tmp/server.cfg', 'w') as f:
            f.write(server_cfg)

        with open('/tmp/team_plugin.py', 'w') as f:
            f.write(team_plugin)

        with open('/tmp/match_config.json', 'w') as f:
            json.dump(config, f, indent=2)

        # 使用SCP传输文件（需要安装paramiko等库）
        """
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.server_ip, username='steam', key_filename='/path/to/key.pem')

        sftp = ssh.open_sftp()
        sftp.put('/tmp/server.cfg', '/home/steam/cs2-server/csgo/cfg/server.cfg')
        sftp.put('/tmp/team_plugin.py', '/home/steam/team_plugin.py')
        sftp.put('/tmp/match_config.json', '/home/steam/match_config.json')

        # 启动CS2服务器
        stdin, stdout, stderr = ssh.exec_command('cd /home/steam && ./start_cs2.sh')

        ssh.close()
        """

    def get_connect_url(self, password: str = None) -> str:
        """
        生成连接URL

        Args:
            password: 服务器密码

        Returns:
            Steam连接URL
        """
        if not self.server_ip:
            raise ValueError("服务器IP未设置")

        if password:
            connect_url = f"steam://connect/{self.server_ip}:{self.server_port}/{password}"
        else:
            connect_url = f"steam://connect/{self.server_ip}:{self.server_port}"

        return connect_url

    def generate_connect_html(self, password: str = None) -> str:
        """
        生成连接HTML代码

        Args:
            password: 服务器密码

        Returns:
            HTML代码
        """
        connect_url = self.get_connect_url(password)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CS2 Match Server</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 50px;
        }}
        .connect-button {{
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }}
        .connect-button:hover {{
            background-color: #45a049;
        }}
        .server-info {{
            margin: 20px 0;
            padding: 20px;
            background-color: #f0f0f0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>CS2 Match Server</h1>
    <div class="server-info">
        <p><strong>服务器IP:</strong> {self.server_ip}</p>
        <p><strong>端口:</strong> {self.server_port}</p>
        <p><strong>状态:</strong> 运行中</p>
    </div>
    <a href="{connect_url}" class="connect-button">连接到服务器</a>
    <p>点击上方按钮将启动Steam并连接到服务器</p>
    <p>手动连接命令: <code>connect {self.server_ip}:{self.server_port}</code></p>
</body>
</html>
"""
        return html

    def terminate_instance(self):
        """
        终止实例
        """
        if not self.instance_id:
            return

        try:
            req = models.TerminateInstancesRequest()
            req.InstanceIds = [self.instance_id]
            self.client.TerminateInstances(req)
            print(f"实例 {self.instance_id} 已终止")

        except Exception as e:
            print(f"终止实例失败: {e}")


# 使用示例
def main():
    # 初始化服务器管理器
    server = CS2MatchServer(
        secret_id="your_secret_id",
        secret_key="your_secret_key",
        region="ap-guangzhou"
    )

    # 队伍Steam ID配置
    t_team_ids = [
        "76561198000000001",
        "76561198000000002",
        "76561198000000003",
        "76561198000000004",
        "76561198000000005"
    ]

    ct_team_ids = [
        "76561198000000006",
        "76561198000000007",
        "76561198000000008",
        "76561198000000009",
        "76561198000000010"
    ]

    try:
        # 1. 创建抢占式实例
        print("正在创建抢占式实例...")
        instance_id = server.create_spot_instance()

        # 2. 生成比赛配置
        print("生成比赛配置...")
        config = server.generate_match_config(t_team_ids, ct_team_ids)

        # 3. 部署服务器配置
        print("部署服务器配置...")
        server.deploy_server_config(config)

        # 4. 生成连接URL和HTML
        password = config['server_config']['sv_password']
        connect_url = server.get_connect_url(password)
        html_content = server.generate_connect_html(password)

        print(f"\n连接URL: {connect_url}")
        print(f"服务器IP: {server.server_ip}")
        print(f"服务器密码: {password}")

        # 保存HTML文件
        with open('cs2_match_server.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("HTML文件已保存为 cs2_match_server.html")

        # 保持服务器运行
        input("按Enter键终止服务器...")

    except Exception as e:
        print(f"错误: {e}")

    finally:
        # 清理资源
        server.terminate_instance()


if __name__ == "__main__":
    main()
