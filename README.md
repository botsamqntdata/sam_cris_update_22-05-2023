# SAM

SAM.
Requirement:
Anaconda 3-5.2.0 - https://repo.anaconda.com/archive/.

**Uninstalling Anaconda**: https://docs.anaconda.com/anaconda/install/uninstall/
- Windows:

Uninstall anaconda using Control Panel. Delete old folder of SAM.
- Mac: add `sudo` before command if got issue **_permission denied_**.

Open terminal.

Install the Anaconda-Clean package
```
conda install anaconda-clean
anaconda-clean --yes
```
Remove your entire Anaconda directory

`rm -rf ~/anaconda3` or `rm -rf ~/anaconda`

Delete old folder of SAM.

**Installation**

Start on Windows:

- Install Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html. Note that Win 7 user ver 12.2.

1. Download the appropriate Instant Client packages for your platform. All installations require the Basic package.
2. Unzip the packages into a single directory such as C:\oracle\instantclient_19_12
3. Add this directory to the PATH environment variable (https://www.computerhope.com/issues/ch000549.htm). If you have multiple versions of Oracle libraries installed, make sure the new directory occurs first in the path. Restart any terminal windows or otherwise make sure the new PATH is used by your applications.

- run setup.bat -> START.bat.

Start on Mac:

- Change the Default Shell to Bash on macOS Catalina 
1. Open Terminal window and run the following command: `chsh -s /bin/bash`
2. Close the Terminal to activate.

- Create environment
```
conda create -n sam python=3.6.5 --y
source activate sam
```

- Install Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html.

1. Download the Basic Package (ZIP).
2. Unzip the packages into folder `lib` in your Anaconda's directory, default path is `/Users/$USER/anaconda3/envs/sam/lib`/

- Install packages:
1. Run each line below to install cmake and dlib
```
pip install cmake==3.18.2.post1
pip install dlib==19.22.1
```
2. Install required software to build wheel for dlib: click yes and wait for the process to complete.
3. Install other packages: `pip install -r mac_requirements.txt`

- Copy credentials.json to folder `config` and util.pyc to folder `sam`.

- Run SAM:
```
source activate sam
python debugger.py
```
**Issue & Fix**
1. 'import cv2' fails because numpy.core.multiarray fails to import

Re-install numpy with version 1.18.5: `pip install numpy==1.18.5`

2. Webcam black screen

See https://stackoverflow.com/questions/29645278/webcam-open-cv-python-black-screen. Current solution:
```
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

3. cx_Oracle error. DPI-1047: Cannot locate a 64-bit Oracle Client library

See https://oracle.github.io/odpi/doc/installation.html for help. Note that Win 7 uses ver 12.2, others use ver 19.


