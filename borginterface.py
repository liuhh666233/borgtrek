import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path
import re

class borgHelper(object):
    q = queue.Queue()
    repository = dict()
    
    def __init__(self, sink):
        self.repository['sink'] = sink
        logging.info(f"Setting up sink as {sink}")

    def listTags(self):
        listTagsThreadInst = threading.Thread(target=self.listTagsThread)
        listTagsThreadInst.runThread = True
        listTagsThreadInst.start()

        return listTagsThreadInst

    def listTagsThread(self):
        t = threading.currentThread()

        logging.info(f"Listing Tags of {self.repository['sink']}")

        output = subprocess.check_output(['/usr/bin/borg', 'list', '--log-json', self.repository['sink']], stderr=subprocess.PIPE)

        outputList = output.decode().split('\n')

        for item in outputList:
            if item == '':
                continue
            x = re.search(r"(?P<tag>\d*)", item)
            tag = x.group('tag')
            self.q.put(tag)


class borgBackup(object):
        
    runBackupScript = "/home/stroblme/Documents/borgBackup.sh"
    # tag = '201221'
    # sink = '/media/veracrypt2/movies'
    # source = '/media/veracrypt1/movies'
    
    
    def __init__(self, tag, sink, source, skipCount = False):
        self.backupThread = threading.Thread(target=self.runBackupThread)
        self.publishThread = threading.Thread(target=self.publishThread)

        self.backupRunning = False

        self.q = queue.Queue()
        
        self.repository = dict()
        
        self.repository['tag'] = tag
        logging.info(f"Setting up instance with tag {tag}")

        self.repository['sink'] = sink
        logging.info(f"Setting up sink as {sink}")

        self.repository['source'] = source
        logging.info(f"Setting up source as {source}")

        if not skipCount:
            self.countFiles()
            numOfFiles = self.repository['total']
            logging.info(f"Found {numOfFiles} files")

        self.repository['processed'] = 0


    def getInfo(self):
        return self.repository

    def countFiles(self):
        self.files = list(Path(self.repository['source']).rglob("*.*"))
        self.repository['total'] = len(self.files)

    def runBackup(self):
        self.countFiles()
        
        self.backupThread.runThread = True
        self.publishThread.runThread = True

        self.publishThread.start()

        self.backupThread.start()

    def awaitFinishBackupThread(self):
        if self.backupRunning:
            self.backupThread.join()
            self.publishThread.runThread = False

            self.publishThread.join()

            logging.info(f"Finished Backup of {self.repository['source']} to {self.repository['sink']} with tag {self.repository['tag']}")

        else:
            self.publishThread.runThread = False

            logging.info(f"Finished Backup of {self.repository['source']} to {self.repository['sink']} with tag {self.repository['tag']}")

    def runBackupThread(self):
        t = threading.currentThread()

        self.backupRunning = True

        logging.info(f"Starting Backup of {self.repository['source']} to {self.repository['sink']} with tag {self.repository['tag']}")

        cmd = ['/usr/bin/borg', 'create', '--progress', '--stats', '--log-json', self.repository['sink']+'::'+self.repository['tag'], self.repository['source']]
        listProcess = subprocess.Popen(cmd, stderr=subprocess.PIPE)

        # listProcess = subprocess.Popen(['/usr/bin/borg', 'list', '--log-json', sink], stderr=subprocess.PIPE)
        listPoll = select.poll()
        listPoll.register(listProcess.stderr)

        out = -1
        while(out != b'' and getattr(t, "runThread", False)):
            rlist = listPoll.poll()
            for fd, event in rlist:
                out = os.read(fd, 1024)
                self.q.put(out.decode().replace('\n',''))

        self.backupRunning = False

    def publishThread(self):
        t = threading.currentThread()
        

        while(getattr(t, "runThread", False)):
            while(self.q.empty()):
                time.sleep(0.1)

            qPt = self.q.get()

            if qPt != "":
                try:
                    j = json.loads(qPt)
                except(Exception):
                    logging.info(qPt)
                    self.q.task_done()
                    continue

                if "archive_progress" in j["type"]:
                    # print("path" + j["path"])
                    # print("o:" + str(j["original_size"]))
                    # print("c:" + str(j["compressed_size"]))
                    # print("d:" + str(j["deduplicated_size"]))
                    self.repository['processed'] = j["nfiles"]
                    # print(f"Processing {nfiles} of {len(files)}")

                elif "repository_message" in j["type"]:
                    logging.info("path" + str(j["time"]))
                    
                elif "progress_message" in j["type"]:
                    logging.info(j["finished"])

                elif "progress_percent" in j["type"]:
                    logging.info(j["finished"])

                elif "log_message" in j["type"]:
                    logging.info(j["message"])


                else:
                    logging.info(j["type"])
                    

            self.q.task_done()


