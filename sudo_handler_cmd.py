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
import sys
import datetime
# Importing all functions from repo lib sudo_handler_lib
from sudo_handler_lib import getsudo_fact 
from sudo_handler_lib import sudoincludedirfix
from sudo_handler_lib import sudoinserttemplate
from sudo_handler_lib import sudoremovetemplate
from sudo_handler_lib import placefirsttemplate
from sudo_handler_lib import addusertoincludeuseralias
from sudo_handler_lib import removeuserfromincludeuseralias
from sudo_handler_lib import addgrouptoincludeuseralias
from sudo_handler_lib import removegroupfromincludeuseralias
from sudo_handler_lib import addusertouseralias
from sudo_handler_lib import removeuserfromuseralias
from sudo_handler_lib import addgrouptouseralias
from sudo_handler_lib import removegroupfromuseralias


from sudo_handler_lib import addnopasswdtouseraliasattemplate
from sudo_handler_lib import removenopasswdtouseraliasattemplate
from sudo_handler_lib import addnopasswdtouseralias
from sudo_handler_lib import removenopasswdfromuseralias

from sudo_handler_lib import addcmdtouseraliasattemplate
from sudo_handler_lib import removecmdfromuseraliasattemplate
from sudo_handler_lib import addcmdtouseralias
from sudo_handler_lib import removecmdfromuseralias


# Variable Definition
#------------------------------------------------------------------------------------------------------------
# LogHandling
logdic = dict(
    log=False,
    logfile="/var/log/sudo_handler"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".log"
    )
sudo_fact={}
sudo_handlercfg = dict(
    version="0.8",
    process=True,
    report=False,
    cmdusage=False,
    backup=True,
    fixincludedir=False
    )

sudoers_file=str('/etc/sudoers')
sudo_module_fixincludedir=False
CR="\n"

#List of unknown arguments
sudo_module_argumentsnotdetected=[]

#List of templates to process
sudo_module_addincludes=[]
sudo_module_addincludesfirst=[]
sudo_module_removeincludes=[]

#List of dictionaries {user,template} to process
sudo_module_addusertotemplate=[]
sudo_module_removeuserfromtemplate=[]
useruseraliastempdic={}

#List of dictionaries {group,template} to process
sudo_module_addgrouptotemplate=[]
sudo_module_removegroupfromtemplate=[]
groupuseraliastempdic={}

#List of dictionaries {user,useralias} to process
sudo_module_addusertouseralias=[]
sudo_module_removeuserfromuseralias=[]
useruseraliasdic={}

#List of dictionaries {group,useralias} to process
sudo_module_addgrouptouseralias=[]
sudo_module_removegroupfromuseralias=[]
groupuseraliasdic={}

#List of dictionaries {templates,useralias} to process with nopasswd
sudo_module_addnopasswdtouseraliastemplate=[]
sudo_module_removenopasswdtouseraliastemplate=[]
useraliastemplate={}

#List of useralias to process with nopasswd
sudo_module_addnopasswdtouseralias=[]
sudo_module_removenopasswdtouseralias=[]
useraliascmd={}

#List of cmd to process with nopasswd
sudo_module_addcmdtouseraliastemplate=[]
sudo_module_removecmdtouseraliastemplate=[]
cmduseraliastemplate={}

#List of cmd to process with nopasswd
sudo_module_addcmdtouseralias=[]
sudo_module_removecmdtouseralias=[]
cmduseralias={}



sudo_module_include=str('')
sudo_module_sudofile=str('')
#sudo_module_state=str('')
sudo_module_includestate=str('')
sudo_module_userstate=str('')
sudo_module_groupstate=str('')
sudo_module_first=False
sudo_module_log=False
sudo_module_fixincludedir=False
sudo_module_user=str('')
sudo_module_group=str('')
sudo_module_user_alias=str('')
#

