'''
Created on 2016. 11. 3.

@author: "comfact"
'''

import time
import threading
try: from Queue import Queue
except: from queue import Queue

#===============================================================================
# System Thread
#===============================================================================
class SystemThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._tb_sw = False
        
    def start(self):
        if not self._tb_sw:
            self._tb_sw = True
            threading.Thread.start(self)
    
    def stop(self):
        if self._tb_sw:
            self._tb_sw = False
            self._stop()
            self.join()
        
    def run(self):
        while self._tb_sw: self.thread()
            
    def thread(self): pass

#===============================================================================
# Scheduler
#===============================================================================
class SchedTask:
    def __init__(self, tick):
        self.schedtask_tick = tick
        self.schedtask_cur = 0
        
    def __sched_wrapper__(self, sched_tick):
        self.schedtask_cur += sched_tick
        if self.schedtask_cur >= self.schedtask_tick:
            self.schedtask_cur = 0
            self.sched()
            
    def sched(self): pass

class Scheduler(SystemThread):
    
    def __init__(self, tick):
        SystemThread.__init__(self)
        self.tick = tick
        self.queue = []
        self.regreq = Queue()
    
    def thread(self):
        start_time = time.time()
        while not self.regreq.empty():
            task = self.regreq.get()
            self.queue.append(task)
        for task in self.queue:
            try: task.__sched_wrapper__(self.tick)
            except: continue
        end_time = time.time()
        sleep_time = self.tick - (end_time - start_time)
        if sleep_time > 0: time.sleep(sleep_time)
        
            
    def register(self, task):
        self.regreq.put(task)
        
    def unregister(self, task):
        sw_stat = self._tb_sw
        if sw_stat: self.stop()
        if task in self.queue: self.queue.remove(task)
        if sw_stat: self.start()
