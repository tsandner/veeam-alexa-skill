import logging
import requests
import xml.etree.ElementTree as elementtree
from flask import Flask
from flask_ask import Ask, statement, question, session
import datetime
import time
import unidecode

troubleshooting = False
if troubleshooting: print("Troubleshooting mode is on. Additional infos to will be printed into the console")

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Disable SSL warnings

app = Flask(__name__)
ask = Ask(app, "/")
#logging.getLogger('flask_ask').setLevel(logging.DEBUG)

@app.route('/')

def auth_veeamapi():
    # Login the first time. Afterwards only use auth_veeamapi() if session has expired.
    ########################################################################
    # veeamapiconfig.py
    import veeamapiconfig as cfg
    server = cfg.server
    port = cfg.port
    verifyssl = cfg.verifyssl
    admin = cfg.admin
    password = cfg.password
    ########################################################################
    idheader = "X-RestSvcSessionId"
    cookie = "Set-Cookie"
    #better in production to have verification and no self signed certificates
    if not verifyssl:
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    hrefapi = "https://{server}:{port}/api/".format(server=server,port=port)
    # Access the API
    response = requests.get(hrefapi,verify=verifyssl)

    # check if API is reachable by checking on the returned HTTP status code
    if response.status_code < 400:
        hreflogonlink = None
        hreflogout = None
        #we need to find the api link so we can authenticate
        #hreflogonlink should be under EnterpriseManager(root)>Links>Link with attibute type eq LogonSession
        #for more info check the login example https://helpcenter.veeam.com/docs/backup/rest/logging_on.html?ver=95

        xmlnamespace = "http://www.veeam.com/ent/v1.0"
        rawxml = response.text
        root = elementtree.fromstring(rawxml)
        #iter finds all link elements at any level
        #findall works only at the current level
        for links in root.findall("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="Links")):
            for link in links.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="Link")):
                if "Href" in link.attrib and "Type" in link.attrib and link.attrib["Type"] == "LogonSession":
                    hreflogonlink = link.attrib["Href"]

        if hreflogonlink != None:
            # Login Link found
            # perform login:
            #s = requests.Session()
            #response = s.post(hreflogonlink,auth=requests.auth.HTTPBasicAuth(admin, password),verify=verifyssl)
            response = requests.post(hreflogonlink,auth=requests.auth.HTTPBasicAuth(admin, password),verify=verifyssl)
            # ceck http status coode if login successful
            if response.status_code < 400 and idheader in response.headers :
                # find logout-link:
                root = elementtree.fromstring(response.text)
                for link in root.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="Link")):
                    if "Href" in link.attrib and "Rel" in link.attrib:
                        if link.attrib["Rel"] == "Delete":
                            hreflogout = link.attrib["Href"]
                # Session-ID Header is needed for any request against the API
                headers = {idheader: response.headers[idheader]}
                return(hrefapi,headers,verifyssl,xmlnamespace,hreflogout)
            else:
                print("Problem logging in - Status Code {}".format(response.status_code))
        else:
            print("Could not find API Login URL - Status Code {0} {1}".format(response.status_code,hreflogonlink))

    else:
        print("Problem reaching the API - Status Code {}".format(response.status_code))


def logout_veeamapi(hreflogout,headers,verifyssl):
    if hreflogout:
            print("Found logout link: {0}".format(hreflogout))
            response = requests.delete(hreflogout,headers=headers,verify=verifyssl)
            if response.status_code == 204:
                print("Succesfully logged out")
            else:
                print("Could not logout ({0})".format(response.status_code))
    else:
        print("Could not find logout link")

