# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@kyndryl>
#                                   <lucianobaez1@ibm.com>
#                                   <lucianobaez@outlook.com>
#
# Latest version at https://github.kyndryl.net/lucianobaez
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/sudoers file
#
# History
# History
#   -Ver 0.1 : Aug 14 2020
#           - Implement the report option gets the sudo configuration as a dictionary.
#           - Allow to Add/removes include files into /etc/sudoers file
#           - Allow to remove the non compliance #includedir directive and replaces it with individulas inlcudes for each file under /etc/sudoers.d
#           - Perform any actions as a "transaction", and only aplies if the result of "visudo -c" is ok
#   -Ver 0.2 : Aug 21 2020
#           - Added the directive includepresent, that prevents an error messaje if the #include line (on /etc/sudoers) is already there
#           - Added the directive includeabsent, that prevents an error messaje if the #include line (on /etc/sudoers) is not there
#           - Added the directive includepresentfirst its the same as includepresent but guarantee that will be the first #include line at /etc/sudoers file

#   -Ver 0.3 : Sep 4 2020
#           - Add diferent way to call the module, as a declarative instead of imperative.
#               To use it, in order to guarantee back compatibility you need to use "action=state", as a state declaration. Then you could use it in the ne way.
#           - Add the declarive action to get a sepcific user or group in a specifica User alias in an specific include file or without specifying the file (is slower but checks all the files)

#   -Ver 0.4 : Sep 24 2020
#           - Fixing some conditions when you set a user or group without specifiyng the 

#   -Ver 0.5 : Oct 27 2020
#           - Fixing full path issue for sudo and visudo
#           - Adding a way to log for debug

#   -Ver 0.5 : Oct 27 2020
#           - Fixing full path issue for sudo and visudo
#           - Adding a way to log for debug

#   -Ver 0.6 : Nov 4 2020
#           - Handling NOPASSWD 

#   -Ver 0.7 : Nov 4 2020
#           - Creating a Lib file 

#   -Ver 0.8 : May 10 2021
#           - Recode the Ansible module
#


import os
import pwd
import grp
import platform
import subprocess
import json
import shutil
import datetime

def logtofile(filename,logline):
    # open a file to append
    f = open(filename, "a")
    f.write(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+' : '+logline)
    f.write("\n")
    f.close()


def catfile(filename):
    f = open(filename, "r")
    text = f.read()
    print(text)
    f.close()
def gettimestampstring():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")

def execute(cmdtoexecute,sudologdic):
    #executable=" su - db2inst1 -c \""+cmdtoexecute+"\""
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (execute)')
    ##stdoutstr=str(stdout, "utf-8")
    stdoutstr = stdout.decode('utf-8')
    #stdoutstr=str(stdout)
    
    #(str(hexlify(b"\x13\x37"), "utf-8"))
    #print (stdoutstr)
    return stdoutstr
    #return stdout

