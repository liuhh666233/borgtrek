import os, sys, select, subprocess, logging, threading, time
import queue
import json
from pathlib import Path
from flask import Flask, Response, request

from borginterface import borgBackup, borgHelper

app = Flask(__name__)
app.config.from_object(__name__)

backups = dict()
backups['movies'] = dict()
backups['music'] = dict()
# backups['pictures'] = dict()
backups['documents'] = dict()

backups['movies']['source'] = '/media/veracrypt1/movies'
backups['movies']['sink'] = '/media/veracrypt2/movies'
backups['music']['source'] = '/media/veracrypt1/music'
backups['music']['sink'] = '/media/veracrypt2/music'
# backups['pictures']['source'] = '/media/veracrypt1/pictures'
# backups['pictures']['sink'] = '/media/veracrypt2/pictures'
backups['documents']['source'] = '/media/veracrypt1/documents'
backups['documents']['sink'] = '/media/veracrypt2/documents'

def findTags():
    for media, mediaDict in backups.items():
        findTagsHelper = borgHelper(mediaDict['sink'])
        findTagsHelperThread = findTagsHelper.listTags()
        findTagsHelperThread.join()

        while(not findTagsHelper.q.empty()):
            tag = findTagsHelper.q.get()
            if backups[media].get(tag) is not None:
                continue

            logging.info(f"Found tag {tag} in {media}")

            backups[media][tag] = borgBackup(tag, backups[media]['sink'], backups[media]['source'], True)
            # findTagsHelper.q.task_done()

        
@app.route('/list')
def list():
    tagDict = dict()

    for media, mediaDict in backups.items():
        tagDict[media] = dict()
        for tagName, _ in mediaDict.items():
            tagDict[media][tagName] = tagName

    return tagDict

@app.route('/status/<media>/<tag>')
def getStatus(media,tag):
    if backups.get(media) is not None:
        if backups[media].get(tag) is not None:
            if backups[media][tag] is not None:
                logging.info(f"Tag exists, returning info")

                return backups[media][tag].getInfo()
            else:
                return "This tag has no running backup"
        else:
            return "This tag does not exist"
    else:
        return "This media does not exist"

@app.route('/setup/<media>/<tag>')
def setup(media,tag):
    if backups.get(media) is not None:
        if backups[media].get(tag) is not None:
            logging.info(f"Tag exists, counting files...")

            backups[media][tag].countFiles()
            return backups[media][tag].getInfo()
        else:
            logging.info(f"Tag does not exists, setting up borg instance")

            backups[media][tag] = borgBackup(tag, backups[media]['sink'], backups[media]['source'])
            return backups[media][tag].getInfo()
    else:
        return "This media does not exist"
    
@app.route('/start/<tag>')
def start(tag):
    if backups.get(tag) is not None:
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


    # backupThread.start()
    findTags()

    app.run(host='192.168.1.114', port=8020)