def cmduse():
    print ("Command usage: ")
    print ("  -? or -h                          : Provides this output ")
    print ("  -report                           : Provides a report without any change ")
    print ("  -fixincludedir                    : Remove the uncompliance #includedir directive if it posible by replacing with indivuduals includes directives ")
    print ("  -addinclude=TEMPLATE              : Adds an include file by providing in the filename ")
    print ("                                      - This will fails if the sudoers is inconsistent, or if have #includedir directive, ")
    print ("                                      or if the file template is not present at /etc/sudoers.d, or if by adding the file brings an incosistence ")
    print ("                                      by repeated labels or any other error")
    print ("  -addincludefirst=TEMPLATE         : Same as 'addinclude' but guarantee that will be the first included file")
    print ("                                      if the included already there but is not the firstone, it moves to the first position.")
    print ("  -removeinclude=TEMPLATE           : Removes an include template by providing the filename ")
    print ("                                      - This will fails if the sudoers is inconsistent, or if have #includedir directive")
    print ("  -addusertoinclude=USER,USER_ALIAS,TEMPLATE")
    print ("                                    : Adds a user to an User_alias label in a specifica sudo Template. ")
    print ("  -removeuserfrominclude=USER,USER_ALIAS,TEMPLATE")
    print ("                                    : Remove a user form an User_alias label in a specifica sudo Template. ")
    print ("  -addgrouptoinclude=GROUP,USER_ALIAS,TEMPLATE")
    print ("                                    : Adds a group to an User_alias label in a specifica sudo Template. ")
    print ("  -removegroupfrominclude=GROUP,USER_ALIAS,TEMPLATE")
    print ("                                    : Remove a group form an User_alias label in a specifica sudo Template. ")
    print ("  -addusertouseralias=USER,USER_ALIAS")
    print ("                                    : Adds a user to an User_alias label. ")
    print ("  -removeuserfromuseralias=USER,USER_ALIAS")
    print ("                                    : Remove a user form an User_alias label. ")
    print ("  -addgrouptouseralias=GROUP,USER_ALIAS")
    print ("                                    : Adds a group to an User_alias label. ")
    print ("  -removegroupfromuseralias=GROUP,USER_ALIAS")
    print ("                                    : Remove a group form an User_alias label. ")
    print ("  -setnopasswdtouseralias=USER_ALIAS,CMD")
    print ("                                    : Set NOPASSWD directive to a specific CMD in a USER_ALIAS. ")
    print ("  -removenopasswdfromuseralias=USER_ALIAS,CMD")
    print ("                                    : Remove NOPASSWD directive from a specific CMD in a USER_ALIAS. ")
    print ("  -setnopasswdtouseraliastemplate=TEMPLATE,USER_ALIAS,CMD")
    print ("                                    : Set NOPASSWD directive to a specific CMD on a USER_ALIAS in a specifica sudo Template. ")
    print ("  -removenopasswdfromuseraliastemplate=TEMPLATE,USER_ALIAS,CMD")
    print ("                                    : Remove NOPASSWD directive from a specific CMD on a USER_ALIAS in a specifica sudo Template. ")

    print ("  -addcmdtouseraliasattemplate=TEMPLATE,USER_ALIAS,CMD")
    print ("                                    : Add a CMD command definition to a USER_ALIAS definition on a specific TEMPLATE. ")
    print ("  -removecmdfromuseraliasattemplate=TEMPLATE,USER_ALIAS,CMD")
    print ("                                    : Remove a CMD command definition from a USER_ALIAS definition on a specific TEMPLATE. ")
    print ("  -addcmdtouseralias=USER_ALIAS,CMD")
    print ("                                    : Add a CMD command definition to a USER_ALIAS definition. ")
    print ("  -removecmdfromuseralias=USER_ALIAS,CMD")
    print ("                                    : Remove a CMD command definition from a USER_ALIAS definition. ")




# Processs Arguments
#------------------------------------------------------------------------------------------------------------
# Count the arguments
arguments = len(sys.argv) - 1
# Output argument-wise
position = 1
insuficientarguments=False
if arguments == 0:
    # Print cmd usage
    cmdusage=1

if arguments==0:
    sudo_handlercfg['cmdusage']=True
