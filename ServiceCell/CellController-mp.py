from __future__ import print_function
import argparse
import json
import os
import sys
import time
import traceback
from threading import Thread
from concurrent import futures
#from multiprocessing import Array, Manager, Value
import logging
import gunicorn.app.base
from flask import Flask, Response, json, make_response, request
import prometheus_client
from prometheus_client import CollectorRegistry, Summary, multiprocess, Histogram

from ExternalServiceExecutor import init_REST, init_gRPC, run_external_service
from InternalServiceExecutor import InternalServiceExecutor 

import mub_pb2_grpc as pb2_grpc
import mub_pb2 as pb2
import grpc

from urllib.parse import parse_qsl, urlencode

# Configuration of global variables

jaeger_headers_list = [
    'x-request-id',
    'x-b3-traceid',
    'x-b3-spanid',
    'x-b3-parentspanid',
    'x-b3-sampled',
    'x-b3-flags',
    'x-datadog-trace-id',
    'x-datadog-parent-id',
    'x-datadog-sampling-priority',
    'x-ot-span-context',
    'grpc-trace-bin',
    'traceparent',
    'x-cloud-trace-context',
]

# Flask APP
app = Flask(__name__)
ID = os.environ["APP"]
ZONE = os.environ["ZONE"]  # Pod Zone
K8S_APP = os.environ["K8S_APP"]  # K8s label app
PN = os.environ["PN"] # Number of processes
TN = os.environ["TN"] # Number of thread per process
NODE_NAME = os.environ["NODE_NAME"] # Node Name
CLOUD_LATENCY = float(os.environ["CLOUD_LATENCY"]) # Cloud Latency
CLOUD_NODE_NAME_PREFIX = os.environ["CLOUD_NODE_NAME_PREFIX"] # Cloud Node Name Prefix
# 从环境变量中获取 JSON 数据
execution_time_map_json = os.environ.get("EXECUTION_TIME_MAP")

current_execution_time = -1
service_execution_times = []
if not execution_time_map_json:
    raise ValueError("CONFIG_JSON environment variable is not set")

# 反序列化 JSON 数据
try:
    execution_time_map = json.loads(execution_time_map_json)
except json.JSONDecodeError as e:
    raise ValueError(f"Error parsing JSON: {e}")

# 打印反序列化后的数据
print("Execution Time Map:", execution_time_map)
traceEscapeString = "__"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#globalDict=Manager().dict()
globalDict=dict()
def read_config_files():
    res = dict()
    with open('MSConfig/workmodel.json') as f:
        workmodel = json.load(f)
        # shrink workmodel
        for service in workmodel:
            app.logger.info(f'service: {service}')
            if service==ID:
                res[service]=workmodel[service]
            else:
                res[service]={"url":workmodel[service]["url"],"path":workmodel[service]["path"]}
    return res
globalDict['work_model'] = read_config_files()    # must be shared among processes for hot update

# default behaviour
work_model_config = globalDict['work_model'][ID]
service_mesh_config = work_model_config['external_services'] 
internal_service_config = work_model_config['internal_service']

if "request_method" in globalDict['work_model'][ID].keys():
    request_method = globalDict['work_model'][ID]["request_method"].lower()
else:
    request_method = "rest"

########################### PROMETHEUS METRICS
registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
RESPONSE_SIZE = Summary('mub_response_size', 'Response size',
                        ['zone', 'app_name', 'method', 'endpoint', 'from', 'kubernetes_service'], registry=registry
                        )

INTERNAL_PROCESSING = Summary('mub_internal_processing_latency_milliseconds', 'Latency of internal service',
                           ['zone', 'app_name', 'method', 'endpoint'],registry=registry
                           )
EXTERNAL_PROCESSING = Summary('mub_external_processing_latency_milliseconds', 'Latency of external services',
                           ['zone', 'app_name', 'method', 'endpoint'], registry=registry
                           )
