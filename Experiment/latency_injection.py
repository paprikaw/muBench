import paramiko
import argparse
from scp import SCPClient
import os

# 定义主机名到IP地址的映射
HOST_MAP = {
    "edge": {
        "tb-client-vm-2-1": "172.26.133.107",
        "tb-edge-vm-4-1": "172.26.133.218",
        "tb-edge-vm-4-2": "172.26.133.227",
        "tb-edge-vm-2-1": "172.26.132.14",
        "tb-edge-vm-2-2": "172.26.132.147",
    },
    "cloud": {
        "tb-cloud-vm-8-1": "172.26.129.236",
        "tb-cloud-vm-8-2": "172.26.133.27",
    }
}

# 动态生成脚本内容的函数
def generate_latency_script(hosts, latency="50ms"):
    script = f"""#!/bin/sh
DEV=eth0 # Only apply to eth0
LATENCY="{latency}"

# 清除之前的tc配置
tc qdisc del dev $DEV root

# 添加根队列规则
tc qdisc add dev $DEV root handle 1: prio
tc qdisc add dev eth0 parent 1:1 handle 2: netem delay $LATENCY

# Apply filters for VM CIDRs
"""
    # 为每个CIDR添加过滤器
    for i, ip in enumerate(hosts, start=1):
        script += f"tc filter add dev $DEV protocol ip parent 1: prio 1 u32 match ip dst {ip}/32 flowid 1:1\n"

    # 添加显示配置的命令
    script += """
# Show tc configuration
echo; echo "tc configuration for $DEV:"
tc qdisc show dev $DEV
tc class show dev $DEV
"""
    return script

# 上传和执行脚本的函数
def execute_latency_script_on_cloud(host_ip, script_content):
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 直接使用ssh config中的Host name进行连接
        ssh.connect(hostname=host_ip, username="ubuntu", key_filename="/Users/ericwhite/.ssh/id_rsa")

        # 在本地生成临时脚本文件
        temp_script_path = "/tmp/latency_script.sh"
        with open(temp_script_path, "w") as f:
            f.write(script_content)

        # 创建SCP会话并上传脚本
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(temp_script_path, "/tmp/latency_script.sh")

        # 在远程主机上执行脚本
        stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/latency_script.sh && sudo /tmp/latency_script.sh")
        stdout.channel.recv_exit_status()  # 等待命令完成

        # 打印脚本输出
        print(f"Output from {host_name}:")
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Failed to execute script on {host_name}: {str(e)}")
    finally:
        ssh.close()


# 主函数，遍历所有cloud nodes，生成并执行脚本
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latency Injection Script")
    parser.add_argument("--latency", type=str, required=True, help="Latency value to inject, e.g., '500ms'")
    args = parser.parse_args()

    for host_name in HOST_MAP["cloud"]:
        print(f"Generating and executing script on {host_name}...")

        # 从 edge nodes 获取 VM CIDRs
        vm_ips = list(HOST_MAP["edge"].values())

        # 动态生成脚本内容
        script_content = generate_latency_script(vm_ips, args.latency)

        # 执行脚本
        execute_latency_script_on_cloud(HOST_MAP["cloud"][host_name], script_content)