print ("sudo_handler_cmd Ver:"+sudo_handlercfg['version']+" ")
paramargs=[]
paramargs.append("")
paramargs.append("")
paramargs.append("")
paramargs.append("")
while (arguments >= position):
    argunknown=True
    arg=sys.argv[position]
    #print ("Parameter %i: %s" % (position, arg))
    argcomponents=arg.strip().split('=')
    directive=argcomponents[0]
    if len(argcomponents)>1:
        directiveargs=argcomponents[1].strip().split(',')
    else:
        aux=",,"
        directiveargs=aux.strip().split(',')
    # Hadling Help
    if directive == "-h":
        sudo_handlercfg['cmdusage']=True
        argunknown=False
    if directive == "-?":
        sudo_handlercfg['cmdusage']=True
        argunknown=False
    # Hadling actions
    if directive == "-report":
        sudo_handlercfg['report']=True
        argunknown=False
    if directive == "-r":
        sudo_handlercfg['report']=True
        argunknown=False
    if directive == "-fixincludedir":
        sudo_handlercfg['fixincludedir']=True
        argunknown=False

    if directive == "-forgotbackup":
        sudo_handlercfg['backup']=False
        argunknown=False

    if directive == "-addinclude":
        sudo_module_addincludes.append(argcomponents[1])
        argunknown=False
    if directive == "-addincludefirst":
        sudo_module_addincludesfirst.append(argcomponents[1])
        argunknown=False
    if directive == "-removeinclude":
        sudo_module_removeincludes.append(argcomponents[1])
        argunknown=False

    paramargs[0]=""
    paramargs[1]=""
    paramargs[2]=""
    paramargs[3]=""
    if len(directiveargs)>0:
        paramargs[0]=directiveargs[0]
    if len(directiveargs)>1:
        paramargs[1]=directiveargs[1]
    if len(directiveargs)>2:
        paramargs[2]=directiveargs[2]
    if len(directiveargs)>3:
        paramargs[3]=directiveargs[3]

    insuficientarguments=False
    if directive == "-addusertoinclude":
        useruseraliastempdic['user']=paramargs[0]
        useruseraliastempdic['useralias']=paramargs[1]
        useruseraliastempdic['template']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_addusertotemplate.append(useruseraliastempdic)
        argunknown=False
    if directive == "-removeuserfrominclude":
        useruseraliastempdic['user']=paramargs[0]
        useruseraliastempdic['useralias']=paramargs[1]
        useruseraliastempdic['template']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_removeuserfromtemplate.append(useruseraliastempdic)
        argunknown=False
    if directive == "-addgrouptoinclude":
        groupuseraliastempdic['group']=paramargs[0]
        groupuseraliastempdic['useralias']=paramargs[1]
        groupuseraliastempdic['template']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_addgrouptotemplate.append(groupuseraliastempdic)
        argunknown=False
    if directive == "-removegroupfrominclude":
        groupuseraliastempdic['group']=paramargs[0]
        groupuseraliastempdic['useralias']=paramargs[1]
        groupuseraliastempdic['template']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_removegroupfromtemplate.append(groupuseraliastempdic)
        argunknown=False

    if directive == "-addusertouseralias":
        useruseraliasdic['user']=paramargs[0]
        useruseraliasdic['useralias']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_addusertouseralias.append(useruseraliasdic)
        argunknown=False
    if directive == "-removeuserfromuseralias":
        useruseraliasdic['user']=paramargs[0]
        useruseraliasdic['useralias']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_removeuserfromuseralias.append(useruseraliasdic)
        argunknown=False
        
    if directive == "-addgrouptouseralias":
        groupuseraliasdic['group']=paramargs[0]
        groupuseraliasdic['useralias']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_addgrouptouseralias.append(groupuseraliasdic)
        argunknown=False
    if directive == "-removegroupfromuseralias":
        groupuseraliasdic['group']=paramargs[0]
        groupuseraliasdic['useralias']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_removegroupfromuseralias.append(groupuseraliasdic)
        argunknown=False

    if directive == "-setnopasswdtouseralias":
        useraliascmd['useralias']=paramargs[0]
        useraliascmd['cmd']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_addnopasswdtouseralias.append(useraliascmd)
        argunknown=False
    if directive == "-removenopasswdfromuseralias":
        useraliascmd['useralias']=paramargs[0]
        useraliascmd['cmd']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_removenopasswdtouseralias.append(useraliascmd)
        argunknown=False
    if directive == "-setnopasswdtouseraliastemplate":
        useraliastemplate['template']=paramargs[0]
        useraliastemplate['useralias']=paramargs[1]
        useraliastemplate['cmd']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_addnopasswdtouseraliastemplate.append(useraliastemplate)
        argunknown=False
    if directive == "-removenopasswdfromuseraliastemplate":
        useraliastemplate['template']=paramargs[0]
        useraliastemplate['useralias']=paramargs[1]
        useraliastemplate['cmd']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_removenopasswdtouseraliastemplate.append(useraliastemplate)
        argunknown=False
    
    if directive == "-addcmdtouseraliasattemplate":
        cmduseraliastemplate['template']=paramargs[0]
        cmduseraliastemplate['useralias']=paramargs[1]
        cmduseraliastemplate['cmd']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_addcmdtouseraliastemplate.append(cmduseraliastemplate)
        argunknown=False
    if directive == "-removecmdfromuseraliasattemplate":
        cmduseraliastemplate['template']=paramargs[0]
        cmduseraliastemplate['useralias']=paramargs[1]
        cmduseraliastemplate['cmd']=paramargs[2]
        if len(directiveargs)<3:
            insuficientarguments=True
        sudo_module_removecmdtouseraliastemplate.append(cmduseraliastemplate)
        argunknown=False

    if directive == "-addcmdtouseralias":
        cmduseralias['useralias']=paramargs[0]
        cmduseralias['cmd']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_addcmdtouseralias.append(cmduseralias)
        argunknown=False
    if directive == "-removecmdfromuseralias":
        cmduseralias['useralias']=paramargs[0]
        cmduseralias['cmd']=paramargs[1]
        if len(directiveargs)<2:
            insuficientarguments=True
        sudo_module_removecmdtouseralias.append(cmduseralias)
        argunknown=False



    #Process unknown arguments
    if argunknown == True:
        sudo_module_argumentsnotdetected.append(directive)
    position = position + 1

