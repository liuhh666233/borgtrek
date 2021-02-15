import os, sys, select, subprocess, logging, threading, time
import queue
import json

runBackupScript = "/home/stroblme/Documents/borgBackup.sh"
tag = '201221'
sink = '/media/veracrypt2/movies'
source = '/media/veracrypt1/movies'




# while True:
#     rlist = listPoll.poll()
#     for fd, event in rlist:
#         out = os.read(fd, 1024)

q = queue.Queue()

def runBackup(name):
    t = threading.currentThread()

    logging.info("Thread %s: starting", name)

    # listProcess = subprocess.Popen(['/usr/bin/borg', 'create', '--progress', '--log-json', sink+'::'+tag, source], stdout=subprocess.PIPE)

    listProcess = subprocess.Popen(['/usr/bin/borg', 'list', '--log-json', sink], stdout=subprocess.PIPE)
    listPoll = select.poll()
    listPoll.register(listProcess.stdout)

    out = -1
    while(out != b'' and getattr(t, "runThread", False)):
        rlist = listPoll.poll()
        for fd, event in rlist:
            out = os.read(fd, 1024)
            q.put(out.decode())

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

            print("path" + j["path"])
            print("o:" + j["original_size"])
            print("c:" + j["compressed_size"])
            print("d:" + j["deduplicated_size"])

        q.task_done()

    logging.info("Thread %s: finishing", name)

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

    logging.info("Main    : wait for the thread to finish")

    backupThread.join()

    logging.info("Main    : Backup Thread joined")

    publishThread.runThread = False

    publishThread.join()

    logging.info("Main    : Publish Thread joined")


    logging.info("Main    : all done")