def bytes_2_human_readable(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! numberOfBytes can't be smaller than 0 !!!")

    step_to_greater_unit = 1024.

    number_of_bytes = float(number_of_bytes)
    unit = 'bytes'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'

    precision = 1
    number_of_bytes = round(number_of_bytes, precision)

    return str(number_of_bytes) + ' ' + unit

def overview():
    if troubleshooting: print("################# FUNCTION overview #############################################")
    apiurl, headers, verifyssl, xmlnamespace,hreflogout = auth_veeamapi()
    overviewlink = apiurl+"reports/summary/overview"
    if troubleshooting: print("API url: {}".format(overviewlink))
    resp = requests.get(overviewlink,headers=headers,verify=verifyssl)
    backupservers = 0
    proxyservers = 0
    repositoryservers = 0
    runningjobs = 0
    scheduledjobs = 0
    successfulvmlasteststates = 0
    warningvmlasteststates = 0
    failedvmlasteststates = 0

    if resp.status_code < 400:
        rawxml = resp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom:
            if '}' in x.tag:
                # strip all namespaces
                x.tag = x.tag.split('}', 1)[1]
                if x.tag == "BackupServers":
                    backupservers = int(x.text)
                    if troubleshooting: print("Backup Servers: {0}".format(backupservers))
                elif x.tag == "ProxyServers":
                    proxyservers = int(x.text)
                    if troubleshooting: print("Proxy Servers: {0}".format(proxyservers))
                elif x.tag == "RepositoryServers":
                    repositoryservers = int(x.text)
                    if troubleshooting: print("Repository Servers: {0}".format(repositoryservers))
                elif x.tag == "RunningJobs":
                    runningjobs = int(x.text)
                    if troubleshooting: print("Running jobs: {0}".format(runningjobs))
                elif x.tag == "ScheduledJobs":
                    scheduledjobs = int(x.text)
                    if troubleshooting: print("Scheduled Backup and Replication jobs: {0}".format(scheduledjobs))
                elif x.tag == "SuccessfulVmLastestStates":
                    successfulvmlasteststates = int(x.text)
                    if troubleshooting: print("Number of VMs with latest protection job successfull: {0}".format(successfulvmlasteststates))
                elif x.tag == "WarningVmLastestStates":
                    warningvmlasteststates = int(x.text)
                    if troubleshooting: print("Number of VMs with latest protection job warning: {0}".format(warningvmlasteststates))
                elif x.tag == "FailedVmLastestStates":
                    failedvmlasteststates = int(x.text)
                    if troubleshooting: print("Number of VMs with latest protection job failed: {0}".format(failedvmlasteststates))
    print("{} Info: Function overview just run".format(datetime.datetime.now().isoformat()))
    if troubleshooting: print("overview return values:\nbackupservers: {}\nproxyservers: {}\nrepositoryservers: {}\nrunningjobs: {}\nscheduledjobs: {}\nsuccessfulvmlasteststates: {}\nwarningvmlasteststates: {}\nfailedvmlasteststates ".format(backupservers,proxyservers,repositoryservers,runningjobs,scheduledjobs,successfulvmlasteststates,warningvmlasteststates,failedvmlasteststates))
    return(backupservers,proxyservers,repositoryservers,runningjobs,scheduledjobs,successfulvmlasteststates,warningvmlasteststates,failedvmlasteststates)

def runningjobs():
    if troubleshooting: print("################# FUNCTION runningjobs START #############################################")
    apiurl, headers, verifyssl, xmlnamespace, hreflogout = auth_veeamapi()
    backupjoblink = apiurl+'query?type=BackupJobSession&format=Entities&sortDesc=endtime&pageSize=999&page=1&filter=state==Working'
    if troubleshooting: print("API url: {}".format(backupjoblink))
    bresp = requests.get(backupjoblink,headers=headers,verify=verifyssl)
    bjcount = 0
    bcjcount = 0
    if bresp.status_code < 400:
        rawxml = bresp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="BackupJobSession")):
            if troubleshooting: print("--------------------------------------------------")
            if troubleshooting: print(x.get("Name"))
            for y in x:
                if '}' in y.tag:
                    y.tag = y.tag.split('}', 1)[1]  # strip all namespaces
                if y.tag == "JobType" and y.text =="BackupCopy":
                    bcjcount = bcjcount +1
                if y.tag == "JobType" and y.text =="Backup":
                    bjcount = bjcount +1

    replicalink = apiurl+'query?type=ReplicaJobSession&format=Entities&sortDesc=endtime&pageSize=999&page=1&filter=state==Working'
    if troubleshooting: print("API url: {}".format(replicalink))
    rresp = requests.get(replicalink,headers=headers,verify=verifyssl)
    rjcount = 0
    if rresp.status_code < 400:
        rawxml = rresp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="ReplicaJobSession")):
            if troubleshooting: print("--------------------------------------------------")
            if troubleshooting: print(x.get("Name"))
            for y in x:
                if '}' in y.tag:
                    y.tag = y.tag.split('}', 1)[1]  # strip all namespaces
                if y.tag == "JobType" and y.text =="Replica":
                    rjcount = rjcount +1
    if troubleshooting: print("\n\n")
    if troubleshooting: print("runningjobs return values:\nbjcount: {}\nbcjcount: {}\nrjcount: {}".format(bjcount,bcjcount,rjcount))
    print("{} Info: Function runningjobs just run".format(datetime.datetime.now().isoformat()))
    return bjcount,bcjcount,rjcount

