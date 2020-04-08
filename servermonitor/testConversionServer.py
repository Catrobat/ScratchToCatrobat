import sys
sys.path.append(sys.path[0].replace("servermonitor","src"))
sys.path.append(sys.path[0].replace("servermonitor","web"))
print(sys.path)
import httplib
import json
import traceback
import os

import websocket
import zipfile
import logging

import scratchtocatrobat
from SmtpUtility import SmtpUtility

from scratchtocatrobat.tools.logger import setup_logging
from scratchtocatrobat.tools.logger import log
from scratchtocatrobat.tools.helpers import _setup_configuration
from ClientRetrieveInfoCommand import ClientRetrieveInfoCommand
from ClientAuthenticateCommand import ClientAuthenticateCommand
from ClientScheduleJobCommand import ClientScheduleJobCommand

configpath = "config/default.ini"
smtp = None

def main():
    setup_logging()
    _logger = logging.getLogger('websocket')
    _logger.addHandler(logging.NullHandler())
    config_params = readConfig()
    failure = False
    failure |= test_web_api(config_params.webapirul)
    failure |= test_conversion(config_params)
    if failure:
        mailcontent = "There was an error at converting. Log is:\n" +getlog()
        log.info(SmtpUtility.send(config_params.mailinfo, mailcontent))

class ConfigFileParams:
    class Mailinfo(object):
        smtp_host = None
        smtp_port = None
        smtp_from = None
        smtp_pwd = None
        smtp_send_to = None

        def to_json(self):
            return json.dumps(self, default=lambda o: o.__dict__,
                              sort_keys=True, indent=4)

    conversionurl = None
    clientid = None
    scractchprojectid = None
    webapirul = None
    code_xml_hash = None
    mailinfo = Mailinfo()


def readConfig():
    global configpath
    config = _setup_configuration(configpath)
    config_params = ConfigFileParams()
    config_params.webapirul = config.config_parser.get("Scratch2CatrobatConverter", "webapiurl")
    config_params.conversionurl = config.config_parser.get("Scratch2CatrobatConverter", "conversionurl")
    config_params.clientid = config.config_parser.getint("Scratch2CatrobatConverter", "clientid")
    config_params.scractchprojectid = config.config_parser.getint("Scratch2CatrobatConverter", "scratchprojectid")
    config_params.downloadurl = config.config_parser.get("Scratch2CatrobatConverter", "downloadurl")
    config_params.code_xml_hash = config.config_parser.getint("Scratch2CatrobatConverter", "code_xml_hash")

    config_params.mailinfo.smtp_host = config.config_parser.get("MAIL", "smtp_host")
    config_params.mailinfo.smtp_from = config.config_parser.get("MAIL", "smtp_from")
    config_params.mailinfo.smtp_port = config.config_parser.get("MAIL", "smtp_port")
    config_params.mailinfo.smtp_pwd = config.config_parser.get("MAIL", "smtp_pwd")
    config_params.mailinfo.smtp_send_to = config.config_parser.get("MAIL", "smtp_send_to")[1:-1].split(", ")
    return config_params


def getlog():
    file = open(scratchtocatrobat.tools.logger.log_file, "r")
    content = file.read()
    file.close()
    return content

#if scratch2catrobat site is shut down refactor this/remove it
def test_web_api(webapirul):
    conn = None
    failed = True
    try:
        conn = httplib.HTTPConnection(webapirul)
        conn.request("GET", "/")
        r1 = conn.getresponse()
        status = r1.status
        if status == 200:
            log.info("WebApi is up and running")
            failed = False
        else:
            log.error("WebApi Http status not OK, status is:" + str(status))
    except:
        log.error("Could not connect to WebApi:\n" + traceback.format_exc())
    try:
        conn.close()
    except AttributeError:
        log.error("Could not close websocket "+ traceback.format_exc())
    return failed


def test_conversion(config_params):
    def authenticate():
        command = ClientAuthenticateCommand(config_params)
        command.execute(ws)

    def start_conversion():
        command = ClientScheduleJobCommand(config_params)
        command.execute(ws)

    def retrieve_info():
        command = ClientRetrieveInfoCommand(config_params)
        return command.execute(ws)

    def download_project():
        conn = httplib.HTTPConnection(config_params.downloadurl)
        conn.request("GET", download_path)
        r1 = conn.getresponse()
        status = r1.status
        if status == 200:
            log.info("Download Project Http status OK: "+ config_params.downloadurl+download_path)
            return r1.read()
        else:
            log.error("Download Project Http status not OK, status is:" + str(status))

    def validate_ziped_project():
        failed = False
        if not os.path.isdir("tmp/"):
            os.makedirs("tmp/")
        file = open("tmp/project.zip","wb")
        file.write(ziped_project)
        file.close()
        myzip = zipfile.ZipFile("tmp/project.zip")
        xml_file_path = myzip.extract("code.xml","tmp/")

        def sortAndStripCodeXml(xml_file_path):
            import xml.etree.ElementTree as ET
            order = 0
            tagsToSort = ["formula", "entry"]

            def getUniqueId(child):
                id = ET.tostring(child)
                return id

            def sortchildrenby(parent, order):
                order += 1
                for child in parent:
                    order += 1
                    order = sortchildrenby(child, order)
                parent[:] = sorted(parent, key=lambda child: getUniqueId(child) if str(child.tag) in tagsToSort else order)
                return order

            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            #remove the build number and other version dependent attributes
            root.find("header").remove(root.find("header").find("applicationBuildNumber"))
            root.find("header").remove(root.find("header").find("applicationVersion"))
            root.find("header").remove(root.find("header").find("catrobatLanguageVersion"))
            root.find("header").remove(root.find("header").find("description"))

            sortchildrenby(root, order)
            result = ""
            for line in ET.tostring(root).split("\n"):
                result += line.strip()+"\n"
            return result

        xml = sortAndStripCodeXml(xml_file_path)
        hash_of_xml_file = hash(xml)
        if hash_of_xml_file == config_params.code_xml_hash:
            log.info("Project hash OK")
        else:
            log.error("Project hash unexpected, has: " + str(hash_of_xml_file)
                      + " but should be: " + str(config_params.code_xml_hash))
            failed = True
        os.remove("tmp/project.zip")
        os.remove("tmp/code.xml")
        return failed

    ws = None
    try:
        ws = websocket.create_connection(config_params.conversionurl)
        authenticate()
        start_conversion()
        result = retrieve_info()
        download_path = ClientRetrieveInfoCommand.get_download_url(result, config_params.scractchprojectid)
        ziped_project = download_project()
        failed = validate_ziped_project()
        #TODO idea: check without force flag if caching works

    except:
        log.error("Exception while Conversion: " + traceback.format_exc())
        failed = True
    try:
        ws.close()
    except AttributeError:
        log.error("Could not close websocket "+ traceback.format_exc())
    return failed


if __name__ == '__main__':
    main()
