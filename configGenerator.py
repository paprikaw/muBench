import json
from string import Template
import argparse
# 从命令行中解析workload和replicaCnt两个变量
parser = argparse.ArgumentParser(description='生成配置文件')
parser.add_argument('--workmodel', type=str, required=True, help='aggregator or chain')
parser.add_argument('--replicaCnt', type=int, required=True, help='replica number')
parser.add_argument('--layer', type=str, required=True, help='node layer') # cloud , edge , all
args = parser.parse_args()
ms_access_gateway = "http://172.26.129.236:31113"
workmodel = args.workmodel
replicaCnt = args.replicaCnt
layer = args.layer
workDir = "/home/ubuntu/muBench"

cloud_node_list = ["tb-cloud-vm-8-1", "tb-cloud-vm-8-2"]
edge_node_list = ["tb-edge-vm-4-1", "tb-edge-vm-4-2", "tb-edge-vm-2-1", "tb-edge-vm-2-2"]
all_node_list = cloud_node_list + edge_node_list
# 定义JSON模板
RunnerTemplate = '''
{
   "RunnerParameters": {
      "ms_access_gateway": "${ms_access_gateway}",
      "workload_files_path_list": [
        "tmp/generated_workload.json"
      ],
      "workload_rounds": 1,
      "workload_type": "periodic",
      "rate": 5,
      "workload_events": 50000,
      "thread_pool_size": 20,
      "result_file": "result",
      "ingress_service": "client"
   },
   "OutputPath": "./",
   "_AfterWorkloadFunction": {
      "_comment": "remove _ from the object name to execute the funcions",
      "file_path": "Function",
      "function_name": "get_prometheus_stats"
   }
}
'''

