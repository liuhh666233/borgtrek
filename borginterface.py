import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path

class borgBackup(object):
        
    runBackupScript = "/home/stroblme/Documents/borgBackup.sh"
    # tag = '201221'
    # sink = '/media/veracrypt2/movies'
    # source = '/media/veracrypt1/movies'

    q = queue.Queue()
    repository = dict()
    
    def __init__(self, tag, sink, source):
        self.repository['tag'] = tag
        logging.info(f"Setting up instance with tag {tag}")

        self.repository['sink'] = sink
        logging.info(f"Setting up sink as {sink}")

        self.repository['source'] = source
        logging.info(f"Setting up source as {source}")

        self.countFiles()
        numOfFiles = self.repository['total']
        logging.info(f"Found {numOfFiles} files")


    def getInfo(self):
        return self.repository

    def countFiles(self):
        self.files = list(Path(self.repository['source']).rglob("*"))
        self.repository['total'] = len(self.files)

    def runBackup(self):
        self.backupThread = threading.Thread(target=runBackup, args=(1,))
        self.backupThread.runThread = True

        self.publishThread = threading.Thread(target=self.publishThread, args=(2,))
        self.publishThread.runThread = True

        self.publishThread.start()
        self.backupThread.start()


    def runBackupThread(self):
        t = threading.currentThread()

        logging.info(f"Starting Backup of {self.repository['source']} to {self.repository['sink']} with tag {self.repository['tag']}")

        listProcess = subprocess.Popen(['/usr/bin/borg', 'create', '--repository', '--stats', '--log-json', sink+'::'+tag, source], stderr=subprocess.PIPE)

        # listProcess = subprocess.Popen(['/usr/bin/borg', 'list', '--log-json', sink], stderr=subprocess.PIPE)
        listPoll = select.poll()
        listPoll.register(listProcess.stderr)

        out = -1
        while(out != b'' and getattr(t, "runThread", False)):
            rlist = listPoll.poll()
            for fd, event in rlist:
                out = os.read(fd, 1024)
                self.q.put(out.decode().replace('\n',''))

        logging.info("Thread %s: finishing", name)

    def publishThread(self, name):
        t = threading.currentThread()
        
        logging.info("Thread %s: starting", name)

        while(getattr(t, "runThread", False)):
            while(self.q.empty()):
                time.sleep(0.1)

            qPt = self.q.get()

            if qPt != "":
                j = json.loads(qPt)

                if "archive_repository" in j["type"]:
                    # print("path" + j["path"])
                    # print("o:" + str(j["original_size"]))
                    # print("c:" + str(j["compressed_size"]))
                    # print("d:" + str(j["deduplicated_size"]))
                    self.repository[tag]['processed'] = j["nfiles"]
                    # print(f"Processing {nfiles} of {len(files)}")

                elif "repository_message" in j["type"]:
                    logging.info("path" + str(j["time"]))

                else:
                    logging.info(j["message"])
                    

            self.q.task_done()

        logging.info("Thread %s: finishing", name)

