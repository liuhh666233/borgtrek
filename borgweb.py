import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path
from flask import Flask, Response, request

runBackupScript = "/home/stroblme/Documents/borgBackup.sh"
tag = '201221'
sink = '/media/veracrypt2/movies'
source = '/media/veracrypt1/movies'


files = list(Path(source).rglob("*"))
print(f"Found {len(files)} files")
# while True:
#     rlist = listPoll.poll()
#     for fd, event in rlist:
#         out = os.read(fd, 1024)

q = queue.Queue()
progress = dict()

progress[tag] = dict()
progress[tag]['total'] = len(files)
progress[tag]['processed'] = 0

def runBackup(name):
    t = threading.currentThread()

    logging.info("Thread %s: starting", name)

    listProcess = subprocess.Popen(['/usr/bin/borg', 'create', '--progress', '--stats', '--log-json', sink+'::'+tag, source], stderr=subprocess.PIPE)

    # listProcess = subprocess.Popen(['/usr/bin/borg', 'list', '--log-json', sink], stderr=subprocess.PIPE)
    listPoll = select.poll()
    listPoll.register(listProcess.stderr)

    out = -1
    while(out != b'' and getattr(t, "runThread", False)):
        rlist = listPoll.poll()
        for fd, event in rlist:
            out = os.read(fd, 1024)
            q.put(out.decode().replace('\n',''))

    logging.info("Thread %s: finishing", name)

def publish(name):
    t = threading.currentThread()
    
    logging.info("Thread %s: starting", name)

    while(getattr(t, "runThread", False)):
        while(q.empty()):
            time.sleep(0.1)

        qPt = q.get()

        if qPt != "":
            j = json.loads(qPt)

            if "archive_progress" in j["type"]:
                # print("path" + j["path"])
                # print("o:" + str(j["original_size"]))
                # print("c:" + str(j["compressed_size"]))
                # print("d:" + str(j["deduplicated_size"]))
                progress[tag]['processed'] = j["nfiles"]
                # print(f"Processing {nfiles} of {len(files)}")

            elif "progress_message" in j["type"]:
                logging.info("path" + str(j["time"]))

            else:
                logging.info(j["message"])
                

        q.task_done()

    logging.info("Thread %s: finishing", name)



app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/status')
def getStatus():
    return progress

@app.route('/status/<tag>')
def getStatus(tag):
    return {'tag':tag, 'progress':progress[tag]}

@app.route('/kill')
def kill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"

    logging.basicConfig(format=format, level=logging.INFO,

                        datefmt="%H:%M:%S")


    logging.info("Main    : before creating thread")

    backupThread = threading.Thread(target=runBackup, args=(1,))
    backupThread.runThread = True

    publishThread = threading.Thread(target=publish, args=(2,))
    publishThread.runThread = True


    logging.info("Main    : before running thread")

    publishThread.start()

    backupThread.start()

    app.run(host='192.168.1.114', port=8020)

    logging.info("Main    : wait for the thread to finish")

    backupThread.join()

    logging.info("Main    : Backup Thread joined")

    publishThread.runThread = False

    publishThread.join()

    logging.info("Main    : Publish Thread joined")


    logging.info("Main    : all done")