REQUEST_PROCESSING = Summary('mub_request_processing_latency_milliseconds', 'Request latency including external and internal service',
                           ['zone', 'app_name', 'method', 'endpoint', 'from', 'kubernetes_service'],registry=registry
                           )

buckets=[0.5, 1, 10, 100 ,1000, 10000, float("inf")] 
INTERNAL_PROCESSING_BUCKET = Histogram('mub_internal_processing_latency_milliseconds_bucket', 'Latency of internal service',
                           ['zone', 'app_name', 'method', 'endpoint'],registry=registry,buckets=buckets
                           )
EXTERNAL_PROCESSING_BUCKET = Histogram('mub_external_processing_latency_milliseconds_bucket', 'Latency of external services',
                           ['zone', 'app_name', 'method', 'endpoint'], registry=registry,buckets=buckets
                           )
REQUEST_PROCESSING_BUCKET = Histogram('mub_request_processing_latency_milliseconds_bucket', 'Request latency including external and internal service',
                           ['zone', 'app_name', 'method', 'endpoint', 'from', 'kubernetes_service'],registry=registry,buckets=buckets
)


internal_service_params = list(internal_service_config.values())[0]
internal_service_executer = InternalServiceExecutor(internal_service_params)

@app.route(f"{globalDict['work_model'][ID]['path']}", methods=['GET','POST'])
def start_worker():
    global work_model_config 
    global service_mesh_config 
    global internal_service_config 
    global InternalServiceExecutor
    global current_execution_time
    global service_execution_times
    cur_srv_execution_time = time.time()
    try:
        start_request_processing = time.time()
        app.logger.info('Request Received')
        
        query_string = request.query_string.decode()
        behaviour_id = request.args.get('bid', default = 'default', type = str)
        # update internal service behaviour
        if behaviour_id != 'default' and "alternative_behaviors" in work_model_config.keys():
                if behaviour_id in work_model_config['alternative_behaviors'].keys():
                    if "internal_services" in work_model_config['alternative_behaviors'][behaviour_id].keys():
                        internal_service_config = work_model_config['alternative_behaviors'][behaviour_id]['internal_service']

        # trace context propagation
        jaeger_headers = dict()
        for jhdr in jaeger_headers_list:
            val = request.headers.get(jhdr)
            if val is not None:
                jaeger_headers[jhdr] = val

        # if POST check the presence of a trace
        trace=dict()
        if request.method == 'POST':
            trace = request.json
            # sanity_check
            assert len(trace.keys())==1, 'bad trace format'
            assert ID == list(trace)[0].split(traceEscapeString)[0], "bad trace format, ID"
            trace[ID] = trace[list(trace)[0]] # We insert 1 more key "s0": [value] 
            
        if len(trace)>0:
        # trace-driven request
            n_groups = len(trace[ID])
            service_mesh_config = list()
            for i in range(0,n_groups):
                group = trace[ID][i]
                group_dict = dict()
                group_dict['seq_len'] = len(group)
                group_dict['services'] = list(group.keys())
                service_mesh_config.append(group_dict)
        else:
            # update external service behaviour
            if behaviour_id != 'default' and "alternative_behaviors" in work_model_config.keys():
                if behaviour_id in work_model_config['alternative_behaviors'].keys():
                    if "external_services" in work_model_config['alternative_behaviors'][behaviour_id].keys():
                        service_mesh_config = work_model_config['alternative_behaviors'][behaviour_id]['external_services']
        # 读取query string中的上一个pod所在的layer，并且和当前pod
        # app.logger.info("*************** Simulate Cloud Latency ***************")
        # query_params = dict(parse_qsl(query_string))
        # last_pod_node_name = query_params.get('last_pod_node_name', NODE_NAME)
        # logging.info(f"NODE_NAME: {NODE_NAME}, last_pod_node_name: {last_pod_node_name}")
        # if is_cloud(NODE_NAME) != is_cloud(last_pod_node_name):
        #     logging.info(f"Sleeping for cloud latency: {CLOUD_LATENCY}")
        #     time.sleep(CLOUD_LATENCY)
        # query_params['last_pod_node_name'] = NODE_NAME
        # query_string = urlencode(query_params)
        # Execute the internal service
        app.logger.info("*************** INTERNAL SERVICE STARTED ***************")
        start_local_processing = time.time()
        internal_service_executer.run_internal_service() # TODO: This implementation is not supported for trace driven
        local_processing_latency = time.time() - start_local_processing
        # Apply the node specific overhead
        sleep_time = execution_time_map[NODE_NAME] * local_processing_latency
        time.sleep(sleep_time)
        app.logger.info(f"Execution time: {local_processing_latency}")
        app.logger.info(f"Sleeping for more execution time: {sleep_time}")
        app.logger.info(f"Sleeping factor: {execution_time_map[NODE_NAME]}")
        local_processing_latency = time.time() - start_local_processing
        current_execution_time = local_processing_latency
        INTERNAL_PROCESSING.labels(ZONE, K8S_APP, request.method, request.path).observe(local_processing_latency*1000)
        INTERNAL_PROCESSING_BUCKET.labels(ZONE, K8S_APP, request.method, request.path).observe(local_processing_latency*1000)
        RESPONSE_SIZE.labels(ZONE, K8S_APP, request.method, request.path, request.remote_addr, ID).observe(1)
        app.logger.info("############### INTERNAL SERVICE FINISHED! ###############")
        # Execute the external services
        start_external_request_processing = time.time()
        app.logger.info("*************** EXTERNAL SERVICES STARTED ***************")
        service_calling_start_time = time.time()
        if len(service_mesh_config) > 0:
            if len(trace)>0:
                service_error_dict = run_external_service(service_mesh_config,globalDict['work_model'],query_string,trace[ID],app, jaeger_headers)
            else:
                service_error_dict = run_external_service(service_mesh_config,globalDict['work_model'],query_string,dict(),app, jaeger_headers)
            if len(service_error_dict):
                app.logger.error(service_error_dict)
                app.logger.error("Error in request external services")
                app.logger.error(service_error_dict)
                return make_response(json.dumps({"message": "Error in external services request"}), 500)
        service_calling_end_time = time.time()
        # 计算调用外部服务的延迟（以毫秒为单位）
        service_calling_latency = (service_calling_end_time - service_calling_start_time) * 1000
        # 获取当前的 Unix 时间戳（以毫秒为单位）
        current_timestamp = int(time.time())
        app.logger.info("############### EXTERNAL SERVICES FINISHED! ###############")
        response = make_response({
            "service_calling_latency": service_calling_latency,
            "timestamp": current_timestamp
        })
        response.mimetype = "text/plain"
        EXTERNAL_PROCESSING.labels(ZONE, K8S_APP, request.method, request.path).observe((time.time() - start_external_request_processing)*1000)
        EXTERNAL_PROCESSING_BUCKET.labels(ZONE, K8S_APP, request.method, request.path).observe((time.time() - start_external_request_processing)*1000)
        
        REQUEST_PROCESSING.labels(ZONE, K8S_APP, request.method, request.path, request.remote_addr, ID).observe((time.time() - start_request_processing)*1000)
        REQUEST_PROCESSING_BUCKET.labels(ZONE, K8S_APP, request.method, request.path, request.remote_addr, ID).observe((time.time() - start_request_processing)*1000)

        # Add trace context propagation headers to the response
        response.headers.update(jaeger_headers)
        service_execution_times.append(time.time() - cur_srv_execution_time)
        return response
    except Exception as err:
        app.logger.error("Error in start_worker", err)
        # app.logger.error(traceback.format_exc())
        return json.dumps({"message": "Error"}), 500