# Processing Detected Arguments
#------------------------------------------------------------------------------------------------------------
if sudo_handlercfg['process']==True:
    #Getting Sudo Facts
    sudo_fact=getsudo_fact(logdic)

    # Detect if have sudo
    if sudo_fact['installed']== True:

        if (len(sudo_module_argumentsnotdetected)==0) and (insuficientarguments==False):
            #Processing arguments without errors
            #Fixing includedir directive
            if sudo_handlercfg['fixincludedir']==True:
                print("INF: Removing #includedir directive from /etc/sudoers")
                RC=sudoincludedirfix(sudo_handlercfg['backup'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding Templates in queue
            #         rc=sudoinserttemplate(sudoers_file,sudo_module_include,sudo_fact,logdic)
            for template in sudo_module_addincludes:
                sudo_module_include=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+template
                print("INF: Adding template "+sudo_module_include+" template.")
                RC=sudoinserttemplate(sudo_handlercfg['backup'],sudo_fact['binaryinfo']['sudoerspath'],template,sudo_fact,logdic)
                print(RC['stdout'])
            

            # Adding Templates in queue in first position
            for template in sudo_module_addincludesfirst:
                sudo_module_include=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+template
                print("INF: Adding template "+sudo_module_include+" in first position.")
                RC=placefirsttemplate(sudo_handlercfg['backup'],sudo_fact['binaryinfo']['sudoerspath'],template,sudo_fact,logdic)
                print(RC['stdout'])
            
            # Removing templates in queue
            for template in sudo_module_removeincludes:
                sudo_module_include=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+template
                if os.path.isfile(sudo_module_include):
                    print("INF: Removing template "+sudo_module_include+" template.")
                    RC=sudoremovetemplate(sudo_fact['binaryinfo']['sudoerspath'],template,sudo_fact,logdic)
                    print(RC['stdout'])

            # Adding users to useralias in a template
            for usertemplate in sudo_module_addusertotemplate:
                templatefullpath=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+useruseraliastempdic['template']
                print("INF: Adding user "+usertemplate['user']+" to "+usertemplate['useralias']+" on template "+useruseraliastempdic['template']+".")
                RC=addusertoincludeuseralias(templatefullpath,usertemplate['useralias'],usertemplate['user'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing users from useralias in a template
            for usertemplate in sudo_module_removeuserfromtemplate:
                templatefullpath=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+useruseraliastempdic['template']
                print("INF: Removing user "+usertemplate['user']+" from "+usertemplate['useralias']+" on template "+useruseraliastempdic['template']+".")
                RC=removeuserfromincludeuseralias(templatefullpath,usertemplate['useralias'],usertemplate['user'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding groups to useralias in a template
            for groupuseraliasdic in sudo_module_addgrouptotemplate:
                templatefullpath=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+groupuseraliasdic['template']
                print("INF: Adding group "+usertemplate['group']+" to "+usertemplate['useralias']+" on template "+useruseraliastempdic['template']+".")
                RC=addgrouptoincludeuseralias(templatefullpath,groupuseraliasdic['useralias'],groupuseraliasdic['group'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing groups from useralias in a template
            for groupuseraliasdic in sudo_module_removegroupfromtemplate:
                templatefullpath=sudo_fact['binaryinfo']['sudoersincludespath']+"/"+groupuseraliasdic['template']
                print("INF: Removing group "+usertemplate['group']+" from "+usertemplate['useralias']+" on template "+useruseraliastempdic['template']+".")
                RC=removegroupfromincludeuseralias(templatefullpath,groupuseraliasdic['useralias'],groupuseraliasdic['group'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding users to useralias
            for usertemplate in sudo_module_addusertouseralias:
                print("INF: Adding user "+usertemplate['user']+" to "+usertemplate['useralias']+".")
                RC=addusertouseralias(usertemplate['useralias'],usertemplate['user'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing users from useralias
            for usertemplate in sudo_module_removeuserfromuseralias:
                print("INF: Removing user "+usertemplate['user']+" from "+usertemplate['useralias']+".")
                RC=removeuserfromuseralias(usertemplate['useralias'],usertemplate['user'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding groups to useralias
            for groupuseraliasdic in sudo_module_addgrouptouseralias:
                print("INF: Adding group "+groupuseraliasdic['group']+" to "+groupuseraliasdic['useralias']+".")
                RC=addgrouptouseralias(groupuseraliasdic['useralias'],groupuseraliasdic['group'],sudo_fact,logdic)
                print(RC['stdout'])    

            # Removing groups from useralias
            for groupuseraliasdic in sudo_module_removegroupfromuseralias:
                print("INF: Removing group "+groupuseraliasdic['group']+" from "+groupuseraliasdic['useralias']+".")
                RC=removegroupfromuseralias(groupuseraliasdic['useralias'],groupuseraliasdic['group'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding NOPASSWD to useralias and template
            for useraliastemplate in sudo_module_addnopasswdtouseraliastemplate:
                print("INF: Adding NOPASSWD to user_alias "+useraliastemplate['useralias']+" at "+useraliastemplate['template']+".")
                RC=addnopasswdtouseraliasattemplate(useraliastemplate['useralias'],useraliastemplate['cmd'],useraliastemplate['template'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing NOPASSWD form useralias and template
            for useraliastemplate in sudo_module_removenopasswdtouseraliastemplate:
                print("INF: removing NOPASSWD from user_alias "+useraliastemplate['useralias']+" at "+useraliastemplate['template']+".")
                RC=removenopasswdtouseraliasattemplate(useraliastemplate['useralias'],useraliastemplate['template'],sudo_fact)
                print(RC['stdout'])
                    
            # Adding NOPASSWD to useralias
            for useralias in sudo_module_addnopasswdtouseralias:
                print("INF: Adding NOPASSWD to user_alias "+useralias['useralias']+".")
                RC=addnopasswdtouseralias(useralias['useralias'],useralias['cmd'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing NOPASSWD from useralias
            for useralias in sudo_module_removenopasswdtouseralias:
                print("INF: removing NOPASSWD from user_alias "+useralias['useralias']+".")
                RC=removenopasswdfromuseralias(useralias['useralias'],useralias['cmd'],sudo_fact,logdic)
                print(RC['stdout'])


            # Adding CMD to useralias and template
            for useraliastemplate in sudo_module_addcmdtouseraliastemplate:
                print("INF: Adding CMD to user_alias "+useraliastemplate['useralias']+" at "+useraliastemplate['template']+".")
                RC=addcmdtouseraliasattemplate(useraliastemplate['useralias'],useraliastemplate['cmd'],useraliastemplate['template'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing CMD form useralias and template
            for useraliastemplate in sudo_module_removecmdtouseraliastemplate:
                print("INF: removing NOPASSWD from user_alias "+useraliastemplate['useralias']+" at "+useraliastemplate['template']+".")
                RC=removecmdfromuseraliasattemplate(useraliastemplate['useralias'],useraliastemplate['cmd'],useraliastemplate['template'],sudo_fact,logdic)
                print(RC['stdout'])

            # Adding CMD to useralias
            for cmduseralias in sudo_module_addcmdtouseralias:
                print("INF: Adding CMD "+cmduseralias['cmd']+" to user_alias "+cmduseralias['useralias']+".")
                RC=addcmdtouseralias(cmduseralias['useralias'],cmduseralias['cmd'],sudo_fact,logdic)
                print(RC['stdout'])

            # Removing CMD form useralias
            for cmduseralias in sudo_module_removecmdtouseralias:
                print("INF: removing CMD "+cmduseralias['cmd']+" from user_alias "+cmduseralias['useralias']+".")
                RC=removecmdfromuseralias(cmduseralias['useralias'],cmduseralias['cmd'],sudo_fact,logdic)
                print(RC['stdout'])
     
            
            # Processing report
            if sudo_handlercfg['report'] == True:
                print(sudo_fact)

        else:
            # Error Handling
            if (len(sudo_module_argumentsnotdetected)>0):
                print("ERR: Argument Error.")
            if (insuficientarguments==True):
                print("ERR: Insuficient arguments for directive.")
            sudo_handlercfg['cmdusage'] = True
            print('')
            #Processing unknwon arguments
            for uargu in sudo_module_argumentsnotdetected:
                print("ERR: Argument "+uargu+" not recognized.")
            print('')

    else:
        print("ERR: Sudo not installed")    
#Handling Help
if sudo_handlercfg['cmdusage'] == True:
    cmduse()
#------------------------------------------------------------------------------------------------------------
