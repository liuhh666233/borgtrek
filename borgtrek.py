import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path
from flask import Flask, Response, request

from borginterface import borgBackup

app = Flask(__name__)
app.config.from_object(__name__)

folderList = dict()
folderList['source'] = dict()
folderList['sink'] = dict()

folderList['source']['movies'] = '/media/veracrypt1/movies'
folderList['sink']['movies'] = '/media/veracrypt2/movies'

backups = dict()

@app.route('/status/<tag>')
def getStatus(tag):
    return backups[tag]

@app.route('/start/<tag>')
def start(tag):
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

    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

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