def backupfiles():
    if troubleshooting: print("################# FUNCTION backupfiles START #############################################")
    apiurl, headers, verifyssl, xmlnamespace, hreflogout = auth_veeamapi()
    dt = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    utcdatetime=dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    onedayago=utcdatetime + "Z"

    overviewlink = apiurl+'query?type=BackupFile&format=Entities&sortDesc=CreationTimeUTC&pageSize=999&page=1&filter=creationtimeutc>"'+onedayago+'"'
    if troubleshooting: print("API url: {}".format(overviewlink))
    resp = requests.get(overviewlink,headers=headers,verify=verifyssl)
    filecount = 0
    backupsize = 0
    datasize = 0

    if resp.status_code < 400:
        rawxml = resp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="BackupFile")):
            if troubleshooting: print("-----------------------------------------------------------------------")
            if troubleshooting: print(x.get("Name"))
            filecount = filecount + 1
            for y in x:
                if '}' in y.tag:
                    y.tag = y.tag.split('}', 1)[1]  # strip all namespaces
                if y.tag == "BackupSize":
                    if troubleshooting: print("BackupSize: {}".format(y.text))
                    backupsize = backupsize + int(y.text)
                if y.tag == "DataSize":
                    datasize = datasize + int(y.text)

    if troubleshooting: print("\n\n")
    if troubleshooting: print("Sourcedata: {}".format(bytes_2_human_readable(datasize)))
    if troubleshooting: print("Backup files of the last 24h: {}".format(bytes_2_human_readable(backupsize)))
    if troubleshooting: print("Number of backup files: {}".format(filecount))
    print("{} Info: Function backupfiles just run".format(datetime.datetime.now().isoformat()))

    return filecount,backupsize,datasize

def jobsessions():
    if troubleshooting: print("################# FUNCTION jobsessions START #############################################")
    apiurl, headers, verifyssl, xmlnamespace, hreflogout = auth_veeamapi()
    dt = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    utcdatetime=dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    onedayago=utcdatetime + "Z"

    #overviewlink = apiurl+'query?type=BackupJobSession&format=Entities&sortDesc=name&pageSize=999&page=1&filter=jobtype==backup;result=='+jobstatus+';endtime>"'+onedayago+'"'
    overviewlink = apiurl+'query?type=BackupJobSession&format=Entities&sortDesc=endtime&pageSize=999&page=1&filter=jobtype==backup;endtime>"'+onedayago+'"'
    if troubleshooting: print("API url: {}".format(overviewlink))
    resp = requests.get(overviewlink,headers=headers,verify=verifyssl)

    successcount = 0
    warningcount = 0
    failedcount = 0
    if resp.status_code < 400:
        rawxml = resp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="BackupJobSession")):
            if troubleshooting: print("-----------------------------------------------------------------------")
            if troubleshooting: print(x.get("Name"))
            for y in x:
                if '}' in y.tag:
                    y.tag = y.tag.split('}', 1)[1]  # strip all namespaces
                if y.tag == "JobName":
                    if troubleshooting: print("JobName: {}".format(y.text))
                if y.tag == "JobType":
                    if troubleshooting: print("JobType: {}".format(y.text))
                if y.tag == "Result":
                    if troubleshooting: print("Result: {}".format(y.text))
                    if y.text == "Success":
                        successcount = successcount +1
                    if y.text == "Warning":
                        warningcount = warningcount +1
                    if y.text == "Failed":
                        failedcount = failedcount +1
                if y.tag == "IsRetry":
                    if troubleshooting: print("IsRetry: {}".format(y.text))

    if troubleshooting: print("\n\n")
    if troubleshooting: print("Job Sessions with status Success: {}".format(successcount))
    if troubleshooting: print("Job Sessions with status Warning: {}".format(warningcount))
    if troubleshooting: print("Job Sessions with status Failed: {}".format(failedcount))
    print("{} Info: Function jobsessions just run".format(datetime.datetime.now().isoformat()))

    return successcount,warningcount,failedcount