K8sParametersTemplate = '''
{
   "K8sParameters": {
      "prefix_yaml_file": "MicroServiceDeployment",
      "namespace": "default",
      "image": "paprikaw/mubench:dev",
      "cluster_domain": "cluster",
      "path": "/api/v1",
      "dns-resolver": "kube-dns.kube-system.svc.cluster.local",
      "scheduler-name": "default-scheduler",
      "sleep": 0,
      "dns-resolver": "kube-dns.kube-system.svc.cluster.local",
      "nginx-gw": true,
      "nginx-svc-type": "NodePort"
   },
   "InternalServiceFilePath": "CustomFunctions",
   "OutputPath": "./",
   "WorkModelPath": "tmp/generated_workmodel.json"
}
'''
if workmodel == "aggregator":
    aggregator_workmodel_template = '''
{
  "client": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "aggregator"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            3,
            3
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": false,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 1
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": 1,
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "is_client": true,
    "affinity_required": true,
    "node_affinity": [
      "tb-client-vm-2-1"
    ]
  },
  "aggregator": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "detection"
        ]
      },
      {
        "seq_len": 1,
        "services": [
          "machine-learning"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 2
        },
        "memory_stress": {
          "run": true,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": ${replicaCnt},
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "node_affinity": ${node_affinity}
  },
  "detection": {
    "external_services": [
      {
        "seq_len": 1,
        "services": []
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 4
        },
        "memory_stress": {
          "run": true,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 1000,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "memory-requests": "900Mi",
    "memory-limits": "900Mi",
    "cpu-requests": "900m",
    "cpu-limits": "900m",
    "replicas": ${replicaCnt},
    "node_affinity": ${node_affinity}
  },
  "machine-learning": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "db"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            400,
            400
          ],
          "thread_pool_size": 1,
          "trials": 8
        },
        "memory_stress": {
          "run": true,
          "memory_size": 2000,
          "memory_io": 2000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 100,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "memory-requests": "1900Mi",
    "memory-limits": "1900Mi",
    "cpu-requests": "1900m",
    "cpu-limits": "1900m",
    "replicas": ${replicaCnt},
    "node_affinity": ${node_affinity}
  },
  "db": {
    "external_services": [],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            100,
            100
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": true,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": ${replicaCnt},
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "node_affinity": ${node_affinity}
  },
  "probeclient": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "probeserver"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            3,
            3
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": false,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 1
      }
    },
    "request_method": "rest",
    "workers": 1,
    "threads": 1,
    "replicas": 1,
    "cpu-limits": "100m",
    "memory-limits": "100Mi",
    "is_client": true,
    "is_probe": true,
    "affinity_required": true,
    "node_affinity": [
      "tb-client-vm-2-1"
    ]
  },
  "probeserver": {
    "external_services": [],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 2
        },
        "memory_stress": {
          "run": false,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "is_probe": true,
    "workers": 1,
    "threads": 1,
    "replicas": 1,
    "cpu-limits": "100m",
    "memory-limits": "100Mi",
    "affinity_required": true,
    "node_affinity": [
      "tb-cloud-vm-8-1"
    ]
  }
}
'''
elif workmodel == "chain":
    chain_workmodel_template = '''
{
  "client": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "aggregator"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            3,
            3
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": false,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 1
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": 1,
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "is_client": true,
    "node_affinity": [
      "tb-client-vm-2-1"
    ]
  },
  "aggregator": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "detection"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 2
        },
        "memory_stress": {
          "run": true,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": ${replicaCnt},
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "node_affinity": ${node_affinity}
  },
  "detection": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "machine-learning"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 4
        },
        "memory_stress": {
          "run": true,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 1000,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "memory-requests": "900Mi",
    "memory-limits": "900Mi",
    "cpu-requests": "900m",
    "cpu-limits": "900m",
    "replicas": ${replicaCnt},
    "node_affinity": ${node_affinity}
  },
  "machine-learning": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "db"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            400,
            400
          ],
          "thread_pool_size": 1,
          "trials": 8
        },
        "memory_stress": {
          "run": true,
          "memory_size": 2000,
          "memory_io": 2000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 100,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "memory-requests": "1900Mi",
    "memory-limits": "1900Mi",
    "cpu-requests": "1900m",
    "cpu-limits": "1900m",
    "replicas": ${replicaCnt},
    "node_affinity": ${node_affinity}
  },
  "db": {
    "external_services": [],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": true,
          "range_complexity": [
            100,
            100
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": true,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": true,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "workers": 4,
    "threads": 16,
    "replicas": ${replicaCnt},
    "cpu-requests": "600m",
    "cpu-limits": "600m",
    "memory-requests": "600Mi",
    "memory-limits": "600Mi",
    "node_affinity": ${node_affinity}
    ]

  },
  "probeclient": {
    "external_services": [
      {
        "seq_len": 1,
        "services": [
          "probeserver"
        ]
      }
    ],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            3,
            3
          ],
          "thread_pool_size": 1,
          "trials": 1
        },
        "memory_stress": {
          "run": false,
          "memory_size": 100,
          "memory_io": 100
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 1
      }
    },
    "request_method": "rest",
    "workers": 1,
    "threads": 1,
    "replicas": 1,
    "cpu-limits": "100m",
    "memory-limits": "100Mi",
    "is_client": true,
    "is_probe": true,
    "node_affinity": [
      "tb-client-vm-2-1"
    ]
  },
  "probeserver": {
    "external_services": [],
    "internal_service": {
      "loader": {
        "cpu_stress": {
          "run": false,
          "range_complexity": [
            200,
            200
          ],
          "thread_pool_size": 1,
          "trials": 2
        },
        "memory_stress": {
          "run": false,
          "memory_size": 1000,
          "memory_io": 1000
        },
        "disk_stress": {
          "run": false,
          "tmp_file_name": "mubtestfile.txt",
          "disk_write_block_count": 10,
          "disk_write_block_size": 1024
        },
        "sleep_stress": {
          "run": false,
          "sleep_time": 0.01
        },
        "mean_bandwidth": 10
      }
    },
    "request_method": "rest",
    "is_probe": true,
    "workers": 1,
    "threads": 1,
    "replicas": 1,
    "cpu-limits": "100m",
    "memory-limits": "100Mi",
    "node_affinity": [
      "tb-cloud-vm-8-1"
    ]
  }
}
    '''
else:
    assert(False)


# 注入变量
if layer == "cloud":
    node_affinity = cloud_node_list
elif layer == "edge":
    node_affinity = edge_node_list
elif layer == "all":
    node_affinity = all_node_list
else:
    assert(False)

variables = {
    'ms_access_gateway': ms_access_gateway,
    'replicaCnt': replicaCnt,
    'node_affinity': json.dumps(node_affinity) 
}

runner_json_str = Template(RunnerTemplate).substitute(variables)
k8s_json_str = Template(K8sParametersTemplate).substitute(variables)
if workmodel == "chain":
    aggregator_workmodel_json_str = Template(chain_workmodel_template).substitute(variables)
else: 
    aggregator_workmodel_json_str = Template(aggregator_workmodel_template).substitute(variables)


# 解析为Python字典
runner_json_obj = json.loads(runner_json_str)
k8s_json_obj = json.loads(k8s_json_str)
if workmodel == "chain":
    workmodel_json_obj = json.loads(chain_workmodel_template)
else:
    workmodel_json_obj = json.loads(aggregator_workmodel_json_str)

# 将生成的JSON对象写入文件
with open(f'{workDir}/tmp/runner_parameters.json', 'w') as runner_file:
    json.dump(runner_json_obj, runner_file, indent=2)

with open(f'{workDir}/tmp/k8s_parameters.json', 'w') as k8s_file:
    json.dump(k8s_json_obj, k8s_file, indent=2)

with open(f'{workDir}/tmp/generated_workmodel.json', 'w') as workmodel_file:
    json.dump(workmodel_json_obj, workmodel_file, indent=2)