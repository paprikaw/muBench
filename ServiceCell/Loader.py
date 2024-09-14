import random
import time
import os
from concurrent.futures import ThreadPoolExecutor, wait
import jsonmerge
import string
import Loader

class StressLoader:
    def __init__(self, params):
        # 初始化参数
        self.params_processed = False
        self.default_params = {
            "cpu_stress": {"run": False, "range_complexity": [100, 100], "thread_pool_size": 1, "trials": 1},
            "memory_stress": {"run": False, "memory_size": 10000, "memory_io": 1000},
            "disk_stress": {"run": False, "tmp_file_name": "mubtestfile.txt", "disk_write_block_count": 1000, "disk_write_block_size": 1024},
            "sleep_stress": {"run": False, "sleep_time": 0.01},
            "mean_bandwidth": 11
        }
        self.params = jsonmerge.merge(self.default_params, params)
        print(self.params)
        # 初始化带宽测试的数据量
        self.response_body = ''.join('a' for _ in range(int(max(1, 1000 * self.params["mean_bandwidth"]))))
    
    def cpu_loader_job(self, params):
        cpu_load = random.randint(params["range_complexity"][0], params["range_complexity"][1])
        trials = int(params["trials"])

        for _ in range(trials):
            pi_greco = list()
            q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
            counter = 0
            while True:
                if 4 * q + r - t < m * t:
                    pi_greco.append(str(m))
                    q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
                    if counter > cpu_load - 1:
                        break
                    else:
                        counter += 1
                else:
                    q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2

    def cpu_loader(self, params):
        pool_size = int(params["thread_pool_size"])
        pool = ThreadPoolExecutor(pool_size)
        futures = [pool.submit(self.cpu_loader_job, params) for _ in range(pool_size)]
        wait(futures)

    def bandwidth_loader(self):
        return self.response_body

    def memory_loader(self, params):
        memory_size = params["memory_size"]
        memory_io = params["memory_io"]

        dummy_buffer = ['A' * 1000 for _ in range(memory_size)]
        for i in range(memory_io):
            v = dummy_buffer[i % memory_size]  # read operation
            dummy_buffer[i % memory_size] = ['A' * 1000]  # write operation
        return dummy_buffer

    def disk_loader(self, params):
        filename_base = params["tmp_file_name"]
        rnd_str = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        filename = f"{rnd_str}-{filename_base}"
        blocks_count = params["disk_write_block_count"]
        block_size = params["disk_write_block_size"]

        # Write stress
        with open(filename, 'wb') as f:
            for _ in range(blocks_count):
                f.write(os.urandom(block_size))

        # Read stress
        with open(filename, 'rb') as f:
            offsets = list(range(0, blocks_count * block_size, block_size))
            random.shuffle(offsets)
            for offset in offsets:
                f.seek(offset)
                f.read(block_size)

        os.remove(filename)

    def sleep_loader(self, params):
        time.sleep(float(params["sleep_time"]))

    def run_loaders(self):
        if self.params['cpu_stress']['run']:
            self.cpu_loader(self.params['cpu_stress'])
        if self.params['memory_stress']['run']:
            self.memory_loader(self.params['memory_stress'])
        if self.params['disk_stress']['run']:
            self.disk_loader(self.params['disk_stress'])
        if self.params['sleep_stress']['run']:
            self.sleep_loader(self.params['sleep_stress'])
        return self.bandwidth_loader()


if __name__ == '__main__':
    params = {
        "cpu_stress": {"run": True, "range_complexity": [100, 100], "thread_pool_size": 1, "trials": 10},
        "memory_stress": {"run": True, "memory_size": 10000, "memory_io": 1000},
        "disk_stress": {"run": True, "tmp_file_name": "mubtestfile.txt", "disk_write_block_count": 1000, "disk_write_block_size": 1024},
        "sleep_stress": {"run": False, "sleep_time": 0.01},
        "mean_bandwidth": 10000
    }

    stress_loader = StressLoader(params)
    cur = time.time()
    stress_loader.run_loaders()
    print(time.time() - cur)