def repositoryinfo():
    if troubleshooting: print("################# FUNCTION repositoryinfo SART #############################################")
    numberofrepositories = 0
    repototalcap = 0
    repototalfree = 0
    totalbackup = 0
    apiurl, headers, verifyssl, xmlnamespace, hreflogout = auth_veeamapi()
    overviewlink = apiurl+"repositories?format=Entity"
    if troubleshooting: print("API url: {}".format(overviewlink))
    resp = requests.get(overviewlink,headers=headers,verify=verifyssl)
    if resp.status_code < 400:
        rawxml = resp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="Repository")):
            if troubleshooting: print("-----------------------------------------------------------------------")
            numberofrepositories=numberofrepositories+1
            if troubleshooting: print(x.get("Name"))
            for y in x:
                if '}' in y.tag:
                    y.tag = y.tag.split('}', 1)[1]  # strip all namespaces
                if y.tag == "Capacity":
                    if y.text != "-1":
                        repototalcap = repototalcap + int(y.text)
                        if troubleshooting: print('Capacity: {}'.format(bytes_2_human_readable(int(y.text))))
                elif y.tag == "FreeSpace":
                    repototalfree = repototalfree + int(y.text)
    totalbackup = repototalcap - repototalfree
    if troubleshooting: print("\n\n\n")
    if troubleshooting: print("numberofrepositories: {}\nrepototalcap: {}\nrepototalfree: {}\ntotalbackup: {}\n".format(numberofrepositories,repototalcap,repototalfree,totalbackup))
    print("{} Info: Function repositoryinfo just run".format(datetime.datetime.now().isoformat()))
    return numberofrepositories,repototalcap,repototalfree,totalbackup

