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
ml_cpu = 1400
ml_memory = 1400
db_cpu = 400
db_memory = 400
aggregator_cpu = 600
aggregator_memory = 600
detection_cpu = 900
detection_memory = 900

# 定义JSON模板
RunnerTemplate = '''
{
   "RunnerParameters": {
      "ms_access_gateway": "${ms_access_gateway}",
      "workload_files_path_list": [
        "tmp/generated_workload.json"
      ],
      "workload_rounds": 1,
      "workload_type": "greedy",
      "workload_events": 50000,
      "thread_pool_size": 1,
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
if workmodel == "aggregator_parallel":
    workmodel_template = '''
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
    "cpu-requests": "${aggregator_cpu}m",
    "cpu-limits": "${aggregator_cpu}m",
    "memory-requests": "${aggregator_memory}Mi",
    "memory-limits": "${aggregator_memory}Mi",
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
    "memory-requests": "${detection_memory}Mi",
    "memory-limits": "${detection_memory}Mi",
    "cpu-requests": "${detection_cpu}m",
    "cpu-limits": "${detection_cpu}m",
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
    "memory-requests": "${ml_memory}Mi",
    "memory-limits": "${ml_memory}Mi",
    "cpu-requests": "${ml_cpu}m",
    "cpu-limits": "${ml_cpu}m",
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
    "cpu-requests": "${db_cpu}m",
    "cpu-limits": "${db_cpu}m",
    "memory-requests": "${db_memory}Mi",
    "memory-limits": "${db_memory}Mi",
    "node_affinity": ${node_affinity}
  }
}
'''
elif workmodel == "chain":
    workmodel_template = '''
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
    "cpu-requests": "${aggregator_cpu}m",
    "cpu-limits": "${aggregator_cpu}m",
    "memory-requests": "${aggregator_memory}Mi",
    "memory-limits": "${aggregator_memory}Mi",
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
    "memory-requests": "${detection_memory}Mi",
    "memory-limits": "${detection_memory}Mi",
    "cpu-requests": "${detection_cpu}m",
    "cpu-limits": "${detection_cpu}m",
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
    "memory-requests": "${ml_memory}Mi",
    "memory-limits": "${ml_memory}Mi",
    "cpu-requests": "${ml_cpu}m",
    "cpu-limits": "${ml_cpu}m",
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
    "cpu-requests": "${db_cpu}m",
    "cpu-limits": "${db_cpu}m",
    "memory-requests": "${db_memory}Mi",
    "memory-limits": "${db_memory}Mi",
    "node_affinity": ${node_affinity}
  }
}
    '''
elif workmodel == "aggregator_sequential":
    workmodel_template = '''
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
        "seq_len": 3,
        "services": [
          "detection",
          "machine-learning",
          "db"
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
    "cpu-requests": "${aggregator_cpu}m",
    "cpu-limits": "${aggregator_cpu}m",
    "memory-requests": "${aggregator_memory}Mi",
    "memory-limits": "${aggregator_memory}Mi",
    "node_affinity": ${node_affinity}
  },
  "detection": {
    "external_services": [],
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
    "memory-requests": "${detection_memory}Mi",
    "memory-limits": "${detection_memory}Mi",
    "cpu-requests": "${detection_cpu}m",
    "cpu-limits": "${detection_cpu}m",
    "replicas": ${replicaCnt},
    "node_affinity": ${node_affinity}
  },
  "machine-learning": {
    "external_services": [],
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
    "memory-requests": "${ml_memory}Mi",
    "memory-limits": "${ml_memory}Mi",
    "cpu-requests": "${ml_cpu}m",
    "cpu-limits": "${ml_cpu}m",
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
    "cpu-requests": "${db_cpu}m",
    "cpu-limits": "${db_cpu}m",
    "memory-requests": "${db_memory}Mi",
    "memory-limits": "${db_memory}Mi",
    "node_affinity": ${node_affinity}
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
    'node_affinity': json.dumps(node_affinity),
    'aggregator_cpu': aggregator_cpu,
    'aggregator_memory': aggregator_memory,
    'detection_cpu': detection_cpu,
    'detection_memory': detection_memory,
    'ml_cpu': ml_cpu,
    'ml_memory': ml_memory,
    'db_cpu': db_cpu,
    'db_memory': db_memory,
}

runner_json_str = Template(RunnerTemplate).substitute(variables)
k8s_json_str = Template(K8sParametersTemplate).substitute(variables)
workmodel_json_str = Template(workmodel_template).substitute(variables)


# 解析为Python字典
runner_json_obj = json.loads(runner_json_str)
k8s_json_obj = json.loads(k8s_json_str)
workmodel_json_obj = json.loads(workmodel_json_str)

# 将生成的JSON对象写入文件
with open(f'{workDir}/tmp/runner_parameters.json', 'w') as runner_file:
    json.dump(runner_json_obj, runner_file, indent=2)

with open(f'{workDir}/tmp/k8s_parameters.json', 'w') as k8s_file:
    json.dump(k8s_json_obj, k8s_file, indent=2)

with open(f'{workDir}/tmp/generated_workmodel.json', 'w') as workmodel_file:
    json.dump(workmodel_json_obj, workmodel_file, indent=2)