def is_cloud(node_name: str) -> bool:
    return node_name.startswith(CLOUD_NODE_NAME_PREFIX)

@app.route('/rtt', methods=['GET'])
def round_trip_time():
    return ''

@app.route('/execution_time', methods=['GET'])
def metrics():
    if len(service_execution_times) <= 20:
        return make_response({"execution_times": service_execution_times})
    else:
        return make_response({"execution_times": service_execution_times[-20:]})

# Custom Gunicorn application: https://docs.gunicorn.org/en/stable/custom.html
class HttpServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# GRPC (no multi-process)
gRPC_port = 51313
class gRPCThread(Thread, pb2_grpc.MicroServiceServicer):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(TN)))

    def __init__(self):
        Thread.__init__(self)

    def GetMicroServiceResponse(self, req, context):
        try:
            start_request_processing = time.time()
            app.logger.info.info('Request Received')
            message = req.message
            remote_address = context.peer().split(":")[1]
            app.logger.info(f'I am service: {ID} and I received this message: --> "{message}"')

            # Execute the internal service
            app.logger.info("*************** INTERNAL SERVICE STARTED ***************")
            start_local_processing = time.time()
            body = internal_service_executer.run_internal_service()
            local_processing_latency = time.time() - start_local_processing
            INTERNAL_PROCESSING.labels(ZONE, K8S_APP, "grpc", "grpc").observe(local_processing_latency*1000)
            RESPONSE_SIZE.labels(ZONE, K8S_APP, "grpc", "grpc", remote_address, ID).observe(len(body))
            app.logger.info("len(body): %d" % len(body))
            app.logger.info("############### INTERNAL SERVICE FINISHED! ###############")

            # Execute the external services
            app.logger.info("*************** EXTERNAL SERVICES STARTED ***************")
            start_external_request_processing = time.time()
            if len(service_mesh_config) > 0:
                service_error_dict = run_external_service(service_mesh_config, globalDict['work_model'])
                if len(service_error_dict):
                    app.logger.error(service_error_dict)
                    app.logger.error("Error in request external services")
                    app.logger.error(service_error_dict)
                    result = {'text': f"Error in external services request", 'status_code': False}
                    return pb2.MessageResponse(**result)
            app.logger.info("############### EXTERNAL SERVICES FINISHED! ###############")

            result = {'text': body, 'status_code': True}
            EXTERNAL_PROCESSING.labels(ZONE, K8S_APP, "grpc", "grpc").observe((time.time() - start_external_request_processing)*1000)
            REQUEST_PROCESSING.labels(ZONE, K8S_APP, "grpc", "grpc", remote_address, ID).observe(
                (time.time() - start_request_processing)*1000)
            return pb2.MessageResponse(**result)
        except Exception as err:
            app.logger.error("Error: in GetMicroServiceResponse,", err)
            result = {'text': f"Error: in GetMicroServiceResponse, {str(err)}", 'status_code': False}
            return pb2.MessageResponse(**result)

    def run(self):
        pb2_grpc.add_MicroServiceServicer_to_server(self, self.server)
        self.server.add_insecure_port(f'[::]:{gRPC_port}')
        self.server.start()

if __name__ == '__main__':
    # 初始化interal function
    if request_method == "rest":
        init_REST(app)
        # Start Gunicorn HTTP REST Server (multi-process)
        options_gunicorn = {
            'bind': '%s:%s' % ('0.0.0.0', 8080),
            'workers': PN,
            'config': "/app/gunicorn.conf.py",
            'threads':TN
        }
        HttpServer(app, options_gunicorn).run()
    elif request_method == "grpc":
        work_model_config = globalDict['work_model'][ID]
        service_mesh_config = work_model_config['external_services']
        init_gRPC(service_mesh_config, globalDict['work_model'], gRPC_port,app)
        # Start the gRPC server
        grpc_thread = gRPCThread()
        grpc_thread.run()
        # Flask HTTP REST server started for Prometheus metrics and for the entry point (s0) that anyway receives REST requests from API gateway
        app.run(host='0.0.0.0', port=8080, threaded=True)
    else:
        app.logger.info("Error: Unsupported request method")
        sys.exit(0)