def listjobs():
    if troubleshooting: print("################# FUNCTION listjobs START #############################################")
    backupjoblist = []
    replicationjoblist = []
    backupcopyjoblist = []
    apiurl, headers, verifyssl, xmlnamespace, hreflogout = auth_veeamapi()
    #overviewlink = apiurl+"jobs?format=Entity"
    overviewlink = apiurl+'query?type=Job&format=Entities&sortDesc=name&pageSize=150&page=1&filter=Platform==Vmware,Platform==HyperV,Platform==vCloud'
    if troubleshooting: print("API url: {}".format(overviewlink))
    #filter=Platform==Vmware,Platform==HyperV,Platform==vCloud
    resp = requests.get(overviewlink,headers=headers,verify=verifyssl)
    if resp.status_code < 400:
        rawxml = resp.text
        dom = elementtree.fromstring(rawxml)
        for x in dom.iter("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="Job")):
            if troubleshooting: print("Job: {0:30} {1:10}".format(x.get("Name"),x.get("UID")))
            if x.findtext("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="JobType")) == "Backup":
                backupjoblist.append(x.get("Name"))
            if x.findtext("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="JobType")) == "Replica":
                replicationjoblist.append(x.get("Name"))
            if x.findtext("{{{ns}}}{tag}".format(ns=xmlnamespace,tag="JobType")) == "BackupCopy":
                backupcopyjoblist.append(x.get("Name"))

    if troubleshooting: print("\n\n")
    if troubleshooting: print("backupjoblist: {}\nreplicationjoblist: {}\nbackupcopyjoblist".format(backupjoblist, replicationjoblist,backupcopyjoblist))
    print("{} Info: Function listjobs just run".format(datetime.datetime.now().isoformat()))
    return backupjoblist, replicationjoblist,backupcopyjoblist

@ask.launch
def start_skill():
        welcome_message = 'Welcome to this Veeam demo Skill. You can ask me for an overview, job status, repository information, backup filesize, and running jobs'
        return question(welcome_message)

@ask.intent("Overview")
def share_overview():
        backupservers,proxyservers,repositoryservers,runningjobs,scheduledjobs,successfulvmlasteststates,warningvmlasteststates,failedvmlasteststates = overview()

        if backupservers == 0:
            msg = 'There are {0} Veeam backup and replication servers, '.format(backupservers)
        elif backupservers == 1:
            msg = 'There is {0} Veeam backup and replication server, '.format(backupservers)
        else:
            msg = 'There are {0} Veeam backup and replication servers, '.format(backupservers)


        if proxyservers == 1:
            msg = msg + ' {} proxy '.format(proxyservers)
        else:
            msg = msg + ' {} proxies '.format(proxyservers)

        #if repositoryservers == 1:
        #    msg = msg + 'and {} repository in your environment. '.format(repositoryservers)
        #else:
        #    msg = msg + 'and {} repositories in your environment. '.format(repositoryservers)

        if runningjobs == 1:
            msg = msg + 'There is {} backup and replication job running. '.format(runningjobs)
        else:
            msg = msg + 'There are {} backup and replication jobs running. '.format(runningjobs)

        if successfulvmlasteststates == 1:
            msg = msg + '{} virtual machine has been protected successfully recently. '.format(successfulvmlasteststates)
        else:
            msg = msg + '{} virtual machines have been protected successfully recently. '.format(successfulvmlasteststates)

        if warningvmlasteststates == 1:
            msg = msg + '{} virtual machine finished with a warning. '.format(warningvmlasteststates)
        else:
            msg = msg + '{} virtual machines finished with a warning. '.format(warningvmlasteststates)

        if failedvmlasteststates == 1:
            msg = msg + '{} virtual machine finished with an error. '.format(failedvmlasteststates)
        else:
            msg = msg + '{} virtual machines finished with an error. '.format(failedvmlasteststates)

        cardtitle = "Veeam Overview"
        cardtext = "Veeam servers: {}\nProxy servers: {}\nRunning jobs: {}\nLatest VM status:\nSuccessful: {}\nWarning: {}\nError: {}"\
                   .format(backupservers,proxyservers,runningjobs,successfulvmlasteststates,warningvmlasteststates,failedvmlasteststates)
        return statement(msg).simple_card(title=cardtitle, content=cardtext)

@ask.intent("RunningJobs")
def share_runningjobs():
        bjcount,bcjcount,rjcount = runningjobs()
        msg = "Running Backup Jobs {}, running backup copy jobs: {}, running replication jobs: {}".format(bjcount,bcjcount,rjcount)
        cardtitle = 'Running Backup Jobs'
        cardtxt = "Running Backup Jobs {}\nRunning Backup Copy Jobs: {}\nRunning Replication Jobs: {}".format(bjcount,bcjcount,rjcount)
        return statement(msg).simple_card(title=cardtitle, content=cardtxt)

@ask.intent("Jobstatus")
def share_jobstatus():
        successcount,warningcount,failedcount = jobsessions()
        msg = "Backup job session status for the last 24 hours: Successful: {}, With Warnings: {}, failed: {}.".format(successcount,warningcount,failedcount)
        cardtitle = 'Backup Job Sessions Last 24h'
        cardtxt = "Success: {}\nWarning: {}\nFailed: {}".format(successcount,warningcount,failedcount)
        return statement(msg).simple_card(title=cardtitle, content=cardtxt)

@ask.intent("Repositoryinfo")
def share_repositoryinfo():
        numberofrepositories,repototalcap,repototalfree,totalbackup = repositoryinfo()
        cardtitle = 'Repository info'
        cardtext = 'Number of repositories: {}\nTotal capacity: {}\nFree space: {}'.format(numberofrepositories,bytes_2_human_readable(repototalcap),bytes_2_human_readable(repototalfree))
        msg = "There are {0} repositories with a total capacity of {1}. Backups are occupying {2} resulting in {3} of free space.".format(numberofrepositories,bytes_2_human_readable(repototalcap),bytes_2_human_readable(totalbackup),bytes_2_human_readable(repototalfree))
        return statement(msg).simple_card(title=cardtitle, content=cardtext)

@ask.intent("RepositoryFreeSpace")
def freespace():
        numberofrepositories,repototalcap,repototalfree,totalbackup = repositoryinfo()
        cardtitle = 'Free space'
        cardtext = 'Number of repositories: {}\nTotal capacity: {}\nFree space: {}'.format(numberofrepositories,bytes_2_human_readable(repototalcap),bytes_2_human_readable(repototalfree))
        msg = "Your {} repositories have a accumulated free space of {}.".format(numberofrepositories,bytes_2_human_readable(repototalfree))
        return statement(msg).simple_card(title=cardtitle, content=cardtext)

@ask.intent("Backupfilesize")
def backupfilesize():
        filecount,backupsize,datasize = backupfiles()
        cardtitle = "Buckups written in last 24h"
        cardtext = 'Backupfiles: {}\nBackupsize: {}'.format(filecount,bytes_2_human_readable(backupsize))
        msg = "{} backup files have been written to disk within the last 24 hours with a total capacity of {}.".format(filecount,bytes_2_human_readable(backupsize))
        return statement(msg).simple_card(title=cardtitle, content=cardtext)

@ask.intent("JobOverview")
def job_overview():
    backupjoblist,replicationjoblist,backupcopyjoblist = listjobs()
    #bj = ''.join(backupjoblist)
    #rj = ''.join(replicationjoblist)
    bj = len(backupjoblist)
    rj = len(replicationjoblist)
    bcj = len(backupcopyjoblist)
    cardtitle = 'Backup and replication jobs'
    cardtext = "Backup Jobs: {}\nBackup Copy Jobs: {}\nReplication Jobs: {}".format(str(bj),str(bcj),str(rj))
    return statement("There are " + str(bj) +" backup jobs, " + str(bcj) + " Backup copy jobs and " + str(rj) + " replication jobs.").simple_card(title=cardtitle, content=cardtext)

'''@ask.intent("ListBackupJobs", default={'numberbackupjobs':10})
def share_backup_jobs(numberbackupjobs):
    backupjoblist, replicationjoblist,backupcopyjoblist = listjobs()
    count = int(numberbackupjobs)
    #print(numbertoread)
    jobcount=len(backupjoblist)
    cardtitle = "Backup Jobs"
    cardtext = "Number of backup jobs: {}\n".format(jobcount)+",\n".join(str(i) for i in backupjoblist[0:count])
    print(cardtext)
    return question("There are {} backup jobs: {}".format(len(backupjoblist),", ".join(str(i) for i in backupjoblist[0:count]))).simple_card(title=cardtitle, content=cardtext)
    #return question("These are the names of the first {} backup jobs: {}".format(numberbackupjobs,", ".join(str(i) for i in backupjoblist[0:count])))

@ask.intent("ListReplicationJobs", default={'numberreplicationjobs':10})
def share_replication_jobs(numberreplicationjobs):
    backupjoblist, replicationjoblist,backupcopyjoblist = listjobs()
    count = int(numberreplicationjobs)
    jobcount=len(replicationjoblist)
    cardtitle = "Replication Jobs"
    cardtext = "Number of replication jobs: {}\n".format(jobcount)+",\n".join(str(i) for i in backupjoblist[0:count])
    return question("There are {} replication jobs: {}".format(len(replicationjoblist),", ".join(str(i) for i in replicationjoblist[0:count]))).simple_card(title=cardtitle, content=cardtext)
    #return question("These are the names of the first {} backup jobs: {}".format(numberbackupjobs,", ".join(str(i) for i in backupjoblist[0:count])))
'''

@ask.intent("NoIntent")
def no_intent():
        bye_text = 'I am not sure why you started this skill at all...bye'
        return statement(bye_text)

@ask.intent("AMAZON.StopIntent")
def stop():
    return statement("Goodd Bye")

if __name__ == '__main__':
       app.run(debug=True)
