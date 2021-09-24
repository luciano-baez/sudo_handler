SUDOers Handler  (Ver 0.8 ) (cmd script and Ansible module)
===========================================================
* This is a python script to be called from your shell script and a python module to be added in your playbooks or Roles in Ansible Tower*


## Requirements
------------
- For scipting python3
- For use in your playbooks in ansile, just usual Ansible requirements.

Module Functions
----------------
*Current programmed functions.*

Example get report
 
```yaml
  - name: Sudo get report
    sudo_handler:
      state: report
```

Example to declare that we want the /etc/sudoers compliance without the "#includedir" directive
If the directive is present will be erased and will add one "#include" directive per file at /etc/sudoers.d directory
If the directive "#inlcudedir" isn't there, the module will do nothing.
```yaml
  - name: Removing include dir
    sudo_handler:
      fixincludedir: True

```

Example to declare an include (file template must be already at /etc/sudoers.d ), will not fail if the include already there.
if the attribute includestate is omitted, will asume the "state: present" Value.
```yaml
  - name: Sudo include file template
    sudo_handler:
      include: 010_STD_TMPSUDO
      state: present

```

Example to ensure the include file is the first include (file template must be already at /etc/sudoers.d ), will not fail if the include already there.
if the attribute includestate is omitted, will asume the "state: present" Value.

```yaml
  - name: Sudo include file template
    sudo_handler:
      include: 010_STD_TMPSUDO
      state: present
      first: True
```

Example to declare an include absense (only remove the include not the file), will not fail if the include aren't there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      include: 010_STD_TMPSUDO
      state: absent
```

Example to declare a user into an specific sudo file in an specific User_alias label, will not fail if the user is already there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      user: ar007310
      user_alias: IBM_SA_BAU_TMP
      include: 010_STD_TMPSUDO
      state: present
```

Example to declare the user absence form an specific sudo file in an specific User_alias label, will not fail if the user isn't there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      user: ar007310
      user_alias: IBM_SA_BAU_TMP
      include: 010_STD_TMPSUDO
      state: absent
```

Example to declare a group into an specific sudo file in an specific User_alias label, will not fail if the group is already there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      group: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      include: 010_STD_TMPSUDO
      state: present

```

Example to declare the group absence form an specific sudo file in an specific User_alias label, will not fail if the group isn't there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      group: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      include: 010_STD_TMPSUDO
      state: absent
```


This is experimental

Example to declare a user without specifying the sudo file in an specific User_alias label (will search in all sudo files), will not fail if the user is already there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      user: ar007310
      user_alias: IBM_SA_BAU_TMP
      state: present

```

Example to declare the group absence  without specifying the sudo file in an specific User_alias label, will not fail if the group isn't there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      user: ar007310
      user_alias: IBM_SA_BAU_TMP
      state: absent
```


Example to declare a group without specifying the sudo file in an specific User_alias label (will search in all sudo files), will not fail if the group is already there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      group: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      state: present

```

Example to declare the group absence  without specifying the sudo file in an specific User_alias label, will not fail if the group isn't there.
```yaml
  - name: Sudo include remove
    sudo_handler:
      group: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      state: absent
```

** Not Implemented yet **

Example to add a command to a user_alias.
```yaml
  - name: Add command to user_alias
    sudo_handler:
      cmd: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      state: present
```

Example to remove a command from a user_alias.
```yaml
  - name: Remove command from user_alias
    sudo_handler:
      cmd: tmpgroup
      user_alias: IBM_SA_BAU_TMP
      state: absent
```

Example to add nopasswd to a command in  user_alias.
```yaml
  - name: Add nopasswd to a command in user_alias
    sudo_handler:
      user_alias: IBM_SA_BAU_TMP
      cmd: tmpgroup
      setnopasswd: true
```
Example to remove nopasswd from a command in  user_alias.
```yaml
  - name: Remove nopasswd from command in user_alias
    sudo_handler:
      user_alias: IBM_SA_BAU_TMP
      cmd: tmpgroup
      setnopasswd: false
```



----------------------------------------------------------------------------------------------------------------------------

sudo_handler_cmd command
=========================
* This is a python program to handle sudoers files ant its includes
To implement this in a playbook you need to place the file sudo_handler.py in the library directory and the sudo_handler_lib.py on module_utils directory.

Author Information
------------------
Role and modules developed by Luciano Baez (lucianobaez@kyndryl.com or lucianobaez1@ibm.com), working for the GI-SVC-GBSE team.