def executefull(cmdtoexecute,sudologdic):
    executeresult={'stdout':'','stderr':'','rc':''}
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    executeresult['stdout']=stdout
    executeresult['stderr']=stderr
    executeresult['rc']=rc
    if sudologdic['log']==True:
        #logtofile(sudologdic['logfile'],'Excecute out '+stdout+' ')
        #logtofile(sudologdic['logfile'],'Excecute err '+stderr+' ')
        logtofile(sudologdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (executefull')
    return executeresult

def executeas(cmdtoexecute,userexe,sudologdic):
    executable=" su - "+userexe.strip()+" -c \""+cmdtoexecute.strip().replace("\"","\\\"")+"\""
    if (userexe.strip() == "root"):
        # if user is "root" will remove the "su -" (swich user)
        executable=cmdtoexecute.strip()
    else:
        try:
            pwd.getpwnam(userexe.strip())
        except KeyError:
            # if user "userexe" doesen't exists will run as root
            executable=cmdtoexecute.strip()
    #executable=cmdtoexecute
    stdout=""
    #print(executable)
    #print(cmdtoexecute.strip())
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Excecute cmd '+cmdtoexecute+' by '+userexe+'  rc:'+str(rc)+' (executeas')
    return stdout


def getuserlist():
    resultlist=[]
    usersfile="/etc/passwd"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist

def getgrouplist():
    resultlist=[]
    usersfile="/etc/group"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist

def getuserlistfromgroup(providedgroup):
    userlist=[]
    result=[]
    groupname=providedgroup.replace('%','')
    groups = grp.getgrall()
    groupid=0
    exists=False
    for group in groups:
        #print(group)
        if group[0]==groupname:
            groupid=group[2]
            exists=True
            for user in group[3]:
                userlist.append(user)
    if exists==True:
        users = pwd.getpwall()
        for user in users:
            if user[3]==groupid:            
                userlist.append(user[0])
    # remove dupleicates
    result = list(dict.fromkeys(userlist))
    return result

def getsudocheck(sudologdic):
    sudocheck={'visudo': '','rc': 0}
    command='/usr/sbin/visudo'
    if os.path.isfile(command):
        fullcommand=command+' -c'
        visudoc=executefull(fullcommand,sudologdic)
        sudocheck['visudo']=visudoc['stdout']
        sudocheck['rc']=visudoc['rc']
    else:
        sudocheck['rc']=127
    return sudocheck

def getsudoversion(sudologdic):
    sudoinfo= {'version': '','policyplugin': '','grammarversion': '','sudoerspath': '','sudoersincludespath': '', 'iopluginversion': ''}
    SUDOVERSION=execute("/usr/bin/sudo -V",sudologdic)
    #print(SUDOVERSION)
    #AUX=SUDOVERSION[1].strip().split("\n")
    #print(SUDOVERSION)
    AUX=str(SUDOVERSION).strip().split("\n")
    AUXVERSION=''
    AUXPOLICY=''
    AUXFILEGRAMMAR=''
    AUXPATH=''
    AUXIOPLUGIN=''
    if len(AUX)>0:
        for AUXITEM in AUX:
            #print(AUXITEM )
            AUXWORDS=AUXITEM.strip().split()
            AUXFIRSTWORD=""
            AUXSECONDWORD=""
            AUXTHIRDWORD=""
            if len(AUXWORDS)>0:
                AUXFIRSTWORD=AUXWORDS[0]
            if len(AUXWORDS)>1:
                AUXSECONDWORD=AUXWORDS[1]
            if len(AUXWORDS)>2:
                AUXTHIRDWORD=AUXWORDS[2]
            #print(AUXFIRSTWORD.upper()+' '+AUXSECONDWORD.upper())
            if (AUXFIRSTWORD.upper()=='SUDO' and AUXSECONDWORD.upper()=='VERSION'):
                AUXVERSION=AUXITEM
            #spanish
            if (AUXFIRSTWORD.upper()=='SUDO' and AUXSECONDWORD.upper()=='VERSIÓN'):
                AUXVERSION=AUXITEM
            if (AUXFIRSTWORD.upper()=='SUDOERS' and AUXSECONDWORD.upper()=='POLICY' and AUXTHIRDWORD.upper()=='PLUGIN'):
                AUXPOLICY=AUXITEM
            if (AUXFIRSTWORD.upper()=='SUDOERS' and AUXSECONDWORD.upper()=='FILE' and AUXTHIRDWORD.upper()=='GRAMMAR'):
                AUXFILEGRAMMAR=AUXITEM
            if (AUXFIRSTWORD.upper()=='SUDOERS' and AUXSECONDWORD.upper()=='PATH:'):
                AUXPATH=AUXITEM
                AUXPATH=AUXTHIRDWORD
            if (AUXFIRSTWORD.upper()=='SUDOERS' and AUXSECONDWORD.upper()=='I/O' and AUXTHIRDWORD.upper()=='PLUGIN'):
                AUXIOPLUGIN=AUXITEM 
            #print(AUXFIRSTWORD+" "+AUXSECONDWORD.upper())
    sudoinfo['version']=AUXVERSION
    sudoinfo['policyplugin']=AUXPOLICY
    sudoinfo['grammarversion']=AUXFILEGRAMMAR
    sudoinfo['sudoerspath']=AUXPATH
    sudoinfo['sudoersincludespath']='/etc/sudoers.d'
    sudoinfo['iopluginversion']=AUXIOPLUGIN
    return sudoinfo

def getsudoerstemplatespath():
    AUXSUDOERSPATH=''
    if os.path.isdir('/etc/sudoers.d'):
        AUXSUDOERSPATH='/etc/sudoers.d'
    return AUXSUDOERSPATH

def getsudoersincludes(sudologdic):
    SUDOERSFILE='/etc/sudoers'
    AUXINCLUDES={'includefiles':0,'includedir': 0,'includelist': [],'includedirlist': []}
    COUNTINCLUDE=0
    COUNTINCLUDEDIR=0
    INCLUDELIST=[]
    INCLUDEDIRLIST=[]
    if os.path.isfile(SUDOERSFILE):
        #Porcess /etc/sudoers file for includes
        with open(SUDOERSFILE,"r") as sudofilehandler:
            sudoline = sudofilehandler.readline().replace('\t', ' ')
            ln=0
            stopprocess=0
            while sudoline:
                ln=ln+1
                firstword=""
                auxline=sudoline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (firstword != ""):
                    if (firstword == "#INCLUDE"):
                        COUNTINCLUDE=COUNTINCLUDE+1
                        if (len(auxline)>1):
                            INCLUDELIST.append(auxline[1])
                            if sudologdic['log']==True:
                                logtofile(sudologdic['logfile'],'Analyzing #include '+auxline[1]+' ')

                    if (firstword == "#INCLUDEDIR"):
                        COUNTINCLUDEDIR=COUNTINCLUDEDIR+1
                        if (len(auxline)>1):
                            INCLUDEDIRLIST.append(auxline[1])
                            if sudologdic['log']==True:
                                logtofile(sudologdic['logfile'],'Analyzing #includedir '+auxline[1]+' ')
            
                sudoline = sudofilehandler.readline().replace('\t', ' ')
            sudofilehandler.close
    AUXINCLUDES['includefiles']=COUNTINCLUDE
    AUXINCLUDES['includedir']=COUNTINCLUDEDIR
    AUXINCLUDES['includelist']=INCLUDELIST
    AUXINCLUDES['includedirlist']=INCLUDEDIRLIST
    return AUXINCLUDES

def processsudofile(sudoalias,sudofile):
    LABELDIC={}
    if os.path.isfile(sudofile):
        #Porcess /etc/sudoers file for includes
        with open(sudofile,"r", errors='replace') as sudofilehandler:
            sudoline = sudofilehandler.readline().replace('\t', ' ')
            ln=0
            stopprocess=0
            morecontent=0
            PREVIOUSLABEL=""
            CURRENTLABEL=""
            DEFAULTSNUMBER=1
            while sudoline:
                #print("Linea: "+sudoline)
                ln=ln+1
                labelfind=0
                firstword=""
                auxline=sudoline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (len(auxline)>1):
                    secondword=auxline[1]
                #print("> "+firstword)
                if (firstword != ""):
                    firstwordeight=""
                    if (len(firstword)>8):
                        firstwordeight=firstword[:8]
                        #print("eight: "+firstwordeight)
                    if (firstword == sudoalias.upper() or firstwordeight == sudoalias.upper()):
                        labelfind=1
                        if (len(auxline)>1):
                            AUXLABELS=secondword.split("=")
                            PREVIOUSLABEL=CURRENTLABEL
                            CURRENTLABEL=AUXLABELS[0]
                            CONTENTS=sudoline.replace('\n', '').strip().split('=')
                            if ((sudoalias=='User_Alias' or sudoalias=='Cmnd_Alias' or sudoalias=='Cmnd_Alias') and len(CONTENTS)>1 ):
                                LABELDIC[CURRENTLABEL]=CONTENTS[1]
                            if (firstword=='DEFAULTS' or firstwordeight=='DEFAULTS'):
                                CURRENTLABEL='Defaults'
                                if sudofile in LABELDIC.keys(): 
                                    LABELDIC[sudofile]=LABELDIC[sudofile]+'\n'+sudoline.replace('\n', '')
                                else:
                                    LABELDIC[sudofile]=sudoline.replace('\n', '')
                                DEFAULTSNUMBER=DEFAULTSNUMBER+1
                                #print('Defaults: '+sudoline.replace('\n', ''))
                            if (sudoline.replace('\n', '').strip()[-1]=="\\"):
                                morecontent=1
                            else:
                                morecontent=0
                    else:
                        # Process non recognized first word
                        if (morecontent==1):
                            
                            try:
                                LABELDIC[CURRENTLABEL]=LABELDIC[CURRENTLABEL]+sudoline.replace('\n', '').strip()
                            except KeyError:
                                LABELDIC[CURRENTLABEL]=sudoline.replace('\n', '').strip()
                            
                            if (sudoline.replace('\n', '').strip()[-1]=="\\"):
                                morecontent=1
                            else:
                                morecontent=0
                sudoline = sudofilehandler.readline().replace('\t', ' ')
            sudofilehandler.close
    return LABELDIC


def processsudofileassign(useralias,sudofile):
    LABELDIC={}
    DATADIC={'Host_Alias':'','assigns':'','file':''}
    #print('user:'+useralias+" file:"+sudofile)
    if os.path.isfile(sudofile):
        #Porcess /etc/sudoers file for includes
        with open(sudofile,"r", errors='replace') as sudofilehandler:
            sudoline = sudofilehandler.readline().replace('\t', ' ').replace(', ', ',')
            ln=0
            stopprocess=0
            morecontent=0
            PREVIOUSLABEL=""
            CURRENTLABEL=""
            DEFAULTSNUMBER=1
            while sudoline:
                #print("Linea: "+sudoline)
                ln=ln+1
                labelfind=0
                firstword=""
                auxline=sudoline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (len(auxline)>1):
                    secondword=auxline[1]
                #print("> "+firstword)
                if (firstword != ""):
                    firstwordlist=firstword.upper().split(',')
                    #if firstword == useralias.upper() :
                    if useralias.upper() in firstwordlist:
                        labelfind=1
                        if (len(auxline)>1):
                            AUXLABELS=secondword.split("=")
                            PREVIOUSLABEL=CURRENTLABEL
                            #CURRENTLABEL=auxline[0]
                            CURRENTLABEL=useralias
                            CONTENTS=sudoline.replace('\n', '').strip().split('=')
                            if ( len(CONTENTS)>1 ):                                
                                AUXIDS=CONTENTS[0].split()
                                if len(AUXIDS)>1:
                                    DATADIC['Host_Alias']=AUXIDS[1]
                                DATADIC['assigns']=CONTENTS[1]
                                DATADIC['file']=sudofile
                                LABELDIC[CURRENTLABEL]=DATADIC
                                
                            if (sudoline.replace('\n', '').strip()[-1]=="\\"):
                                morecontent=1
                            else:
                                morecontent=0
                    else:
                        # Process non recognized first word
                        if (morecontent==1):
                            
                            try:
                                DATADIC['assigns']=DATADIC['assigns']+sudoline.replace('\n', '').strip()
                                #LABELDIC[CURRENTLABEL]=LABELDIC[CURRENTLABEL]+sudoline.replace('\n', '').strip()
                            except KeyError:
                                DATADIC['assigns']=sudoline.replace('\n', '').strip()
                                #LABELDIC[CURRENTLABEL]=sudoline.replace('\n', '').strip()
                            
                            if (sudoline.replace('\n', '').strip()[-1]=="\\"):
                                morecontent=1
                            else:
                                morecontent=0
                sudoline = sudofilehandler.readline().replace('\t', ' ')
            sudofilehandler.close
    #print(LABELDIC)
    #print()
    return LABELDIC


def detectusergroups(sudofile):
    result={}
    userlist=[]
    grouplist=[]
    if os.path.isfile(sudofile):
        #Porcess /etc/sudoers file for includes
        with open(sudofile,"r", errors='replace') as sudofilehandler:
            sudoline = sudofilehandler.readline().replace('\t', ' ')
            ln=0
            stopprocess=0
            morecontent=0
            PREVIOUSLABEL=""
            CURRENTLABEL=""
            DEFAULTSNUMBER=1
            while sudoline:
                #print("Linea: "+sudoline)
                ln=ln+1
                labelfind=0
                firstword=""
                firstchar=""
                sudolineprocessed=""
                if len(sudoline)>0:
                    sudolineprocessed=sudoline.replace('\n', '').strip()
                if len(sudolineprocessed)>0:                    
                    firstchar=sudolineprocessed[0]
                    auxline=sudolineprocessed.split()
                    if (len(auxline)>0):
                        firstword=auxline[0].upper()
                    
                    #print("firstchar:"+firstchar+" line:"+sudolineprocessed)
                    if firstchar != '#':
                        # A line not commented
                        if morecontent == 0:
                            # Process because is not part of previous line
                            foudequal=sudolineprocessed.find("=")
                            if foudequal >= 0:
                                # Found the "=" character in the line
                                if firstword != "CMND_ALIAS" and firstword != "USER_ALIAS" and firstword != "HOST_ALIAS" and firstword != "DEFAULTS":
                                    # is not a label definition
                                    AUXEQUALITY=sudolineprocessed.split("=")
                                    if len(AUXEQUALITY)==2:
                                        # Got an assignation
                                        AUXLABELS=AUXEQUALITY[0].strip().split()
                                        if len(AUXLABELS)>1:
                                            usergrouplables=AUXLABELS[0].strip().split(',')
                                            for ug in usergrouplables:
                                                ugid=''
                                                if len(ug)>0:
                                                    ugid=ug[0]
                                                    if ugid == '%':
                                                        grouplist.append(ug)
                                                    else:
                                                        userlist.append(ug)
                                            #print("firstchar:"+firstchar+" line:"+sudolineprocessed)
                        # Detect if there are more lines 
                        #print("line:"+sudolineprocessed)
                        if (sudolineprocessed[-1]=="\\"):
                            morecontent=1
                        else:
                            morecontent=0
                #
                sudoline = sudofilehandler.readline().replace('\t', ' ')
            sudofilehandler.close
    result={'userlist':userlist,'grouplist':grouplist}
    return result

def getassignslist(assignstring):
    result=[]
    auxstring=assignstring.replace('\n', '').replace('\t', '').replace('\\', '').replace(' ', '')
    auxstring=auxstring.strip().replace('#', ',#')
    result=auxstring.split(',')
    return result

def getsudoersaliases(sudoincludes):
    sudoaliasfound=[]
    sudoaliasfoundwithfile=[]
    tmpassign={}
    usersandgroups={'userlist':[],'grouplist':[],'aliaslist':[]}
    uandg={}
    SUDOALIASES= {'User_Alias': {},'Host_Alias': {},'Cmnd_Alias':{},'Runas_Alias':{},'Defaults':{},'assigns':{}}
    SUDOALIASES['User_Alias']=processsudofile('User_Alias','/etc/sudoers')
    SUDOALIASES['Host_Alias']=processsudofile('Host_Alias','/etc/sudoers')
    SUDOALIASES['Cmnd_Alias']=processsudofile('Cmnd_Alias','/etc/sudoers')
    SUDOALIASES['Runas_Alias']=processsudofile('Runas_Alias','/etc/sudoers')
    
    SUDOALIASES['Defaults']=processsudofile('Defaults','/etc/sudoers')
    uandg=detectusergroups('/etc/sudoers')
    for usr in uandg['userlist']:
        if usr in SUDOALIASES['User_Alias']:
            aliasdic={}
            aliasdic['alias']=usr
            aliasdic['file']='/etc/sudoers'
            tmpassign={}
            tmpassign=processsudofileassign(usr,'/etc/sudoers')
            #aliasdic['assigns']=processsudofileassign(usr,'/etc/sudoers')
            aliasdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
            aliasdic['Host_Alias']=tmpassign[usr]['Host_Alias']
            usersandgroups['aliaslist'].append(aliasdic)
            sudoaliasfound.append(usr)
            sudoaliasfoundwithfile.append('/etc/sudoers')
        else:    
            userdic={}
            userdic['user']=usr
            userdic['file']='/etc/sudoers'
            tmpassign={}
            tmpassign=processsudofileassign(usr,'/etc/sudoers')
            #userdic['assigns']=processsudofileassign(usr,'/etc/sudoers')
            userdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
            userdic['Host_Alias']=tmpassign[usr]['Host_Alias']
            usersandgroups['userlist'].append(userdic)
    for grp in uandg['grouplist']:
        groupdic={}
        groupdic['group']=grp
        groupdic['file']='/etc/sudoers'
        tmpassign={}
        tmpassign=processsudofileassign(grp,'/etc/sudoers')
        #groupdic['assigns']=processsudofileassign(grp,'/etc/sudoers')
        groupdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
        groupdic['Host_Alias']=tmpassign[usr]['Host_Alias']
        usersandgroups['grouplist'].append(groupdic)
        
    for includefile in sudoincludes['includelist']:
        #lists
        #SUDOALIASES['User_Alias']=SUDOALIASES['User_Alias']+processsudofile('User_Alias',includefile)
        #Dictionaries
        SUDOALIASES['User_Alias'].update(processsudofile('User_Alias',includefile))
        SUDOALIASES['Host_Alias'].update(processsudofile('Host_Alias',includefile))
        SUDOALIASES['Cmnd_Alias'].update(processsudofile('Cmnd_Alias',includefile))
        SUDOALIASES['Runas_Alias'].update(processsudofile('Runas_Alias',includefile))
        SUDOALIASES['Defaults'].update(processsudofile('Defaults',includefile))
        uandg=detectusergroups(includefile)
        #print(uandg)
        #print(' ')
        for usr in uandg['userlist']:
            if usr in SUDOALIASES['User_Alias']:
                aliasdic={}
                aliasdic['alias']=usr
                aliasdic['file']=includefile                
                tmpassign={}
                tmpassign=processsudofileassign(usr,includefile)
                #aliasdic['assigns']=processsudofileassign(usr,includefile)
                aliasdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
                aliasdic['Host_Alias']=tmpassign[usr]['Host_Alias']

                usersandgroups['aliaslist'].append(aliasdic)
                sudoaliasfound.append(usr)
                sudoaliasfoundwithfile.append(includefile)
            else:    
                userdic={}
                userdic['user']=usr
                userdic['file']=includefile
                tmpassign={}                
                tmpassign=processsudofileassign(usr,includefile)
                #print(tmpassign)
                #userdic['assigns']=processsudofileassign(usr,includefile)
                userdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
                userdic['Host_Alias']=tmpassign[usr]['Host_Alias']
                usersandgroups['userlist'].append(userdic)

        for grp in uandg['grouplist']:
            groupdic={}
            groupdic['group']=grp
            groupdic['file']=includefile
            tmpassign={}
            tmpassign=processsudofileassign(grp,includefile)
            #groupdic['assigns']=processsudofileassign(grp,includefile)
            groupdic['assigns']=getassignslist(tmpassign[grp]['assigns'])
            groupdic['Host_Alias']=tmpassign[grp]['Host_Alias']
            usersandgroups['grouplist'].append(groupdic)    
    
    # User aliases
    pos=0
    for useraliaskey in SUDOALIASES['User_Alias']:
        if useraliaskey not in sudoaliasfound:
            aliasdic={}
            aliasdic['alias']=useraliaskey
            aliasdic['file']=sudoaliasfoundwithfile[pos]
            tmpassign={}
            tmpassign=processsudofileassign(usr,includefile)
            #aliasdic['assigns']=processsudofileassign(usr,includefile)
            aliasdic['assigns']=getassignslist(tmpassign[usr]['assigns'])
            aliasdic['Host_Alias']=tmpassign[usr]['Host_Alias']
            usersandgroups['aliaslist'].append(aliasdic)
        pos=pos+1
    SUDOALIASES['assigns']=usersandgroups
    #        SUDOALIASES['assigns'][useraliaskey]=processsudofileassign(useraliaskey,'/etc/sudoers')
    #        for includefile in sudoincludes['includelist']:
    #            SUDOALIASES['assigns'][useraliaskey].update(processsudofileassign(useraliaskey,includefile))
    return SUDOALIASES


def getsudopermissions(SUDODIC,sudologdic):
    # Function to detect excessive permissions
    result={}
    result={'explisit':[],'potentially':[],'suspicious':[]}
    ep_explisit=['NOPASSWD:ALL','ALL','(ALL)NOPASSWD:ALL']
    ep_potentially=[]
    ep_suspicious=[]
    #
    os_grouplist=[]
    groups = grp.getgrall()
    for group in groups:
        os_grouplist.append(group[0])
    #
    os_userlist=[]
    os_userlist.append('ALL')
    users = pwd.getpwall()
    for user in users:
        os_userlist.append(user[0])

    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Inspecting userz permissions')
    for userdic in SUDODIC['aliases']['assigns']['userlist']:
        for cmdassignation in userdic['assigns']:
            tmprecord={}
            tmprecord['type']='user'
            tmprecord['name']=userdic['user']
            auxuser=userdic['user']
            tmprecord['groups']=''
            tmprecord['users']=auxuser
            tmprecord['assign']=cmdassignation
            tmprecord['file']=userdic['file']
            tmprecord['hosts']=userdic['Host_Alias']
            tmprecord['comment']=''
            potentially_flag=False
            if auxuser not in os_userlist:
                tmprecord['comment']='User not deffined in the system'
            if cmdassignation.upper() in ep_explisit:
                result['explisit'].append(tmprecord)
            elif cmdassignation.upper() in ep_potentially or potentially_flag==True:
                result['potentially'].append(tmprecord)
            elif cmdassignation.upper() in ep_suspicious:
                result['suspicious'].append(tmprecord)

    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Inspecting groups permissions')
    for groupdic in SUDODIC['aliases']['assigns']['grouplist']:
        for cmdassignation in groupdic['assigns']:
            tmprecord={}
            tmprecord['type']='group'
            auxgroup=groupdic['group']
            tmprecord['name']=auxgroup
            tmprecord['groups']=auxgroup
            tmprecord['users']=grp.getgrnam(auxgroup.replace('%',''))[3]
            tmprecord['assign']=cmdassignation
            tmprecord['file']=groupdic['file']
            tmprecord['hosts']=groupdic['Host_Alias']
            tmprecord['comment']=''
            potentially_flag=False
            if auxgroup not in os_grouplist:
                tmprecord['comment']='Group not deffined in the system'
            if cmdassignation.upper() in ep_explisit:
                result['explisit'].append(tmprecord)
            elif cmdassignation.upper() in ep_potentially or potentially_flag==True:
                result['potentially'].append(tmprecord)
            elif cmdassignation.upper() in ep_suspicious:
                result['suspicious'].append(tmprecord)
    
    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Inspecting user_alias permissions')

    for aliasdic in SUDODIC['aliases']['assigns']['aliaslist']:
        for cmdassignation in aliasdic['assigns']:
            auxcomment=''
            tmprecord={}
            tmprecord['type']='alias'
            tmprecord['name']=aliasdic['alias']
            AUXUSR=SUDODIC['aliases']['User_Alias'][aliasdic['alias']]
            AUXUSRlist=AUXUSR.strip().split(',')
            AUXUSERlist=''
            AUXgrp=''            
            for userorgroup in AUXUSRlist:
                AUXSTRING=''
                if userorgroup.find("%") >=0: 
                    AUXgrp=AUXgrp+' '+userorgroup.strip()
                    aul=getuserlistfromgroup(userorgroup.strip())
                    for usr in aul:                        
                        if len(AUXSTRING)==0:
                            AUXSTRING=usr
                            #print(usr)
                        else:
                            AUXSTRING=AUXSTRING+','+usr
                else:
                    AUXSTRING=userorgroup.strip()
                if len(AUXSTRING.strip())>0:
                    if len(AUXUSERlist)==0:                    
                        AUXUSERlist=AUXSTRING
                    else:
                        AUXUSERlist=AUXUSERlist+','+AUXSTRING
            tmprecord['groups']=AUXgrp
            tmprecord['users']=AUXUSERlist
            tmprecord['assign']=cmdassignation
            tmprecord['file']=aliasdic['file']
            tmprecord['hosts']=aliasdic['Host_Alias']
            if len(AUXgrp)>0:
                auxcomment='Involve groups: '+AUXgrp.strip()
            tmprecord['comment']=auxcomment
            potentially_flag=False
            if cmdassignation.upper() in ep_explisit:
                result['explisit'].append(tmprecord)
            elif cmdassignation.upper() in ep_potentially or potentially_flag==True:
                result['potentially'].append(tmprecord)
            elif cmdassignation.upper() in ep_suspicious:
                result['suspicious'].append(tmprecord)
    return result 


def getsudo_fact(sudologdic):
    SUDODIC= {'installed':False, 'platform': '','binaryinfo': '','check': '','includespath': '','includes': {},'aliases': {}}
    SUDODIC['platform']=getsudoplatform(sudologdic)
    SUDODIC['installed']=getsudoinstalled(SUDODIC['platform'],sudologdic)
    SUDODIC['binaryinfo']=getsudoversion(sudologdic)
    SUDODIC['check']=getsudocheck(sudologdic)
    SUDODIC['includespath']=getsudoerstemplatespath()
    SUDODIC['includes']=getsudoersincludes(sudologdic)
    SUDODIC['aliases']=getsudoersaliases(SUDODIC['includes'])
    return SUDODIC

def getsudoplatform(sudologdic):
    flavor=execute("uname",sudologdic)
    #check if allways is encoded in "utf-8" .decode("utf-8")
    straux=str(flavor).replace("\n",'').strip()
    #AUX=str(flavor).strip().split("\n")
    #platform=AUX[0]
    platform=straux
    #print(platform +"-"+ str(len(platform)))
    return platform

def getsudoinstalled(platform,sudologdic):
    sudoinstalled=False
    if platform == "Linux":
         if os.path.isfile('/usr/bin/sudo'):
             if os.path.isfile('/usr/sbin/visudo'):
                 if os.path.isfile('/etc/sudoers'):
                     sudoinstalled=True
    if platform == "zLinux":
         if os.path.isfile('/usr/bin/sudo'):
             if os.path.isfile('/usr/sbin/visudo'):
                 if os.path.isfile('/etc/sudoers'):
                     sudoinstalled=True
    if platform == "AIX":
         if os.path.isfile('/usr/bin/sudo'):
             if os.path.isfile('/usr/sbin/visudo'):
                 if os.path.isfile('/etc/sudoers'):
                     sudoinstalled=True

    return sudoinstalled

def getsudoershealth(sudoersfile,sudologdic):
    resultcode=0
    command='/usr/sbin/visudo'
    if os.path.isfile(command):
        fullcommand=command+' -c -f '
        healthresult=executefull(fullcommand+sudoersfile,sudologdic)
        resultcode=healthresult['rc']
    else:
        resultcode=127
    return resultcode

def sudoremplaceincludedir(sudosource,sudotarget,SUDODICTIONARY,sudologdic):
    resultcode=0
    # 0 Execution succesfull
    # 1 sudo source doesn't exists
    # 2 sudo source is not consistent 
    # 3 sudo source havent #includedir
    # 4 sudo includedir doesen't exists
    # 5 No files detected in the include dir
    if os.path.isfile(sudosource):
        if (getsudoershealth(sudosource,sudologdic)==0):
            #Porcess sudoers source  and source target
            with open(sudosource,"r") as sudosourcefh:
                with open(sudotarget,"w") as sudotargetfh:
                    #print("processing file:"+sudotarget)
                    sudoline = sudosourcefh.readline()
                    sudoauxline = sudoline.replace('\t', ' ')
                    while sudoline:
                        firstword=""
                        auxline=sudoauxline.replace('\n', '').strip().split()
                        if (len(auxline)>0):
                            firstword=auxline[0].upper()
                        if (firstword == "#INCLUDEDIR"):
                            if sudologdic['log']==True:
                                logtofile(sudologdic['logfile'],'Replacing #includedir directive (sudoremplaceincludedir) ')
                            #processs included templates
                            AUXSUDOERSINCLUDEPATH=SUDODICTIONARY['binaryinfo']['sudoersincludespath']
                            if os.path.isdir(AUXSUDOERSINCLUDEPATH):
                                INCLUDEFILELIST=os.listdir(AUXSUDOERSINCLUDEPATH)
                                if (len(INCLUDEFILELIST)==0):
                                    resultcode=5
                                    #No files detected in the include dir
                                for templatefile in INCLUDEFILELIST:
                                    sudotargetfh.write('#include '+AUXSUDOERSINCLUDEPATH+'/'+templatefile+"\n")
                                    if sudologdic['log']==True:
                                        logtofile(sudologdic['logfile'],'Adding #include '+AUXSUDOERSINCLUDEPATH+'/'+templatefile+' (sudoremplaceincludedir) ')
                                    #print(templatefile)
                            else:
                                # 4 sudo includedir doesen't exists
                                resultcode=4
                        else:
                            #write line
                            sudotargetfh.write(sudoline)
                            #sudotargetfh.write("\n")
                        sudoline = sudosourcefh.readline()
                        sudoauxline = sudoline.replace('\t', ' ')
                    sudotargetfh.close()
                sudosourcefh.close()
                #print("file "+sudotarget)
                #catfile(sudotarget)
        else:
            resultcode=2
            # 2 sudo source is not consistent 
    else:   
        resultcode=1
    return resultcode


def getfirstwordlastlinenumber(sudoersfile,wordtofind,findpartial):
    wordtf=wordtofind.upper()
    wordtflen=len(wordtofind)
    linenumberresult=0
    linenumber=1
    # 0 include not found
    # -1 file doesen't exists
    if os.path.isfile(sudoersfile):
        with open(sudoersfile,"r") as sudofh:
            sudoline = sudofh.readline()
            sudoauxline = sudoline.replace('\t', ' ')
            while sudoline:
                firstword=""
                auxline=sudoauxline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (firstword == wordtf ):
                    linenumberresult=linenumber
                else:
                    if (findpartial>0):
                        # Find word in bigger words(Example: if you find #inlcude... #includedir will be a succesfull found)
                        if (len(firstword) >= wordtflen):
                            if (firstword[:wordtflen] == wordtf):
                                linenumberresult=linenumber
                sudoline = sudofh.readline()
                sudoauxline = sudoline.replace('\t', ' ')
                linenumber=linenumber+1
            sudofh.close
    else:
        linenumberresult=-1
    return linenumberresult

def getfirstwordfirstlinenumber(sudoersfile,wordtofind,findpartial):
    wordtf=wordtofind.upper()
    wordtflen=len(wordtofind)
    linenumberresult=0
    linenumber=1
    # 0 include not found
    # -1 file doesen't exists
    if os.path.isfile(sudoersfile):
        with open(sudoersfile,"r") as sudofh:
            sudoline = sudofh.readline()
            sudoauxline = sudoline.replace('\t', ' ')
            while sudoline and linenumberresult==0:
                firstword=""
                auxline=sudoauxline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (firstword == wordtf ):
                    linenumberresult=linenumber
                else:
                    if (findpartial>0):
                        # Find word in bigger words(Example: if you find #inlcude... #includedir will be a succesfull found)
                        if (len(firstword) >= wordtflen):
                            if (firstword[:wordtflen] == wordtf):
                                linenumberresult=linenumber
                sudoline = sudofh.readline()
                sudoauxline = sudoline.replace('\t', ' ')
                linenumber=linenumber+1
            sudofh.close
    else:
        linenumberresult=-1
    return linenumberresult

def getincludelinenumber(sudoersfile,includetofind,SUDODICTIONARY):
    includetf=includetofind.upper()
    includetfext=SUDODICTIONARY['includespath'].upper()+'/'+includetofind.upper()
    linenumberresult=0
    linenumber=1
    # 0 include not found
    # -1 sudoers file doesen't exists
    if os.path.isfile(sudoersfile):
        with open(sudoersfile,"r") as sudofh:
            sudoline = sudofh.readline()
            sudoauxline = sudoline.replace('\t', ' ')
            while sudoline:
                firstword=""
                seccondword=""
                auxline=sudoauxline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (len(auxline)>1):
                    seccondword=auxline[1].upper()
                if (firstword == '#INCLUDE' ):
                    #print(includetfext,' ',seccondword)
                    if ((seccondword == includetf) or (seccondword == includetfext)):
                        linenumberresult=linenumber
                sudoline = sudofh.readline()
                sudoauxline = sudoline.replace('\t', ' ')
                linenumber=linenumber+1
            sudofh.close
    else:
        linenumberresult=-1
    return linenumberresult


def getincludetotallines(sudoersfile):
    linenumberresult=0
    linenumber=1
    # 0 includes not found
    # -1 sudoers file doesen't exists
    if os.path.isfile(sudoersfile):
        with open(sudoersfile,"r") as sudofh:
            sudoline = sudofh.readline()
            sudoauxline = sudoline.replace('\t', ' ')
            while sudoline:
                firstword=""
                auxline=sudoauxline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (firstword == '#INCLUDE' ):
                    #print(includetfext,' ',seccondword)
                    linenumberresult=linenumberresult+1
                    
                sudoline = sudofh.readline()
                sudoauxline = sudoline.replace('\t', ' ')
                linenumber=linenumber+1
            sudofh.close
    else:
        linenumberresult=-1
    return linenumberresult

def getincludelinenumberrelative(sudoersfile,includetofind,SUDODICTIONARY):
    includetf=includetofind.upper()
    includetfext=SUDODICTIONARY['includespath'].upper()+'/'+includetofind.upper()
    linenumberresult=0
    linenumberrelative=0
    linenumber=1
    # 0 include not found
    # -1 sudoers file doesen't exists
    if os.path.isfile(sudoersfile):
        with open(sudoersfile,"r") as sudofh:
            sudoline = sudofh.readline()
            sudoauxline = sudoline.replace('\t', ' ')
            while sudoline:
                firstword=""
                seccondword=""
                auxline=sudoauxline.replace('\n', '').strip().split()
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (len(auxline)>1):
                    seccondword=auxline[1].upper()
                if (firstword == '#INCLUDE' ):
                    linenumberrelative=linenumberrelative+1
                    #print(includetfext,' ',seccondword)
                    if ((seccondword == includetf) or (seccondword == includetfext)):
                        linenumberresult=linenumberrelative
                sudoline = sudofh.readline()
                sudoauxline = sudoline.replace('\t', ' ')
                linenumber=linenumber+1
            sudofh.close
    else:
        linenumberresult=-1
    return linenumberresult


def sudoincludedirfix(backup,SUDODICTIONARY,sudologdic):
    SUDOERSFILE='/etc/sudoers'
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: #includedir directive removed succesfully (rc=0).",
            "ERR: Directive #includedir not present (rc=1).",
            "ERR: Replacement try got error (rc=2).",
            "ERR: Sudoers file "+SUDOERSFILE+" inconsistent (rc=3)."
            ]

    
    if (SUDODICTIONARY['includes']['includedir']>0):
        # Processing the implement
        tmpsudofile='/tmp/sudoers-fixincludedir-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".tmp"
        #tmpsudofile=aux.replace(':','').replace(' ','').replace('.','')
        #shutil.copy2('/etc/sudoers', tmpsudofile)
        RC=sudoremplaceincludedir(SUDOERSFILE,tmpsudofile,SUDODICTIONARY,sudologdic)
        # catfile(tmpsudofile)
        # print('TMPFILE: '+tmpsudofile)
        # print("RC sudoremplaceincludedir=")
        # print(RC)
        if (RC == 0): 
            # Checking consistency
            if (getsudoershealth(tmpsudofile,sudologdic)==0):
                if backup==True:
                    backupsudofile=SUDOERSFILE+'-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".bkp"
                    shutil.copy2(SUDOERSFILE,backupsudofile)
                    os.chmod(backupsudofile, 0o440)
                shutil.copy2(tmpsudofile,SUDOERSFILE)
                os.chmod(SUDOERSFILE, 0o440)
            else:
                resultcode['rc']=3
                # 3 sudoers file inconsistent
        else:
            resultcode['rc']=2
            # 2 replacement try got error

        #Finishing process
        if os.path.isfile(tmpsudofile):
            os.remove(tmpsudofile)
    else:
        resultcode['rc']=1
        # 1 Directive #includedir not present

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def sudoinserttemplate(backup,sudoersfile,templatefile,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Template "+templatefile+" inserted succesfully (rc=0).",
            "ERR: Template "+templatefile+" doesn't exsists (rc=1).",
            "ERR: Sudoers file "+sudoersfile+" doesn't exsists (rc=2).",
            "ERR: Directive #includedir implemented (rc=3).",
            "ERR: Sudoers file "+sudoersfile+" inconsistent (rc=4).",
            "WAR: Template "+templatefile+" already there (rc=5)."
            ]

    TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+str(templatefile)
    TEMPLATEINCLUDELINE="#include "+TEMPLATEFILEFULLPATH
    if os.path.isfile(sudoersfile):
        templatelinenumber=getincludelinenumber(sudoersfile,templatefile,SUDODICTIONARY)
        if (templatelinenumber == 0):
            if os.path.isfile(TEMPLATEFILEFULLPATH):
                # Setting the sudoers template permissions
                os.chmod(TEMPLATEFILEFULLPATH, 0o440)
                if (SUDODICTIONARY['includes']['includedir']==0):
                    # Processing the implement
                    tmpsudofile='/tmp/sudoers-inserttemplate-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".tmp"
                    if sudologdic['log']==True:
                        logtofile(sudologdic['logfile'],'Preparing file '+tmpsudofile+' ')
                    #tmpsudofile=aux.replace(':','').replace(' ','').replace('.','')
                    #shutil.copy2(sudoersfile, tmpsudofile)
                    #print('TMPFILE: '+tmpsudofile)
                    ## Process the insertion
                    #lnincludedir=getfirstwordlastlinenumber(sudoersfile,'#includedir',0)
                    lninsert=0
                    lninclude=getfirstwordlastlinenumber(sudoersfile,'#include',0)
                    lnall=getfirstwordlastlinenumber(sudoersfile,'ALL',0)
                    if (lninclude>0):
                        lninsert=lninclude
                    else:
                        if (lnall>0):
                            lninsert=lnall
                    linepos=1
                    #print("lninclude: ",lninclude)
                    #print("lnall: ",lnall)
                    with open(sudoersfile,"r") as sudosourcefh:
                        with open(tmpsudofile,"w") as sudotargetfh:
                            sudoline = sudosourcefh.readline()
                            while sudoline:
                                if (lninclude>0):
                                    #print('linepos: ',linepos,' lninclude: ',lninclude)
                                    sudotargetfh.write(sudoline)
                                    if (lninclude==linepos):
                                        sudotargetfh.write(TEMPLATEINCLUDELINE+'\n')
                                else:
                                    if (lnall>0):
                                        #processing if line "ALL" found 
                                        if (lninclude==linepos):
                                            sudotargetfh.write(TEMPLATEINCLUDELINE+'\n')
                                            #print(TEMPLATEINCLUDELINE)
                                    sudotargetfh.write(sudoline)
                                sudoline = sudosourcefh.readline()
                                linepos=linepos+1
                            if (lninclude == 0 and lnall == 0):
                                sudotargetfh.write(TEMPLATEINCLUDELINE+'\n')
                                #print(TEMPLATEINCLUDELINE+'\n')

                            sudotargetfh.close
                        sudosourcefh.close
                    ##

                    # Checking consistency
                    if (getsudoershealth(tmpsudofile,sudologdic)==0):
                        if backup==True:
                            backupsudofile=sudoersfile+'-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".bkp"
                            shutil.copy2(sudoersfile,backupsudofile)
                            os.chmod(backupsudofile, 0o440)
                        shutil.copy2(tmpsudofile,sudoersfile)
                        os.chmod(sudoersfile, 0o440)
                    else:
                        resultcode['rc']=4
                        if sudologdic['log']==True:
                            logtofile(sudologdic['logfile'],'Sudoers file inconsistent by sudoinserttemplate function with '+tmpsudofile+' file')
                        # 4 sudoers file inconsistent
                    #Finishing process by removing the tempfile
                    if os.path.isfile(tmpsudofile):
                        #catfile(tmpsudofile)
                        if sudologdic['log']==False:
                            os.remove(tmpsudofile)
                else:
                    resultcode['rc']=3
                    # 3 Directive #includedir implemented
            else:
                #File sudotemplate doesen't exists
                resultcode['rc']=1
        else:
             # Include template already exists
            resultcode['rc']=5
    else:
        #File sudoers doesen't exists
        resultcode['rc']=2
    if sudologdic['log']==True:
        logtofile(sudologdic['logfile'],'Ending function sudoinserttemplate with result code '+str(resultcode['rc']))
    
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def sudoremovetemplate(sudoersfile,templatefile,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Template "+templatefile+" removed succesfully (rc=0).",
            "ERR: Template "+templatefile+" doesn't exsists (rc=1).",
            "ERR: Sudoers file "+sudoersfile+" doesn't exsists (rc=2).",
            "ERR: Directive #includedir implemented (rc=3).",
            "ERR: Sudoers file "+sudoersfile+" inconsistent (rc=4).",
            "ERR: Template "+templatefile+" is not included  (rc=5)."
            ]

    TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+templatefile
    TEMPLATEINCLUDELINE="#include "+TEMPLATEFILEFULLPATH
    if TEMPLATEFILEFULLPATH in SUDODICTIONARY['includes']['includelist']:
        #print(TEMPLATEFILEFULLPATH+" is in indludes")
        if os.path.isfile(sudoersfile):
            if os.path.isfile(TEMPLATEFILEFULLPATH):
                if (SUDODICTIONARY['includes']['includedir']==0):
                    # Processing the implement
                    tmpsudofile='/tmp/sudoers-inserttemplate-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".tmp"
                    linepos=1
                    with open(sudoersfile,"r") as sudosourcefh:
                        with open(tmpsudofile,"w+") as sudotargetfh:
                            sudoline = sudosourcefh.readline()
                            sudoauxline = sudoline.replace('\t', ' ')
                            while sudoline:
                                firstword=""
                                seccondword=""
                                auxline=sudoauxline.replace('\n', '').strip().split()
                                if (len(auxline)>0):
                                    firstword=auxline[0].upper()
                                if (len(auxline)>1):
                                    seccondword=auxline[1].upper()
                                wirteline=1
                                if ((firstword == "#INCLUDE") and  (seccondword == TEMPLATEFILEFULLPATH.upper())):
                                    #if found the line with include, ignore the write to a file
                                    wirteline=0
                                    if sudologdic['log']==True:
                                        logtofile(sudologdic['logfile'],'Marking for remove line  '+sudoline+' (sudoremovetemplate)')
                                if (wirteline==1):
                                    sudotargetfh.write(sudoline)
                                #print(seccondword,wirteline)
                                sudoline = sudosourcefh.readline()
                                sudoauxline = sudoline.replace('\t', ' ')
                                linepos=linepos+1
                            sudotargetfh.close
                        sudosourcefh.close
                    ##

                    # Checking consistency
                    if (getsudoershealth(tmpsudofile,sudologdic)==0):
                        shutil.copy2(tmpsudofile,sudoersfile)
                        os.chmod(sudoersfile, 0o440)
                    else:
                        resultcode['rc']=4
                        # 4 sudoers file inconsistent
                    #Finishing process by removing the tempfile
                    if os.path.isfile(tmpsudofile):
                        os.remove(tmpsudofile)
                else:
                    resultcode['rc']=3
                    # 3 Directive #includedir implemented
            else:
                #File sudotemplate doesen't exists
                resultcode['rc']=1
        else:
            #File sudoers doesen't exists
            resultcode['rc']=2
    else:
        # 5 template is not included
        resultcode['rc']=5
    
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def placefirsttemplate(backup,sudoersfile,templatefile,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Template "+templatefile+" sorted succesfully (rc=0).",
            "ERR: Template "+templatefile+" doesn't exsists (rc=1).",
            "ERR: Sudoers file "+sudoersfile+" doesn't exsists (rc=2).",
            "ERR: Directive #includedir implemented (rc=3).",
            "ERR: Sudoers file "+sudoersfile+" inconsistent (rc=4).",
            "WAR: Template "+templatefile+" is already the first position  (rc=5)."
            ]


    if (SUDODICTIONARY['includes']['includedir']==0):
        insertrc=sudoinserttemplate(backup,sudoersfile,templatefile,SUDODICTIONARY,sudologdic)
        # With this we ensure that at leat one "#include" directive will be there
        #   so no need to check if there is no include directive in order to insert before "ALL ALL=!SUDOSUDO" line
        if (insertrc['rc'] > 0 and insertrc['rc'] < 5):
            resultcode['rc']=insertrc['rc']
        else:
            TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+templatefile
            TEMPLATEINCLUDELINE="#include "+TEMPLATEFILEFULLPATH
            INCLUDESTOTAL=getincludetotallines(sudoersfile)
            INCLUDEPOS=getincludelinenumberrelative(sudoersfile,templatefile,SUDODICTIONARY)
            if INCLUDEPOS>1:
                # Setting the sudoers template permissions
                os.chmod(TEMPLATEFILEFULLPATH, 0o440)
                # Processing the implement
                tmpsudofile='/tmp/sudoers-inserttemplate-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".tmp"            
                lninsert=0
                #lninclude=getfirstwordlastlinenumber(sudoersfile,'#include',0)
                lninclude=getfirstwordfirstlinenumber(sudoersfile,'#include',0)
                #lnall=getfirstwordlastlinenumber(sudoersfile,'ALL',0)
                if (lninclude>0):
                    lninsert=lninclude
                linepos=1
                #print("lninclude: ",lninclude)
                #print("lnall: ",lnall)
                ignoreline=0
                with open(sudoersfile,"r") as sudosourcefh:
                    with open(tmpsudofile,"w") as sudotargetfh:
                        sudoline = sudosourcefh.readline()
                        while sudoline:
                            auxline=sudoline.replace('\n', '').strip().split()
                            firstword=""
                            secondword=""
                            if (len(auxline)>0):
                                firstword=auxline[0].upper()
                            if (len(auxline)>1):
                                secondword=auxline[1]
                                
                            if (lninclude>0):
                                #print('firstword: '+firstword+' second: '+secondword+'   '+TEMPLATEFILEFULLPATH)
                                if (lninclude==linepos):
                                    sudotargetfh.write(TEMPLATEINCLUDELINE+'\n')
                                    #print(' adding  : '+TEMPLATEFILEFULLPATH)
                                if  (firstword == "#INCLUDE" and secondword == TEMPLATEFILEFULLPATH ):
                                    #Ignore the already inserted line
                                    ignoreline=ignoreline+1
                                    #print('IGNOTING firstword: '+firstword+' second: '+secondword+'   '+TEMPLATEFILEFULLPATH)
                                else:
                                    # write the original content
                                    sudotargetfh.write(sudoline)

                            sudoline = sudosourcefh.readline()
                            linepos=linepos+1
                        sudotargetfh.close
                    sudosourcefh.close
                ##
                #print("Ignored files: ",ignoreline)
                # Checking consistency
                if (getsudoershealth(tmpsudofile,sudologdic)==0):
                    shutil.copy2(tmpsudofile,sudoersfile)
                    os.chmod(sudoersfile, 0o440)
                else:
                    if sudologdic['log']==True:
                        logtofile(sudologdic['logfile'],'Sudoers file inconsistent by placefirsttemplate function with '+tmpsudofile+' file')
                    resultcode['rc']=4
                    # 4 sudoers file inconsistent
                #Finishing process by removing the tempfile
                if os.path.isfile(tmpsudofile):
                    #catfile(tmpsudofile)
                    if sudologdic['log']==False:
                        os.remove(tmpsudofile)
            
        
            else:
                # 5 Template already the first
                resultcode['rc']=5
    else:
        resultcode['rc']=3
        # 3 Directive #includedir implemented

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def getlinefromfile(linenumber,file):
    lineresult=""
    linepos=1
    done=0
    if os.path.isfile(file):
        with open(file,"r") as filefh:
            stringline = filefh.readline()
            while stringline and done==0:
                if (linenumber==linepos):
                    lineresult=stringline
                    done=1
                stringline = filefh.readline()
                linepos=linepos+1
            filefh.close
    else:
        lineresult="-1"
    return lineresult

def getlabeluseralias(sudofile,useralias):
    resultdic={'rc':0,'result':''}
    resultdic['rc']=0
    stringresult=''
    useraliasup=useralias.upper()
    useraliasfound=0
    useraliasdirectivefound=0
    # 0 user_alias label found
    # 1 File does not exsists
    # 2 user_alias directive not present
    # 3 user_alias label not present
    
    if os.path.isfile(sudofile):
        with open(sudofile,"r") as sudosourcefh:
            linepos=1
            processrawline=0
            processend=0
            sudoline = sudosourcefh.readline()
            while sudoline and processend==0:
                #lastchar=sudoline.replace('\n', '').strip()[-1]
                lastchar=""
                if len(sudoline)>1:
                    lastchar=sudoline.strip()[-1]
                auxline=sudoline.replace('\n', '').strip().split()
                auxline2=sudoline.replace('\n', '').strip().split('=')
                auxline3=auxline2[0].strip().split()
                firstword=""
                secondword=""
                if (len(auxline)>0):
                    firstword=auxline[0].upper()
                if (len(auxline3)>1):
                    secondword=auxline3[1]
                if (processrawline==1):
                    if (lastchar != "\\"):
                        processrawline=0
                        processend=1
                        stringresult=stringresult+sudoline
                    else:
                        stringresult=stringresult+sudoline[:-1]
                #print(sudoline+" ->>>",linepos,lastchar)
                if  (firstword == "USER_ALIAS"):
                    useraliasdirectivefound=1
                    if (secondword == useraliasup ):
                        useraliasfound=1
                        USERALIASRES=""
                        if (len(auxline2)>1):
                            USERALIASRES=auxline2[1].strip()
                        if (lastchar == "\\"):
                            processrawline=1
                            stringresult=stringresult+USERALIASRES[:-1]
                        else:
                            stringresult=stringresult+USERALIASRES
                        #print(getlinefromfile(linepos,sudofile))    
                sudoline = sudosourcefh.readline()
                linepos=linepos+1
            sudosourcefh.close

        if (useraliasdirectivefound>0):
            if (useraliasfound==0):
                # 3 user_alias not present
                resultdic['rc']=3
        else:
            # 2 user_alias directive not present
            resultdic['rc']=2
            
    else:
        # 1 File does not exsists
        resultdic['rc']=1

    resultdic['result']=stringresult.replace('\n','')
    return resultdic

def replacelineonsudofile(sudofile,linetoreplace,linenew,sudologdic):
    resultcode=0
    # 0 Line replaced succesfully
    # 1 sudofile does not exsists
    # 2 linetoreplace not found
    # 3 previous sudo state not consistent 
    # 4 result sudo state not consistent 
    sudoers="/etc/sudoers"
    BACKUPFILE=sudofile+gettimestampstring()+'.bkp'
    TMPBACKUPFILE='/tmp/sudofile-replacelineonsudofile-tmp-'+gettimestampstring()+'.bkp'
    TEMPFILE='/tmp/sudofile-replacelineonsudofile-tmp-'+gettimestampstring()+'.tmp'
    linefound=0
    if os.path.isfile(sudofile):
        if (getsudoershealth(sudoers,sudologdic)==0):
            with open(sudofile,"r") as sudosourcefh:
                with open(TEMPFILE,"w") as sudotargetfh:
                    #sudoline = sudotargetfh.write
                    linepos=1
                    processrawline=0
                    processend=0
                    sudolineacum = ""
                    sudoline = sudosourcefh.readline()
                    while sudoline and processend==0:
                        #lastchar=sudoline.replace('\n', '').strip()[-1]
                        lastchar=""
                        if len(sudoline)>1:
                            lastchar=sudoline.strip()[-1]
                        sudolineacum=sudolineacum+sudoline
                        if (lastchar != "\\"):
                            if (sudolineacum.strip() == linetoreplace.strip()):
                                res=sudotargetfh.write(linenew)
                                #print(linenew)
                                linefound=1
                            else:
                                res=sudotargetfh.write(sudolineacum)
                            sudolineacum=""

                        sudoline = sudosourcefh.readline()
                        linepos=linepos+1
                    sudotargetfh.close
                sudosourcefh.close
            if (linefound==1):
                # Checking consistency
                #Take a file backup
                #catfile(sudofile)
                #catfile(TEMPFILE)
                #print(sudofile,TEMPFILE)
                shutil.copy2(sudofile,TMPBACKUPFILE)
                #os.remove(sudofile)
                shutil.copy2(TEMPFILE,sudofile)
                os.chmod(sudofile, 0o440)
                if (getsudoershealth(sudoers,sudologdic)>0):
                    #Rollback the change bacause state not consistent 
                    shutil.copy2(TMPBACKUPFILE,sudofile)
                    os.chmod(sudofile, 0o440)
                    resultcode=4
                    # 4 result sudo state not consistent 
                
            if (linefound==0):
                # 2 user_alias label not present
                resultcode=2
        else:
            # 3 previous sudo state not consistent
            resultcode=3
    else:
        # 1 File does not exsists
        resultcode=1

    #removing temp files
    if os.path.isfile(TMPBACKUPFILE):
        os.remove(TMPBACKUPFILE)
    if os.path.isfile(TEMPFILE):
        os.remove(TEMPFILE)

    return resultcode

def getuseraliascmddef(sudofile,useralias):
    resultdic={'rc':0,'stdout':''}
    resultdic['rc']=0
    stringresult=''
    CMDDEFLINE=''
    useraliasup=useralias.upper()
    useraliasfound=0
    # 0 user_alias cmd def found
    # 1 File does not exsists
    # 2 user_alias label not present
    if os.path.isfile(sudofile):
        with open(sudofile,"r") as sudosourcefh:
            linepos=1
            processrawline=0
            processend=0
            sudolineacum = ""
            sudoline = sudosourcefh.readline()
            while sudoline and processend==0:
                #lastchar=sudoline.replace('\n', '').strip()[-1]
                lastchar=""
                if len(sudoline)>1:
                    lastchar=sudoline.strip()[-1]
                sudolineacum=sudolineacum+sudoline
                if (lastchar != "\\"):
                    auxline=sudolineacum.replace('\n', '').strip().split()
                    auxline2=sudolineacum.replace('\n', '').strip().split('=')
                    firstword=""
                    secondword=""
                    auxcommands=[]
                    if (len(auxline)>0):
                        firstword=auxline[0].upper()


                    if (firstword == useraliasup):
                        CMDDEFLINE=sudolineacum
                        useraliasfound=1

                    sudolineacum=""

                sudoline = sudosourcefh.readline()
                linepos=linepos+1
            sudosourcefh.close

        if (useraliasfound==0):
            # 2 user_alias label not present
            resultdic['rc']=2
            
    else:
        # 1 File does not exsists
        resultdic['rc']=1

    resultdic['stdout']=CMDDEFLINE
    return resultdic


def addlabeltoincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic):
    resultcode=0
    # 0 Label added succesfully
    # 1 File does not exsists
    # 2 user_alias directive not present
    # 3 user_alias label not present
    # 4 Label already there
    sudofilenopath=sudofile.split('/')[-1]
    ORIGINALFILE=sudofile
    useraliasup=useralias.upper()
    BACKUPFILE='/tmp/sudofile-'+sudofilenopath+'-backup-'+gettimestampstring()+'.tmp'
    TEMPFILE='/tmp/sudofile-'+sudofilenopath+'-tmp-'+gettimestampstring()+'.tmp'

    #print(BACKUPFILE)
    LABELTOADD=label.strip()
    LINETOADD=''
    USERALIAS=getlabeluseralias(sudofile,useralias)
    #print(USERALIAS)
    #print(sudofile+' '+useralias)
    if (USERALIAS['rc']>=1 and USERALIAS['rc']<=3):
        resultcode=USERALIAS['rc']
    #print('USERALIAS',USERALIAS)
    if (USERALIAS['rc']==0):
        USERALIASLABELS=USERALIAS['result'].replace(' ','').replace('\n','').split(',')
        #print(LABELTOADD,USERALIASLABELS)
        if (LABELTOADD not in USERALIASLABELS):
            LINETOADD="User_Alias "+"\t"+useralias+" = "+USERALIAS['result']+','+LABELTOADD+"\n"
    
            linepos=1
            with open(ORIGINALFILE,"r") as sourcefh:
                with open(TEMPFILE,"w") as targetfh:
                    sudoline = sourcefh.readline()
                    processwrite=1
                    while sudoline:
                        lastchar=""
                        if len(sudoline)>1:
                            lastchar=sudoline.strip()[-1]
                        auxline=sudoline.replace('\n', '').strip().split()
                        auxline2=sudoline.replace('\n', '').strip().split('=')
                        auxline3=auxline2[0].strip().split()
                        firstword=""
                        secondword=""
                        if (len(auxline)>0):
                            firstword=auxline[0].upper()
                        if (len(auxline3)>1):
                            secondword=auxline3[1]

                        if  (firstword == "USER_ALIAS"):
                            if (secondword == useraliasup ):
                                targetfh.write(LINETOADD)
                                processwrite=0
                        if (processwrite==1):
                            targetfh.write(sudoline)
                        else:
                            if (lastchar != "\\"):
                                processwrite=1

                        sudoline = sourcefh.readline()
                        linepos=linepos+1
                    targetfh.close
                sourcefh.close
            
            # Checking consistency
            if (getsudoershealth(TEMPFILE,sudologdic)==0):
                #Take a file backup
                shutil.copy2(ORIGINALFILE,BACKUPFILE)
                # commit transaction
                shutil.copy2(TEMPFILE,ORIGINALFILE)
                os.chmod(ORIGINALFILE, 0o440)
            else:
                resultcode=4
                # 4 sudoers file inconsistent
            
            #Finishing process by removing the tempfile
            #print (TEMPFILE)
            if os.path.isfile(TEMPFILE):
                #catfile(TEMPFILE)
                os.remove(TEMPFILE)
        else:
            # 4 Label already there
            resultcode=4
    else:
        if USERALIAS['rc']<=3:
            resultcode=USERALIAS['rc']
            
            # 1 File does not exsists
            # 2 user_alias directive not present
            # 3 user_alias label not present
   
    return resultcode



def removelabelfromincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic):
    resultcode=0
    # 0 Label removed succesfully
    # 1 File does not exsists
    # 2 user_alias directive not present
    # 3 user_alias label not present
    # 4 Label not there

    if os.path.isfile(sudofile):
        sudofilenopath=sudofile.split('/')[-1]
        ORIGINALFILE=sudofile
        useraliasup=useralias.upper()
        BACKUPFILE='/tmp/sudofile-'+sudofilenopath+'-backup-'+gettimestampstring()+'.tmp'
        TEMPFILE='/tmp/sudofile-'+sudofilenopath+'-tmp-'+gettimestampstring()+'.tmp'
        LABELTOADD=label.strip()
        LINETOADD=''
        USERALIAS=getlabeluseralias(sudofile,useralias)
        #print(USERALIAS)
        if (USERALIAS['rc']>=1 and USERALIAS['rc']<=3):
            resultcode=USERALIAS['rc']
        #print(USERALIAS)
        if (USERALIAS['rc']==0):
            USERALIASLABELS=USERALIAS['result'].replace(' ','').split(',')
            if (LABELTOADD in USERALIASLABELS):
                AUXLABLELIST=""
                for AUXLABEL in USERALIASLABELS:
                    if (AUXLABEL != label):
                        if (AUXLABLELIST == ""):
                            AUXLABLELIST=AUXLABEL
                        else:
                            AUXLABLELIST=AUXLABLELIST+','+AUXLABEL
                LINETOADD="User_Alias "+"\t"+useralias+" = "+AUXLABLELIST+"\n"
            
                linepos=1
                with open(ORIGINALFILE,"r") as sourcefh:
                    with open(TEMPFILE,"w") as targetfh:
                        sudoline = sourcefh.readline()
                        processwrite=1
                        while sudoline:
                            lastchar=""
                            if len(sudoline)>1:
                                lastchar=sudoline.strip()[-1]
                            auxline=sudoline.replace('\n', '').strip().split()
                            auxline2=sudoline.replace('\n', '').strip().split('=')
                            auxline3=auxline2[0].strip().split()
                            firstword=""
                            secondword=""
                            if (len(auxline)>0):
                                firstword=auxline[0].upper()
                            if (len(auxline3)>1):
                                secondword=auxline3[1]

                            if  (firstword == "USER_ALIAS"):
                                if (secondword == useraliasup ):
                                    targetfh.write(LINETOADD)
                                    processwrite=0
                            if (processwrite==1):
                                targetfh.write(sudoline)
                            else:
                                if (lastchar != "\\"):
                                    processwrite=1

                            sudoline = sourcefh.readline()
                            linepos=linepos+1
                        targetfh.close
                    sourcefh.close
                
                # Checking consistency
                if (getsudoershealth(TEMPFILE,sudologdic)==0):
                    #Take a file backup
                    shutil.copy2(ORIGINALFILE,BACKUPFILE)
                    # commit transaction
                    shutil.copy2(TEMPFILE,ORIGINALFILE)
                    os.chmod(ORIGINALFILE, 0o440)
                else:
                    resultcode=4
                    # 4 sudoers file inconsistent
                
                #Finishing process by removing the tempfile
                #print (TEMPFILE)
                if os.path.isfile(TEMPFILE):
                    #catfile(TEMPFILE)
                    os.remove(TEMPFILE)
            else:
                # 4 Label not there
                resultcode=4
    else:                
            resultcode=1
        # 1 File does not exsists
    return resultcode

