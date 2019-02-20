from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import time
import math
import os
import sys
from socketIO_client import SocketIO

inputData = {}

SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}

def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.
      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776
      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])

def worker(duration, memoryPerProcess):
    print("worker starting")
    print("allocating ",memoryPerProcess,"bytes")
    allocated='a'*memoryPerProcess
    start = time.perf_counter()
    res = 0
    while True:
        print(".")
        now = time.perf_counter()
        if (now - start) > duration:
            break
    print("worker finished")
    allocated=None
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
    memory = human2bytes(inputData.get('memory','128Mi'))
    memoryPerProcess = math.ceil(memory/cpu_count)
    # start the algorithm async

    for i in range(cpu_count):
        p = Process(target=worker, args=(duration, memoryPerProcess,))
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
socketIO = SocketIO('http://40.69.222.75/hkube/debug/xxx/socket.io')

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
