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
#

#   -Ver 0.8 : May 10 2021
#           - Recode the Ansible module
#

ANSIBLE_METADATA = {
    'metadata_version': '0.8',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: sudo_handler

short_description: Module to handle SUDO (/etc/sudoers) in Kyndryl/IBM under Unix/linux platforms

version_added: "1"

description:
    - "This is module provides SUDO handle"

options:
    action:
        description:
            - This provided the behavior of the module (report, state)
            If is set to "report", will provide the SUDO facts.
            If is set to "state", will check the other atributes in order to set the desired state.
        required: true

    fixincludedir: 
        description:
            - This is the flag to fix the #includedir non compliance directive (Values: True, False)
            (If is true, and the #includedir is present, will be removed, and will be added one #include directive by file at /etc/sudoers.d directory)
        required: false

    include:
        description:
            - This is the include file, to remove or insert ( the file could be only the file name or the full path file name)
            (this will be only needed by actions addinclude and removeinclude)
        required: false

    includestate: 
        description:
            - This is desired state of the include file, (present,absent)
            If no specified this atribute "present" state will be asumed
        required: false

    sudofile:
        description:
            - This is the filename to be used with "user:" or "group:" attribute
        required: false

    user_alias: 
        description:
            - This is the "User_alias" label asociated to the "sudofile:" attribute, in order to be used with "user:" or "group:" attribute
        required: false

    user: 
        description:
            - This is the user to be added or removed from the "User_alias" at the  "sudofile:" 
        required: false

    userstate: 
        description:
            - Is the desired state for the "user:" attribute. if ommited "present" will be asumed
        required: false

    group: 
        description:
            - This is the group to be added or removed from the "User_alias" at the  "sudofile:" 
        required: false

    groupstate: 
        description:
            - Is the desired state for the "group:" attribute. if ommited "present" will be asumed
        required: false


extends_documentation_fragment:
    - To be executed on Jump Host and Ansible TOWER

author:
    - Luciano Báez (@lucianoabez) on Kyndryl slack and on IBM slack (@lucianoabez1)
'''

EXAMPLES = '''
# Get information
- name: Get the SUDO information
  sudo_handler:
    state: report

# Fix (remove) #includedir directive
- name: Remove #includedir directive 
  sudo_handler:
    fixincludedir: True

# Add an include template 
- name: Add include 
  sudo_handler:
    action: state
    include: 010_STD_TMPSUDO
    state: present


# Remove an include template 
- name: Remove include 
  sudo_handler:
    include: 010_STD_TMPSUDO
    state: absent

# Remove an include template 
- name: Remove include 
  sudo_handler:
    include: 010_STD_TMPSUDO
    user_alias:
    user:
    state: prsent

'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the SUDO module generates
    type: str
    returned: always
'''

import os
import pwd
import grp
import platform
import subprocess
import json
import shutil
import datetime

# Importing all functions from repo lib sudo_handler_lib
from ansible.module_utils.sudo_handler_lib import *

#Needed to be usable as Ansible Module
from ansible.module_utils.basic import AnsibleModule


#Module Global Variables 

sudo_fact={}
sudoincludedirfix_res=['#includedir fixed succesfully','Directive #includedir not present','Replacement try got error','sudoers file inconsistent']
# 0 includedir fixed succesfully
# 1 Directive #includedir not present
# 2 replacement try got error
# 3 sudoers file inconsistent

sudoinserttemplate_res=['Insertion succesfull.','Template does not exists.','Sudoers file does not exists.',
            'Directive #includedir implemented.','Sudoers File inconsistent.','include template already exists.']
# 0 Insertion succesfull
# 1 Template doesen't exists
# 2 sudoers file doesen't exists
# 3 Directive #includedir implemented
# 4 Sudoers File inconsistent
# 5 include template already exists

sudoremovetemplate_res=['Removal succesfull','Template does not exists','Sudoers file does not exists','Directive #includedir implemented',
'sudoers file inconsistent','Template is not included']
# 0 Removal succesfull
# 1 Template doesen't exists
# 2 sudoers file doesen't exists
# 3 Directive #includedir implemented
# 4 sudoers file inconsistent
# 5 template is not included


sudoinsertuser_res=['User added succesfully.','File does not exsists.','user_alias directive not present.',
    'user_alias label not present.','Label already there.','User does not exists.']
# 0 User added succesfully
# 1 File does not exsists
# 2 user_alias directive not present
# 3 user_alias label not present
# 4 Label already there
# 5 User does not exists


sudoremovetuser_res=['User removed succesfully.','File does not exsists.','user_alias directive not present.',
    'user_alias label not present.','Label not there .']
# 0 User removed succesfully
# 1 File does not exsists
# 2 user_alias directive not present
# 3 user_alias label not present
# 4 Label not there 

sudoinsertgroup_res=[' Group added succesfully.','File does not exsists.','user_alias directive not present.',
    'user_alias label not present.','Label already there.','group does not exists.']
# 0 Group added succesfully
# 1 File does not exsists
# 2 user_alias directive not present
# 3 user_alias label not present
# 4 Label already there
# 5 group does not exists


sudoremovegroup_res=['Group removed succesfully.','File does not exsists.','user_alias directive not present.',
'user_alias label not present.','Label not there.']
# 0 Group removed succesfully
# 1 File does not exsists
# 2 user_alias directive not present
# 3 user_alias label not present
# 4 Label not there



def sudoershandle(options):
    SUDOHANDLERESULT={}
    return SUDOHANDLERESULT
    

def run_module():
    #------------------------------------------------------------------------------------------------------------
    # This are the arguments/parameters that a user can pass to this module
    # the action is the only one that is required

    module_args = dict(
        #action=dict(type='str', required=True),
        state=dict(type='str', default='present'),
        include=dict(type='str', required=False),
        sudofile=dict(type='str', required=False, default=""),
        first=dict(type='bool', required=False, default=False),
        fixincludedir=dict(type='bool', required=False, default=False),
        user=dict(type='str', required=False, default=""),
        group=dict(type='str', required=False, default=""),
        user_alias=dict(type='str', required=False, default=""),
        cmnd_alias=dict(type='str', required=False, default=""),
        setnopasswd=dict(type='bool', required=False, default=False),
        cmd=dict(type='str', required=False, default=""),

        # Non documented option For troubleshoot
        log=dict(type='bool', required=False, default=False)
    )
    

    # Acepted values for "state" 
    #   -report                 = Provides a report without any change
    
    #------------------------------------------------------------------------------------------------------------
    # This is the dictionary to handle the module result
    result = dict(
        changed=False,
        failed=False,
        skipped=False,
        original_message='',
        message=''
    )

    # This is the dictionary to handle the logs
    logdic = dict(
        log=False,
        logfile='/tmp/sudo_handler'
    )

    # The AnsibleModule object will be our abstraction working with Ansible this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module supports check mode
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Define Vaariables to use 
    sudo_process=1
    sudoers_file=str('/etc/sudoers')
    sudo_module_first=False
    sudo_module_log=False
    sudo_module_fixincludedir=False
    sudo_module_setnopasswd=False
    sudo_module_include=str('')
    # the include file fullpath 
    sudo_module_include_file=str('')
    sudo_module_include_file_exists=False
    sudo_module_state=str('')
    sudo_module_user=str('')
    sudo_module_group=str('')
    sudo_module_user_alias=str('')
    sudo_module_cmnd_alias=str('')
    sudo_module_cmd=str('')
    sudo_module_backup=False

    #

    # Dectecting arguments
    #try:
    #    sudo_module_action=str(module.params['action'])
    #except KeyError:
    #    sudo_process=0


    # Provide the the requested action as the original Message
    CR="\n"
    result['original_message'] = module.params
    #result['message'] = 'goodbye',
    ModuleExitMessage = ''
    ModuleExitChanged = False
    ModuleExitFailed= False

    # <processing parameters>
    try:
        sudo_module_state=str(module.params['state'])
    except KeyError:
        sudo_module_state='report'

    if sudo_module_state != 'report' and sudo_module_state != 'report_ep':
        #Process when state is present or absent
        # Detects if fixincludedir in order to remove '#includedir' directive
        try:
            sudo_module_fixincludedir=module.params['fixincludedir']
        except:
            sudo_module_fixincludedir=False
        
        try:
            sudo_module_first=module.params['first']
        except:
            sudo_module_first=False

        try:
            sudo_module_setnopasswd=module.params['setnopasswd']
        except:
            sudo_module_setnopasswd=False

        #Detecting the include file (could be with full path or without path, adn will asume that are at /etc/sudoers.d )
        try:
            sudo_module_include=str(module.params['include'])
        except:
            sudo_module_include=str('')
        if sudo_module_include.upper() == 'NONE':
            sudo_module_include=''
        if sudo_module_include != '':
            sudo_module_include_file="/etc/sudoers.d/"+sudo_module_include
            
        try:
            sudo_module_user=str(module.params['user'])
        except:
            sudo_module_user=str('')
        if sudo_module_user == 'None':
            sudo_module_user=''        

        try:
            sudo_module_group=str(module.params['group'])
        except:
            sudo_module_group=str('')
        if sudo_module_group == 'None':
            sudo_module_group=''

        try:
            sudo_module_user_alias=str(module.params['user_alias'])
        except:
            sudo_module_user_alias=str('')
        if sudo_module_user_alias.upper() == 'NONE':
            sudo_module_user_alias=''
        
        try:
            sudo_module_cmnd_alias=str(module.params['cmnd_alias'])
        except:
            sudo_module_cmnd_alias=str('')
        if sudo_module_cmnd_alias.upper() == 'NONE':
            sudo_module_cmnd_alias=''
        
        try:
            sudo_module_cmd=str(module.params['cmd'])
        except:
            sudo_module_cmd=str('')
        if sudo_module_cmd.upper() == 'NONE':
            sudo_module_cmd=''

        try:
            sudo_module_log=module.params['log']       
        except:
            sudo_module_log=False
        if sudo_module_log==True:
            logdic['log']=sudo_module_log
            logdic['logfile']="/var/log/sudo_handler_debug"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".log"
            #logging.basicConfig( filename = logdic[logfile],filemode = 'w',level = logging.DEBUG,format = '%(asctime)s - %(levelname)s: %(message)s',\
            #         datefmt = '%m/%d/%Y %I:%M:%S %p' )
            #logging.debug("Starting of the file1"+logdic[logfile]+" (sudo_handler)")

        #try:
        #    sudo_module_sudofile=str(module.params['sudofile'])
        #except:
        #    sudo_module_sudofile=str('')
        #if sudo_module_sudofile == 'None':
        #    sudo_module_sudofile=''

        
        if ( os.path.isfile(sudoers_file) == False):
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "Sudoers file not present." + CR   
        if sudo_module_include != '':
            if ( os.path.isfile(sudo_module_include_file) == False):
                sudo_module_include_file_exists=False
                sudo_process==0
                ModuleExitMessage = ModuleExitMessage + "Sudoers file "+sudo_module_include_file+" not present." + CR   
        if sudo_module_include == '' and sudo_module_user_alias == '' and sudo_module_fixincludedir == False:
            # If there are no include or no user alias, there is nothing to do
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no include or no user alias." + CR   
        
        if sudo_module_include == '' and sudo_module_first==True:
            # A template couldn't placed in the first position
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no include to be placed at the first position." + CR   

        if (sudo_module_include == '' and sudo_module_user_alias == '' ) and (sudo_module_user=='' or sudo_module_group == '') and sudo_module_fixincludedir == False:
            # could not process a group or a user if there is no sudo_module_include or sudo_module_user_alias specified
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no include or user_alias to handle user or group." + CR   

        if (sudo_module_include == '' and sudo_module_user_alias != '' ) and (sudo_module_user=='' and sudo_module_group == '') and (sudo_module_cmd == ''):
            # could not process a group or a user if there is no sudo_module_include or sudo_module_user_alias specified
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no user or group to asociate to  user_alias "+sudo_module_user_alias+"." + CR   

        if sudo_module_cmnd_alias == '' and sudo_module_user_alias == '' and sudo_module_setnopasswd == True:
            # If a cmnd_alias not specified we couldn't place the nopasswd directive
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no cmnd_alias or user_alias to set NOPASSWD." + CR   
        
        if sudo_module_cmnd_alias == '' and sudo_module_user_alias == '' and sudo_module_cmd != '':
            # A it a cmdalias or cmd not specified we couldn't place the nopasswd directive
            sudo_process==0
            ModuleExitMessage = ModuleExitMessage + "There is no cmnd_alias or user_alias to handle a cmd ." + CR   

    # </processing parameters>

        
    # if the user is working with this module in only check mode we do not want to make any changes to the environment, 
    # just return the report with no modifications
    # if module.check_mode:
    #     sudo_process=1
    #     result['original_message'] = module.params['check_mode']

    if sudo_process==1:
        # Getting sudo fats
        sudo_fact=getsudo_fact(logdic)

        #Processing the report
        if sudo_module_state == 'report':
            result['changed']=False
            if len(sudo_fact) > 0:
                #result['message']=sudo_fact
                ModuleExitMessage=sudo_fact
            else:
                result['failed'] = True
                #result['message']="No SUDO detected."
                ModuleExitMessage="No SUDO detected."

        elif sudo_module_state == 'report_ep':
            result['changed']=False
            if len(sudo_fact) > 0:
                #result['message']=getsudopermissions(sudo_fact,logdic)
                ModuleExitMessage=getsudopermissions(sudo_fact,logdic)
            else:
                result['failed'] = True
                #result['message']="No SUDO detected."
                ModuleExitMessage="No SUDO detected."

        else:
            #fixing the #includedir directive (not affected if the state is present or absent)
            if sudo_module_fixincludedir == True:
                rc=sudoincludedirfix(sudo_module_backup,sudo_fact,logdic)
                if rc['rc'] == 0:
                    result['changed'] = True
                else:
                    result['changed'] = False
                    result['failed'] = True
                    if (rc['rc']==1):
                        # 1 Directive #includedir not present
                        result['failed'] = False
                ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

            if sudo_module_state == 'present':
                if sudo_module_include != '':
                    #Processing include
                    if sudo_module_first==True:
                        # Ensure that the include module is at the first position
                        rc=placefirsttemplate(sudo_module_backup,sudoers_file,sudo_module_include,sudo_fact,logdic)
                        if rc['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3 or rc['rc']==5):
                                # 3 Directive #includedir implemented
                                # 5 include template already exists
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR    
                    else:
                        # Ensure that the include module is there
                        rc=sudoinserttemplate(sudo_module_backup,sudoers_file,sudo_module_include,sudo_fact,logdic)
                        if rc['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3 or rc['rc']==5):
                                # 3 Directive #includedir implemented
                                # 5 include template already exists
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                    # processing users and groups    
                    if sudo_module_user != '' and sudo_module_user_alias != "" and sudo_module_include_file != "":
                        rc=addusertoincludeuseralias(sudo_module_include_file,sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    if sudo_module_user != '' and sudo_module_user_alias != "" and sudo_module_include_file == "":
                        rc=addusertouseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                        
                    if sudo_module_group != '' and sudo_module_user_alias != "" and sudo_module_include_file != "":
                        rc=addgrouptoincludeuseralias(sudo_module_include_file,sudo_module_user_alias,sudo_module_group,sudo_fact,logdic)
                        #ddgrouptoincludeuseralias(sudofile,useralias,group,SUDODICTIONARY,sudologdic):
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    if sudo_module_group != '' and sudo_module_user_alias != "" and sudo_module_include_file == "":
                        rc=addgrouptouseralias(sudo_module_user_alias,sudo_module_group,sudo_fact,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    #Adding sudo_module_cmd command to sudo_module_user_alias 
                    if sudo_module_user_alias != '' and sudo_module_cmd != ""  :
                        rc=addcmdtouseraliasattemplate(sudo_module_user_alias,sudo_module_cmd,sudo_module_include_file,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3):
                                # 3 sudocmd already there
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                    #adding NOPASSWD for user_alias
                    if sudo_module_user_alias != ""  and  sudo_module_include_file != "" and sudo_module_cmd != ""  and sudo_module_setnopasswd==True:                        
                        rc=addnopasswdtouseraliasattemplate(sudo_module_user_alias,sudo_module_cmd,sudo_module_include_file,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 NOPASSWD already there 
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                    #removing NOPASSWD for user_alias
                    if sudo_module_user_alias != ""  and  sudo_module_include_file != "" and sudo_module_setnopasswd==False and sudo_module_cmd != "" :
                        rc=removenopasswdtouseraliasattemplate(sudo_module_user_alias,sudo_module_cmd,sudo_module_include_file,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 NOPASSWD not there 
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR                    
                    
                else:    
                    
                    # processing users without include and with user_alias
                    if sudo_module_user != '' and sudo_module_user_alias != "" :
                        rc=addusertouseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)                    
                        #ModuleExitMessage = ModuleExitMessage + "Processing:"+sudo_module_user_alias+" with user "+ sudo_module_user+ CR
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    # processing group without include and with user_alias
                    if sudo_module_group != '' and sudo_module_user_alias != "" :
                        #rc=addusertouseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        rc=addgrouptouseralias(sudo_module_user_alias,sudo_module_group,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    
                    #Adding  sudo_module_cmd to sudo_module_user_alias
                    #if sudo_module_user_alias != '' and sudo_module_cmd != "" :

                    #Adding sudo_module_cmd command to sudo_module_user_alias  command_alias
                    if sudo_module_user_alias != '' and sudo_module_cmd != ""  :
                        rc=addcmdtouseralias(sudo_module_user_alias,sudo_module_cmd,sudo_fact,logdic)
                        #rc=removecmdfromuseralias(sudo_module_user_alias,sudo_module_cmd,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==2):
                                # 2 sudocmd already there
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    #Adding NOPASSWD to sudo_module_cmd command at sudo_module_user_alias 
                    if sudo_module_user_alias != '' and sudo_module_cmd != "" and sudo_module_setnopasswd == True :
                        rc=addnopasswdtouseralias(sudo_module_user_alias,sudo_module_cmd,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3):
                                # 3 NOPASSWD already there 
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    #Removing sudo_module_cmd command from sudo_module_user_alias 
                    if sudo_module_user_alias != '' and sudo_module_cmd != "" and sudo_module_setnopasswd == False :
                        rc=removenopasswdfromuseralias(sudo_module_user_alias,sudo_module_cmd,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3):
                                # 3 NOPASSWD not there 
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    

            if sudo_module_state == 'absent':
                if sudo_module_include !='':
                    rc=sudoremovetemplate(sudoers_file,sudo_module_include,sudo_fact,logdic)
                    if rc['rc'] == 0:
                        result['changed'] = True
                        result['failed'] = False
                    else:
                        result['changed'] = False
                        result['failed'] = True
                        if (rc['rc']==5):
                            # 5 include template isent there
                            result['failed'] = False
                    ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                    #Processing the user and group absent
                    if sudo_module_user != '' and sudo_module_user_alias != "" and sudo_module_include_file != "":
                        rc=removeuserfromincludeuseralias(sudo_module_include_file,sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "ERR: Label "+user+" not there (rc=4)."
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    if sudo_module_user != '' and sudo_module_user_alias != "" and sudo_module_include_file == "":
                        rc=removeuserfromuseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "ERR: Label "+user+" not there (rc=4)."
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                    if sudo_module_group != '' and sudo_module_user_alias != "" and sudo_module_include_file != "":
                        rc=removegroupfromincludeuseralias(sudo_module_include_file,sudo_module_user_alias,sudo_module_group,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "ERR: Label "+group+" not there (rc=4)."
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                                        
                    #Removing sudo_module_cmd command to sudo_module_user_alias 
                    if sudo_module_user_alias != '' and sudo_module_cmd != ""  :
                        rc=removecmdfromuseraliasattemplate(sudo_module_user_alias,sudo_module_cmd,sudo_module_include_file,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==3):
                                # 3 sudocmd not there
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                else:
                    # processing users without include and with user_alias
                    if sudo_module_user != '' and sudo_module_user_alias != "" :
                        rc=removeuserfromuseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    # processing group without include and with user_alias
                    if sudo_module_group != '' and sudo_module_user_alias != "" :
                        #rc=addusertouseralias(sudo_module_user_alias,sudo_module_user,sudo_fact,logdic)
                        rc=removegroupfromuseralias(sudo_module_user_alias,sudo_module_group,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==4):
                                # 4 "WAR: Label "+user+" already there (rc=4).",
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    #Removing sudo_module_cmd command from sudo_module_user_alias 
                    if sudo_module_user_alias != '' and sudo_module_cmd != ""  :
                        rc=removecmdfromuseralias(sudo_module_user_alias,sudo_module_cmd,sudo_fact,logdic)
                        if rc['rc']==0:
                            result['changed'] = True
                            result['failed'] = False
                        else:
                            result['changed'] = False
                            result['failed'] = True
                            if (rc['rc']==2):
                                # 2 sudocmd not there
                                result['failed'] = False
                        ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                    
                    

        # End of declarative state parsing
        #---------------------------------------------------------------------------------------------------------------------------

    result['message'] = ModuleExitMessage
    # Returning the result
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()