def getuserlistfromincludeuseralias(sudofile,useralias,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''


    rcstdout=["INF: user list extracted (rc=0).",
            "ERR: File "+sudofile+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+user+" label not present in any file (rc=3).",
            "WAR: Label "+user+" already there (rc=4).",
            "ERR: User "+user+" doesn't exsists (rc=5)."
            ]
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def addusertoincludeuseralias(sudofile,useralias,user,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: User "+user+" added succesfully (rc=0).",
            "ERR: File "+sudofile+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+user+" label not present in any file (rc=3).",
            "WAR: Label "+user+" already there (rc=4).",
            "ERR: User "+user+" doesn't exsists (rc=5)."
            ]
    if (user in getuserlist()):
        label=user
        addlablerc=addlabeltoincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic)
        if (addlablerc>=0 and addlablerc<=4):
            resultcode['rc']=addlablerc
            # Using the result code from addlabeltoincludeuseralias
    else:
        # 5 User does not exists
        resultcode['rc']=5
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def addgrouptoincludeuseralias(sudofile,useralias,group,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Group "+group+" added succesfully (rc=0).",
            "ERR: File "+sudofile+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+group+" label not present in any file (rc=3).",
            "WAR: Label "+group+" already there (rc=4).",
            "ERR: Group "+group+" doesn't exsists (rc=5)."
            ]
    if (group in getgrouplist()):
        label='%'+group
        addlablerc=addlabeltoincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic)
        if (addlablerc>=0 and addlablerc<=4):
            resultcode['rc']=addlablerc
            # Using the result code from addlabeltoincludeuseralias
    else:
        # 5 User does not exists
        resultcode['rc']=5
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def removeuserfromincludeuseralias(sudofile,useralias,user,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: User "+user+" added succesfully (rc=0).",
            "ERR: File "+sudofile+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+user+" label not present in any file (rc=3).",
            "ERR: Label "+user+" not there (rc=4)."
            ]
    
    label=user
    removelablerc=removelabelfromincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic)
    if (removelablerc>=0 and removelablerc<=4):
        resultcode['rc']=removelablerc
        # Using the result code from removelabelfromincludeuseralias
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removegroupfromincludeuseralias(sudofile,useralias,group,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    rcstdout=["INF: Group "+group+" added succesfully (rc=0).",
            "ERR: File "+sudofile+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+group+" label not present in any file (rc=3).",
            "ERR: Label "+group+" not there (rc=4)."
            ]
    
    label='%'+group
    removelablerc=removelabelfromincludeuseralias(sudofile,useralias,label,SUDODICTIONARY,sudologdic)
    if (removelablerc>=0 and removelablerc<=4):
        resultcode['rc']=removelablerc
        # Using the result code from removelabelfromincludeuseralias
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def addusertouseralias(useralias,user,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: User "+user+" added succesfully (rc=0).",
            "ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+useralias+" label not present in any file (rc=3).",
            "WAR: Label "+user+" already there (rc=4).",
            "ERR: User "+user+" not present (rc=5)."
            ]

    
    if (user in getuserlist()):
        label=user
        addlablerc=addlabeltoincludeuseralias('/etc/sudoers',useralias,label,SUDODICTIONARY,sudologdic)
        # 0 User added succesfully
        # 1 File does not exsists
        # 2 user_alias directive not present
        # 3 user_alias label not present
        # 4 Label already there
        # 5 User does not exists

        if addlablerc>0:
            if addlablerc>1:
                forprocess=1
                #Copy all list Values using [:] .. (not just referencinf to the other list)
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    addlablerc=addlabeltoincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
                    # 0 User added succesfully
                    if addlablerc==0:
                        forprocess=0
                        resultcode['rc']=0
                    # 1 File does not exsists
                    if addlablerc==1:
                        forprocess=0
                        resultcode['rc']=1
                    # 2 user_alias directive not present
                    if addlablerc==2:
                        resultcode['rc']=2
                    # 3 user_alias label not present
                    if addlablerc==3:
                        resultcode['rc']=3
                    # 4 Label already there
                    if addlablerc==4:
                        forprocess=0
                        resultcode['rc']=4
            else:
                # 1 /etc/sudoers does not exsists
                resultcode['rc']=1

    else:
        # 5 User does not exists
        resultcode['rc']=5

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def addgrouptouseralias(useralias,group,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: Group "+group+" added succesfully (rc=0).",
            "ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+useralias+" label not present in any file (rc=3).",
            "WAR: Label "+group+" already there (rc=4).",
            "ERR: Group "+group+" doesn't exists (rc=5)."
            ]
    # 0 group added succesfully
    # 1 /etc/sudoers does not exsists
    # 2 user_alias directive not present in any file
    # 3 user_alias label not present in any file
    # 4 Label already there 
    # 5 group does not exists
    
    if (group in getgrouplist()):
        label='%'+group
        addlablerc=addlabeltoincludeuseralias('/etc/sudoers',useralias,label,SUDODICTIONARY,sudologdic)
        resultcode['stdout']='file /etc/sudoers processed'
        # 0 label added succesfully
        # 1 File does not exsists
        # 2 user_alias directive not present
        # 3 user_alias label not present
        # 4 Label already there
        # 5 label does not exists
        if addlablerc>0:
            if addlablerc>1:
                forprocess=1
                #Copy all list Values using [:] .. (not just referencinf to the other list)
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    #print(INCLUDEFILE,label)
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    addlablerc=addlabeltoincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
                    # 0 User added succesfully
                    if addlablerc==0:
                        forprocess=0
                        resultcode['rc']=0
                        resultcode['stdout']='file '+INCLUDEFILE+' processed'
                    # 1 File does not exsists
                    if addlablerc==1:
                        forprocess=0
                        resultcode['rc']=1
                    # 2 user_alias directive not present
                    if addlablerc==2:
                        resultcode['rc']=2
                    # 3 user_alias label not present
                    if addlablerc==3:
                        resultcode['rc']=3
                    # 4 Label already there
                    if addlablerc==4:
                        forprocess=0
                        resultcode['rc']=4
            else:
                #import copy
                 resultcode['rc']=1
    else: 
        # 5 group does not exists
        resultcode['rc']=5
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removeuserfromuseralias(useralias,user,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: User "+user+" removed succesfully (rc=0).",
            "ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+useralias+" label not present in any file (rc=3).",
            "WAR: Label "+user+" not present (rc=4)."
            ]

    #resultcode=0
    # 0 User removed succesfully
    # 1 /etc/sudoers does not exsists
    # 2 user_alias directive not present in any file
    # 3 user_alias label not present in any file
    # 4 Label not present 

    label=user
    removelablerc=removelabelfromincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
    # 0 Label removed succesfully
    # 1 File does not exsists
    # 2 user_alias directive not present
    # 3 user_alias label not present
    # 4 Label not there
    #print(removelablerc)
    if removelablerc>0:
        if removelablerc>1:
            forprocess=1
            #Copy all list Values using [:] .. (not just referencinf to the other list)
            INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
            while (INCLUDEDFILES and forprocess==1):
                INCLUDEFILE=INCLUDEDFILES.pop()
                rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                #addlablerc=addlabeltoincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY)
                #removelablerc=removelabelfromincludeuseralias('/etc/sudoers',useralias,label,SUDODICTIONARY)
                removelablerc=removelabelfromincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
                # 0 User removed succesfully
                if removelablerc==0:
                    forprocess=0
                    resultcode['rc']=0
                # 1 File does not exsists
                if removelablerc==1:
                    forprocess=0
                    resultcode['rc']=1
                # 2 user_alias directive not present
                if removelablerc==2:
                    resultcode['rc']=2
                # 3 user_alias label not present
                if removelablerc==3:
                    resultcode['rc']=3
                # 4 Label not present 
                if removelablerc==4:
                    forprocess=0
                    resultcode['rc']=4
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=1
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removegroupfromuseralias(useralias,group,SUDODICTIONARY,sudologdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: Group "+group+" removed succesfully (rc=0).",
            "ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present in any file (rc=2).",
            "ERR: user_alias "+useralias+" label not present in any file (rc=3).",
            "WAR: Label "+group+" not present (rc=4)."
            ]
    # 0 group removed succesfully
    # 1 /etc/sudoers does not exsists
    # 2 user_alias directive not present in any file
    # 3 user_alias label not present in any file
    # 4 Label not present 

    label='%'+group
    removelablerc=removelabelfromincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
    resultcode['stdout']='/etc/sudoers'
    # 0 Label removed succesfully
    # 1 File does not exsists
    # 2 user_alias directive not present
    # 3 user_alias label not present
    # 4 Label not there

    if removelablerc>0:
        if removelablerc>1:
            forprocess=1
            #Copy all list Values using [:] .. (not just referencinf to the other list)
            INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
            while (INCLUDEDFILES and forprocess==1):
                INCLUDEFILE=INCLUDEDFILES.pop()
                #addlablerc=addlabeltoincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY)
                #removelablerc=removelabelfromincludeuseralias('/etc/sudoers',useralias,label,SUDODICTIONARY)
                removelablerc=removelabelfromincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
                resultcode['stdout']=INCLUDEFILE
                # 0 User removed succesfully
                if removelablerc==0:
                    forprocess=0
                    resultcode['rc']=0
                # 1 File does not exsists
                if removelablerc==1:
                    forprocess=0
                    resultcode['rc']=1
                # 2 user_alias directive not present
                if removelablerc==2:
                    resultcode['rc']=2
                # 3 user_alias label not present
                if removelablerc==3:
                    resultcode['rc']=3
                # 4 Label not present 
                if removelablerc==4:
                    forprocess=0
                    resultcode['rc']=4
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=1

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def sudoershandle(options):
    SUDOHANDLERESULT={}
    return SUDOHANDLERESULT



def addnopasswdtouseraliasfile(useralias,sudofile,SUDODICTIONARY,sudologdic):
    resultcode=0
    # 0 NOPASSWD added succesfully
    # 1 file does not exsists
    # 2 user_alias directive not present
    # 3 NOPASSWD already there 
    # 4 sudo inconsistent
    if os.path.isfile(sudofile):
        sudofilenopath=sudofile.split('/')[-1]
        ORIGINALFILE=sudofile
        useraliasup=useralias.upper()
        BACKUPFILE='/tmp/sudofile-'+sudofilenopath+'-backup-'+gettimestampstring()+'.tmp'
        TEMPFILE='/tmp/sudofile-'+sudofilenopath+'-tmp-'+gettimestampstring()+'.tmp'
        LINETOADD=''
        USERALIAS=getlabeluseralias(sudofile,useralias)
        #print(USERALIAS)
        if (USERALIAS['rc']>=1 and USERALIAS['rc']<=3):
            resultcode=USERALIAS['rc']
        #print(USERALIAS)
        if (USERALIAS['rc']==0):
            USERALIASLABELS=USERALIAS['result'].replace(' ','').split(',')
            if (LABELTOADD in USERALIASLABELS):
                AUXLABLELIST=""
                for AUXLABEL in USERALIASLABELS:
                    if (AUXLABEL != label):
                        if (AUXLABLELIST == ""):
                            AUXLABLELIST=AUXLABEL
                        else:
                            AUXLABLELIST=AUXLABLELIST+','+AUXLABEL
                LINETOADD="User_Alias "+"\t"+useralias+" = "+AUXLABLELIST+"\n"
            
                linepos=1
                with open(ORIGINALFILE,"r") as sourcefh:
                    with open(TEMPFILE,"w") as targetfh:
                        sudoline = sourcefh.readline()
                        processwrite=1
                        while sudoline:
                            lastchar=""
                            if len(sudoline)>1:
                                lastchar=sudoline.strip()[-1]
                            auxline=sudoline.replace('\n', '').strip().split()
                            auxline2=sudoline.replace('\n', '').strip().split('=')
                            auxline3=auxline2[0].strip().split()
                            firstword=""
                            secondword=""
                            if (len(auxline)>0):
                                firstword=auxline[0].upper()
                            if (len(auxline3)>1):
                                secondword=auxline3[1]

                            if  (firstword == "USER_ALIAS"):
                                if (secondword == useraliasup ):
                                    targetfh.write(LINETOADD)
                                    processwrite=0
                            if (processwrite==1):
                                targetfh.write(sudoline)
                            else:
                                if (lastchar != "\\"):
                                    processwrite=1

                            sudoline = sourcefh.readline()
                            linepos=linepos+1
                        targetfh.close
                    sourcefh.close
                
                # Checking consistency
                if (getsudoershealth(TEMPFILE,sudologdic)==0):
                    #Take a file backup
                    shutil.copy2(ORIGINALFILE,BACKUPFILE)
                    # commit transaction
                    shutil.copy2(TEMPFILE,ORIGINALFILE)
                    os.chmod(ORIGINALFILE, 0o440)
                else:
                    resultcode=4
                    # 4 sudoers file inconsistent
                
                #Finishing process by removing the tempfile
                #print (TEMPFILE)
                if os.path.isfile(TEMPFILE):
                    #catfile(TEMPFILE)
                    os.remove(TEMPFILE)
            else:
                # 4 Label not there
                resultcode=4
    else:                
            resultcode=1
        # 1 File does not exsists        
    return resultcode

def addnopasswdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic):
    # 0 NOPASSWD added succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd  not present
    # 4 NOPASSWD already there 
    # 5 sudo previous state inconsistent
    # 6 sudo new state inconsistent
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: NOPASSWD added succesfully to user_alias "+useralias+" at "+template+" template (rc=0).",
            "ERR: Template file "+template+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present at the template "+template+" (rc=2).",
            "ERR: Command  "+sudocmd+" not present on "+useralias+" at "+template+" template (rc=3).",
            "WAR: NOPASSWD is already on user_alias "+useralias+" at "+template+" template (rc=4).",
            "ERR: Previous sudo state inconsistent (rc=5).",
            "ERR: Change generates a sudo state inconsistent (rc=6)."
            ]
    cmdtofind=sudocmd.upper()
    if cmdtofind=="":
        cmdtofind="ALL"

    if os.path.isfile(template):
        TEMPLATEFILEFULLPATH=template
    else:
        TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+template

    resultua=getuseraliascmddef(TEMPLATEFILEFULLPATH,useralias)
    LINETOPROCESS=""
    PROCESSEDLINE=""
    if resultua['rc'] == 0:
        LINETOPROCESS=resultua['stdout']
        LINETOPROCESSPARTS=LINETOPROCESS.strip().split('=')
        LINEFIRSTPART=LINETOPROCESSPARTS[0].strip()
        LINESECONDPART=""
        if len(LINETOPROCESSPARTS)>1:
            LINESECONDPART=LINETOPROCESSPARTS[1].strip()
        COMMANDLIST=LINESECONDPART.strip().split(',')
        CMDLINE=""
        cmdreplaced=0
        #Default value for resultcode not found # 3 sudocmd  not present
        resultcode['rc']=3
        while COMMANDLIST:
            auxcmd=COMMANDLIST.pop(0).strip()
            cmdreplacement=auxcmd
            cmdparts=auxcmd.strip().split(':')
            cmdfirstpart=cmdparts[0].upper()
            cmdsecondpart=""
            if len(cmdparts)>1:
                cmdsecondpart=cmdparts[1].upper()
            
            #print(cmdfirstpart+" "+cmdsecondpart)
            if cmdfirstpart == cmdtofind and cmdsecondpart=="":
                #cmdreplacement="NOPASSWD:"+cmdtofind
                cmdreplacement="NOPASSWD:"+sudocmd
                cmdreplaced=1
        
            if cmdfirstpart == "NOPASSWD" and cmdsecondpart==cmdtofind:
                # 4 NOPASSWD already there 
                #print("NOPASSWD already there ")
                resultcode['rc']=4
            if CMDLINE == "":
                CMDLINE=cmdreplacement
            else: 
                CMDLINE=CMDLINE+","+cmdreplacement

            PROCESSEDLINE=LINEFIRSTPART+ " = " + CMDLINE

        if cmdreplaced==1:
            PROCESSEDLINE=PROCESSEDLINE+'\n'
            resultreplace=replacelineonsudofile(TEMPLATEFILEFULLPATH,LINETOPROCESS,PROCESSEDLINE,sudologdic)
            if resultreplace==0:
                 # 0 NOPASSWD added succesfully
                resultcode['rc']=0
            if resultreplace==1:
                # 1 Template file does not exsists
                resultcode['rc']=1
            if resultreplace==2:
                # 2 user_alias directive not present
                resultcode['rc']=2
            if resultreplace==3:
                # 5 sudo previous state inconsistent
                resultcode['rc']=5
            if resultreplace==4:
                 # 6 sudo new state inconsistent
                resultcode['rc']=6
                
    if resultua['rc'] == 1:
        # 1 Template file does not exsists
        resultcode['rc']=1
    if resultua['rc'] == 2:
        # 2 user_alias directive not present
        resultcode['rc']=2

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removenopasswdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic):
    # 0 NOPASSWD removed succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd  not present
    # 4 NOPASSWD not there 
    # 5 sudo previous state inconsistent
    # 6 sudo new state inconsistent
    
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: NOPASSWD removed succesfully from user_alias "+useralias+" at "+template+" template (rc=0).",
            "ERR: Template file "+template+" doesn't exsists (rc=1).",
            "ERR: user_alias "+useralias+" directive not present at the template "+template+" (rc=2).",
            "ERR: Command "+sudocmd+" not present at "+useralias+" on template "+template+" (rc=3).",
            "WAR: NOPASSWD isn't on cmd "+sudocmd+" on user_alias "+useralias+" at "+template+" template (rc=4).",
            "ERR: sudo previous state inconsistent (rc=5).",
            "ERR: sudo result state inconsistent (rc=6)."
            ]
            
    cmdtofind=sudocmd.upper()
    if cmdtofind=="":
        cmdtofind="ALL"

    if os.path.isfile(template):
        TEMPLATEFILEFULLPATH=template
    else:
        TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+template


    resultua=getuseraliascmddef(TEMPLATEFILEFULLPATH,useralias)
    LINETOPROCESS=""
    PROCESSEDLINE=""
    if resultua['rc'] == 0:
        LINETOPROCESS=resultua['stdout']
        LINETOPROCESSPARTS=LINETOPROCESS.strip().split('=')
        LINEFIRSTPART=LINETOPROCESSPARTS[0].strip()
        LINESECONDPART=""
        if len(LINETOPROCESSPARTS)>1:
            LINESECONDPART=LINETOPROCESSPARTS[1].strip()
        COMMANDLIST=LINESECONDPART.strip().split(',')
        CMDLINE=""
        cmdreplaced=0
        #Default value for resultcode not found # 3 sudocmd  not present
        resultcode['rc']=3
        while COMMANDLIST:
            auxcmd=COMMANDLIST.pop(0).strip()
            cmdreplacement=auxcmd
            cmdparts=auxcmd.strip().split(':')
            cmdfirstpart=cmdparts[0].upper()
            cmdsecondpart=""
            if len(cmdparts)>1:
                cmdsecondpart=cmdparts[1].upper()
            
            #print(cmdfirstpart+" "+cmdsecondpart)
            if cmdfirstpart == cmdtofind and cmdsecondpart=="":
                # 4 NOPASSWD not there 
                resultcode['rc']=4
        
            if cmdfirstpart == "NOPASSWD" and cmdsecondpart==cmdtofind:
                cmdreplacement=cmdtofind
                cmdreplaced=1

            if CMDLINE == "":
                CMDLINE=cmdreplacement
            else: 
                CMDLINE=CMDLINE+","+cmdreplacement

            PROCESSEDLINE=LINEFIRSTPART+ " = " + CMDLINE

        if cmdreplaced==1:
            PROCESSEDLINE=PROCESSEDLINE+'\n'
            resultreplace=replacelineonsudofile(TEMPLATEFILEFULLPATH,LINETOPROCESS,PROCESSEDLINE,sudologdic)
            if resultreplace==0:
                 # 0 NOPASSWD added succesfully
                resultcode['rc']=0
            if resultreplace==1:
                # 1 Template file does not exsists
                resultcode['rc']=1
            if resultreplace==2:
                # 2 user_alias directive not present
                resultcode['rc']=2
            if resultreplace==3:
                # 5 sudo previous state inconsistent
                resultcode['rc']=5
            if resultreplace==4:
                 # 6 sudo new state inconsistent
                resultcode['rc']=6


    if resultua['rc'] == 1:
        # 1 Template file does not exsists
        resultcode['rc']=1
    if resultua['rc'] == 2:
        # 2 user_alias directive not present
        resultcode['rc']=2
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def addnopasswdtouseralias(useralias,sudocmd,SUDODICTIONARY,sudologdic):
    # 0 NOPASSWD added succesfully
    # 1 user_alias directive not present in anyfile
    # 2 sudocmd  not present
    # 3 NOPASSWD already there 
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: NOPASSWD added succesfully to user_alias "+useralias+" (rc=0).",
            "ERR: user_alias "+useralias+" directive not present at any file (rc=1).",
            "ERR: sudocmd not on user_alias "+useralias+" (rc=2).",
            "WAR: NOPASSWD is already on user_alias "+useralias+" (rc=3).",
            "ERR: Sudo previous state is inconsistent (rc=4).",
            "ERR: Sudo result state is inconsistent (rc=5)."
            ]

    template="/etc/sudoers"
    RCUATOTEMP=addnopasswdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic)
    # 0 NOPASSWD added succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd  not present
    # 4 NOPASSWD already there 
    # 5 sudo previous state inconsistent
    # 6 sudo new state inconsistent
    if RCUATOTEMP['rc']>0:
        if RCUATOTEMP['rc']>1:
            forprocess=1
            if RCUATOTEMP['rc']==3:
                resultcode['rc']=2
            if RCUATOTEMP['rc']==4:
                resultcode['rc']=3
            if RCUATOTEMP['rc']==5:
                resultcode['rc']=4
            if RCUATOTEMP['rc']==6:
                resultcode['rc']=5
            if RCUATOTEMP['rc']==2:
            #2 user_alias directive not present so will search in includes
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    ##addlablerc=addlabeltoincludeuseralias(INCLUDEFILE,useralias,label,SUDODICTIONARY,sudologdic)
                    RCUATOTEMP=addnopasswdtouseraliasattemplate(useralias,sudocmd,INCLUDEFILE,SUDODICTIONARY,sudologdic)

                    if RCUATOTEMP['rc']==0:
                        forprocess=0
                        resultcode['rc']=0

                    if RCUATOTEMP['rc']==1:
                        forprocess=0
                        resultcode['rc']=4

                    if RCUATOTEMP['rc']==2:
                        resultcode['rc']=1

                    if RCUATOTEMP['rc']==3:
                        forprocess=0
                        resultcode['rc']=2

                    if RCUATOTEMP['rc']==4:
                        forprocess=0
                        resultcode['rc']=3
                    if RCUATOTEMP['rc']==5:
                        forprocess=0
                        resultcode['rc']=4
                    if RCUATOTEMP['rc']==6:
                        forprocess=0
                        resultcode['rc']=5
                        
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=4

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode






    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removenopasswdfromuseralias(useralias,sudocmd,SUDODICTIONARY,sudologdic):
    # 0 NOPASSWD removed succesfully
    # 1 user_alias directive not present in any file
    # 2 sudocmd  not present
    # 3 NOPASSWD not there 
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent

    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: NOPASSWD removed succesfully from user_alias "+useralias+" (rc=0).",
            "ERR: user_alias "+useralias+" directive not present at any file (rc=1).",
            "ERR: sudocmd not on user_alias "+useralias+" (rc=2).",
            "WAR: NOPASSWD isn't there on user_alias "+useralias+" (rc=3).",
            "ERR: Sudo previous state is inconsistent (rc=4).",
            "ERR: Sudo result state is inconsistent (rc=5)."
            ]

    template="/etc/sudoers"
    RCUATOTEMP=removenopasswdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic)
    # 0 NOPASSWD removed succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd  not present
    # 4 NOPASSWD not there 
    # 5 sudo previous state inconsistent
    # 6 sudo new state inconsistent

    if RCUATOTEMP['rc']>0:
        if RCUATOTEMP['rc']>1:
            forprocess=1
            if RCUATOTEMP['rc']==3:
                resultcode['rc']=2
            if RCUATOTEMP['rc']==4:
                resultcode['rc']=3
            if RCUATOTEMP['rc']==5:
                resultcode['rc']=4
            if RCUATOTEMP['rc']==6:
                resultcode['rc']=5
            if RCUATOTEMP['rc']==2:
            #2 user_alias directive not present so will search in includes
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    RCUATOTEMP=removenopasswdtouseraliasattemplate(useralias,sudocmd,INCLUDEFILE,SUDODICTIONARY,sudologdic)
                    if RCUATOTEMP['rc']==0:
                        forprocess=0
                        resultcode['rc']=0

                    if RCUATOTEMP['rc']==1:
                        forprocess=0
                        resultcode['rc']=4

                    if RCUATOTEMP['rc']==2:
                        resultcode['rc']=1

                    if RCUATOTEMP['rc']==3:
                        forprocess=0
                        resultcode['rc']=2

                    if RCUATOTEMP['rc']==4:
                        forprocess=0
                        resultcode['rc']=3
                    if RCUATOTEMP['rc']==5:
                        forprocess=0
                        resultcode['rc']=4
                    if RCUATOTEMP['rc']==6:
                        forprocess=0
                        resultcode['rc']=5
                        
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=4
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def addcmdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic):
    # 0 cmd added succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd already there
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: CMD added succesfully to user_alias "+useralias+" (rc=0).",
            "ERR: Template file "+template+" does not exsists(rc=1).",
            "ERR: user_alias "+useralias+" directive does not exsists on "+template+" (rc=2).",
            "WAR: sudocmd "+sudocmd+" already on "+useralias+" directive at "+template+"(rc=3).",
            "ERR: sudo previous state inconsistent(rc=4).",
            "ERR: sudo result state inconsistent(rc=5)."
            ]
    cmdtofind=sudocmd.upper()

    if os.path.isfile(template):
        TEMPLATEFILEFULLPATH=template
    else:
        TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+template
    #print(TEMPLATEFILEFULLPATH)
    resultua=getuseraliascmddef(TEMPLATEFILEFULLPATH,useralias)
    LINETOPROCESS=""
    PROCESSEDLINE=""
    if resultua['rc'] == 0:
        LINETOPROCESS=resultua['stdout']
        LINETOPROCESSPARTS=LINETOPROCESS.strip().split('=')
        LINEFIRSTPART=LINETOPROCESSPARTS[0].strip()
        LINESECONDPART=""
        if len(LINETOPROCESSPARTS)>1:
            LINESECONDPART=LINETOPROCESSPARTS[1].strip()
        COMMANDLIST=LINESECONDPART.strip().split(',')
        CMDLINE=""
        cmdreplaced=0
        #Default value for resultcode not found # 3 sudocmd  not present
        resultcode['rc']=3
        cmdfound=0
        while COMMANDLIST and cmdfound==0:
            auxcmd=COMMANDLIST.pop(0).strip()
            cmdreplacement=auxcmd
            cmdparts=auxcmd.strip().split(':')
            cmdfirstpart=cmdparts[0].upper()
            cmdsecondpart=""
            if len(cmdparts)>1:
                cmdsecondpart=cmdparts[1].upper()
            
            #print(cmdfirstpart+" "+cmdsecondpart)
            if cmdfirstpart == cmdtofind and cmdsecondpart=="":
                cmdfound=1
                cmdreplaced=1
        
            if cmdfirstpart == "NOPASSWD" and cmdsecondpart==cmdtofind:
                cmdfound=1
                
            if CMDLINE == "":
                CMDLINE=cmdreplacement
            else: 
                CMDLINE=CMDLINE+","+cmdreplacement

        if cmdfound==1:
                    # 3 CMD already there 
                    resultcode['rc']=3
        else:
            # CMD insertion
            PROCESSEDLINE=LINEFIRSTPART+ " = " +sudocmd +","+ CMDLINE +'\n'
            resultreplace=replacelineonsudofile(TEMPLATEFILEFULLPATH,LINETOPROCESS,PROCESSEDLINE,sudologdic)
            if resultreplace==0:
                 # 0 CMD added succesfully
                resultcode['rc']=0
            if resultreplace==1:
                # 1 Template file does not exsists
                resultcode['rc']=1
            if resultreplace==2:
                # 2 user_alias directive not present
                resultcode['rc']=2
            if resultreplace==3:
                # 5 sudo previous state inconsistent
                resultcode['rc']=5
            if resultreplace==4:
                 # 6 sudo new state inconsistent
                resultcode['rc']=6
                
    if resultua['rc'] == 1:
        # 1 Template file does not exsists
        resultcode['rc']=1
    if resultua['rc'] == 2:
        # 2 user_alias directive not present
        resultcode['rc']=2

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removecmdfromuseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic):
    # 0 cmd removed succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd not there
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent
    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: CMD removed succesfully from user_alias "+useralias+" (rc=0).",
            "ERR: Template file "+template+" does not exsists(rc=1).",
            "ERR: user_alias "+useralias+" directive does not exsists on "+template+" (rc=2).",
            "WAR: sudocmd "+sudocmd+" isn't on "+useralias+" directive at "+template+"(rc=3).",
            "ERR: sudo previous state inconsistent(rc=4).",
            "ERR: sudo result state inconsistent(rc=5)."
            ]

        
    cmdtofind=sudocmd.upper()
    if cmdtofind=="":
        cmdtofind="ALL"

    if os.path.isfile(template):
        TEMPLATEFILEFULLPATH=template
    else:
        TEMPLATEFILEFULLPATH=SUDODICTIONARY['includespath']+'/'+template


    resultua=getuseraliascmddef(TEMPLATEFILEFULLPATH,useralias)
    LINETOPROCESS=""
    PROCESSEDLINE=""
    if resultua['rc'] == 0:
        LINETOPROCESS=resultua['stdout']
        LINETOPROCESSPARTS=LINETOPROCESS.strip().split('=')
        LINEFIRSTPART=LINETOPROCESSPARTS[0].strip()
        LINESECONDPART=""
        if len(LINETOPROCESSPARTS)>1:
            LINESECONDPART=LINETOPROCESSPARTS[1].strip()
        COMMANDLIST=LINESECONDPART.strip().split(',')
        CMDLINE=""
        cmdreplaced=0
        #Default value for resultcode not found # 3 sudocmd  not present
        resultcode['rc']=3
        cmdfound=0
        while COMMANDLIST:
            auxcmd=COMMANDLIST.pop(0).strip()
            cmdreplacement=auxcmd
            cmdparts=auxcmd.strip().split(':')
            cmdfirstpart=cmdparts[0].upper()
            cmdsecondpart=""
            if len(cmdparts)>1:
                cmdsecondpart=cmdparts[1].upper()
            
            cmdreplace=1
            if cmdfirstpart == cmdtofind and cmdsecondpart=="":
                cmdfound=1
                cmdreplace=0
                # 4 NOPASSWD not there 
                resultcode['rc']=4
        
            if cmdfirstpart == "NOPASSWD" and cmdsecondpart==cmdtofind:
                cmdfound=1
                cmdreplace=0
                cmdreplacement=cmdtofind

            if cmdreplace==1:
                if CMDLINE == "":
                    CMDLINE=cmdreplacement
                else: 
                    CMDLINE=CMDLINE+","+cmdreplacement

        if cmdfound==0:
            # 3 sudocmd not there
            resultcode['rc']=3
        
        else:
            PROCESSEDLINE=LINEFIRSTPART+ " = " + CMDLINE+'\n'
            resultreplace=replacelineonsudofile(TEMPLATEFILEFULLPATH,LINETOPROCESS,PROCESSEDLINE,sudologdic)
            if resultreplace==0:
                 # 0 CMD removed succesfully
                resultcode['rc']=0
            if resultreplace==1:
                # 1 Template file does not exsists
                resultcode['rc']=1
            if resultreplace==2:
                # 2 user_alias directive not present
                resultcode['rc']=2
            if resultreplace==3:
                # 5 sudo previous state inconsistent
                resultcode['rc']=5
            if resultreplace==4:
                 # 6 sudo new state inconsistent
                resultcode['rc']=6


    if resultua['rc'] == 1:
        # 1 Template file does not exsists
        resultcode['rc']=1
    if resultua['rc'] == 2:
        # 2 user_alias directive not present
        resultcode['rc']=2

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode


def addcmdtouseralias(useralias,sudocmd,SUDODICTIONARY,sudologdic):
    # 0 cmd added succesfully
    # 1 user_alias directive not present
    # 2 sudocmd already there
    # 3 sudo previous state inconsistent
    # 4 sudo new state inconsistent

    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: CMD added succesfully to user_alias "+useralias+" (rc=0).",
            "ERR: user_alias "+useralias+" directive does not exsists (rc=1).",
            "WAR: sudocmd "+sudocmd+" already on "+useralias+" directive(rc=2).",
            "ERR: sudo previous state inconsistent(rc=3).",
            "ERR: sudo result state inconsistent(rc=4)."
            ]

    template="/etc/sudoers"
    RCUATOTEMP=addcmdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic)
    #RCUATOTEMP=addnopasswdtouseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic)
    # 0 cmd added succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd already there
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent
    if RCUATOTEMP['rc']>0:
        if RCUATOTEMP['rc']>1:
            forprocess=1
            if RCUATOTEMP['rc']==3:
                resultcode['rc']=2
            if RCUATOTEMP['rc']==4:
                resultcode['rc']=3
            if RCUATOTEMP['rc']==5:
                resultcode['rc']=4

            if RCUATOTEMP['rc']==2:
            #2 user_alias directive not present so will search in includes
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    RCUATOTEMP=addcmdtouseraliasattemplate(useralias,sudocmd,INCLUDEFILE,SUDODICTIONARY,sudologdic)
                    if RCUATOTEMP['rc']==0:
                        forprocess=0
                        resultcode['rc']=0

                    if RCUATOTEMP['rc']==1:
                        forprocess=0
                        resultcode['rc']=4

                    if RCUATOTEMP['rc']==2:
                        resultcode['rc']=1

                    if RCUATOTEMP['rc']==3:
                        forprocess=0
                        resultcode['rc']=2

                    if RCUATOTEMP['rc']==4:
                        forprocess=0
                        resultcode['rc']=3
                    if RCUATOTEMP['rc']==5:
                        forprocess=0
                        resultcode['rc']=4

                        
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=3


    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode

