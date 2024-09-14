from readline import append_history_file
import threading
import os
import glob
import random
import jsonmerge
from Loader import StressLoader

class InternalServiceExecutor:
    def __init__(self, params):
        # 初始化参数
        self.loader = StressLoader(params)
        # 初始化带宽测试的数据量
    def run_internal_service(self):
        return self.loader.run_loaders()