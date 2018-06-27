from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import time
import os
import sys
from socketIO_client import SocketIO

inputData = {}


def worker(duration):
    print("worker starting")
    start = time.perf_counter()
    res = 0
    while True:
        now = time.perf_counter()
        if (now - start) > duration:
            break
    print("worker finished")
    return res


def waitForProcesses(processes):
    while True:
        isrunning=False
        for p in processes:
            if p.is_alive():
                isrunning=True
        if not isrunning:
            break
        time.sleep(0.5)
    if processes[0].exitcode < 0:
        return
    out_message = {'command': 'done', 'data': 'finished'}
    socketIO.emit('done', out_message)


processesGlobal = []


def run_algo():
    cpu_count = int(inputData.get('cpu', 1))
    duration = inputData.get('duration',10)
    # start the algorithm async

    for i in range(cpu_count):
        p = Process(target=worker, args=(duration,))
        processesGlobal.append(p)
        p.start()

    pool = ThreadPoolExecutor(1)
    future = pool.submit(waitForProcesses, processesGlobal)


def stop_algo():
    print('got stop command')
    for p in processesGlobal:
        p.terminate()


def on_connect():
    print('connect')


def on_disconnect():
    print('disconnect')


def on_reconnect():
    print('reconnect')


def on_init(*args):
    message = args[0].get("data",{})
    print("message",message)
    try:
        global inputData
        inputData = message["input"][0]
    except Exception as e:
        print("error parsing input", e)
    out_message = {'command': 'initialized'}
    socketIO.emit('initialized', out_message)


def on_start(*args):
    outMessage = {'command': 'started'}
    socketIO.emit('started', outMessage)
    run_algo()

def on_stop(*args):
    print("Got stop")
    stop_algo()
    outMessage = {'command': 'stopped'}
    socketIO.emit('stopped', outMessage)


def on_exit(*args):
    code = 0
    print("args:", args[0])
    if args and args[0]:
        code = args[0].get('exitCode', 0)
    print('Got exit command. Exiting with code', code)
    sys.exit(code)


print('starting')
socketPort = os.getenv('WORKER_SOCKET_PORT', 3000)
socketIO = SocketIO('127.0.0.1', socketPort)

socketIO.on('connect', on_connect)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)

# Listen
# socketIO.on('commandMessage', on_command)
socketIO.on('initialize', on_init)
socketIO.on('start', on_start)
socketIO.on('stop', on_stop)
socketIO.on('exit', on_exit)
socketIO.wait()
