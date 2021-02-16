import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path
from flask import Flask, Response, request

from borginterface import borgBackup

app = Flask(__name__)
app.config.from_object(__name__)

backups = dict()
backups['movies'] = dict()
backups['music'] = dict()
backups['pictures'] = dict()
backups['documents'] = dict()

backups['movies']['source'] = '/media/veracrypt1/movies'
backups['movies']['sink'] = '/media/veracrypt2/movies'
backups['music']['source'] = '/media/veracrypt1/music'
backups['music']['sink'] = '/media/veracrypt2/music'
backups['pictures']['source'] = '/media/veracrypt1/pictures'
backups['pictures']['sink'] = '/media/veracrypt2/pictures'
backups['documents']['source'] = '/media/veracrypt1/documents'
backups['documents']['sink'] = '/media/veracrypt2/documents'

backups = dict()

@app.route('/status/<tag>')
def getStatus(tag):
    return backups[tag]

@app.route('/setup/<tag>')
def setup(tag):
    if backup.get(tag) is not None:
        print('Backup tag already exists')
        return
    else:
        backups[tag] = dict()
    
    backups[tag]['thread'] = threading.Thread(target=runBackup, args=(1,))
    backups[tag]['thread'].runThread = True

    return backups[tag]

@app.route('/start/<tag>')
def start(tag):
    if backup.get(tag) is not None:
        backups[tag]['thread'].start()
        return "success"
    else:
        print('Tag does not exist. Call setup first')

@app.route('/kill')
def kill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."



if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"

    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Main    : before creating thread")

    # backupThread = threading.Thread(target=runBackup, args=(1,))
    # backupThread.runThread = True

    publishThread = threading.Thread(target=publish, args=(2,))
    publishThread.runThread = True


    logging.info("Main    : before running thread")

    publishThread.start()

    # backupThread.start()

    app.run(host='192.168.1.114', port=8020)

    logging.info("Main    : wait for the thread to finish")

    # backupThread.join()

    logging.info("Main    : Backup Thread joined")

    publishThread.runThread = False

    publishThread.join()

    logging.info("Main    : Publish Thread joined")


    logging.info("Main    : all done")