def removecmdfromuseralias(useralias,sudocmd,SUDODICTIONARY,sudologdic):
    # 0 cmd removed succesfully
    # 1 user_alias directive not present
    # 2 sudocmd not there
    # 3 sudo previous state inconsistent
    # 4 sudo new state inconsistent

    resultcode={}
    resultcode['rc']=0
    resultcode['stdout']=''
    INCLUDEFILE='/etc/sudoers'
    rcstdout=["INF: CMD removed succesfully from user_alias "+useralias+" (rc=0).",
            "ERR: user_alias "+useralias+" directive does not exsists (rc=1).",
            "WAR: sudocmd "+sudocmd+" isn't on "+useralias+" directive (rc=2).",
            "ERR: sudo previous state inconsistent(rc=3).",
            "ERR: sudo result state inconsistent(rc=4)."
            ]


    template="/etc/sudoers"
    RCUATOTEMP=removecmdfromuseraliasattemplate(useralias,sudocmd,template,SUDODICTIONARY,sudologdic)
    # 0 cmd removed succesfully
    # 1 Template file does not exsists
    # 2 user_alias directive not present
    # 3 sudocmd not there
    # 4 sudo previous state inconsistent
    # 5 sudo new state inconsistent

    if RCUATOTEMP['rc']>0:
        if RCUATOTEMP['rc']>1:
            forprocess=1
            if RCUATOTEMP['rc']==3:
                resultcode['rc']=2
            if RCUATOTEMP['rc']==4:
                resultcode['rc']=3
            if RCUATOTEMP['rc']==5:
                resultcode['rc']=4

            if RCUATOTEMP['rc']==2:
            #2 user_alias directive not present so will search in includes
                INCLUDEDFILES=SUDODICTIONARY['includes']['includelist'][:]
                while (INCLUDEDFILES and forprocess==1):
                    INCLUDEFILE=INCLUDEDFILES.pop()
                    
                    rcstdout[1]="ERR: File "+INCLUDEFILE+" doesn't exsists (rc=1)."
                    RCUATOTEMP=removecmdfromuseraliasattemplate(useralias,sudocmd,INCLUDEFILE,SUDODICTIONARY,sudologdic)
                    if RCUATOTEMP['rc']==0:
                        forprocess=0
                        resultcode['rc']=0

                    if RCUATOTEMP['rc']==1:
                        forprocess=0
                        resultcode['rc']=4

                    if RCUATOTEMP['rc']==2:
                        resultcode['rc']=1

                    if RCUATOTEMP['rc']==3:
                        forprocess=0
                        resultcode['rc']=2

                    if RCUATOTEMP['rc']==4:
                        forprocess=0
                        resultcode['rc']=3
                    if RCUATOTEMP['rc']==5:
                        forprocess=0
                        resultcode['rc']=4
                        
        else:
            # 1 /etc/sudoers does not exsists
            resultcode['rc']=3

    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode
