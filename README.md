ScratchToCatrobat
=================
A tool for converting Scratch projects into Catrobat programs.

# License
[License](http://developer.catrobat.org/licenses) of our project (mainly AGPL v3).

#Setup for Debian (Wheezy 7.x):

* First of all you have to refresh your package lists via:
```sh
sudo aptitude update
```
* Now install python (if not already installed) (minimum allowed version 2.7):
```sh
sudo aptitude install python
```
* Install sox via aptitude (needed for sound conversion):
```sh
sudo aptitude install sox
```
* Jython 2.7 requires java version 1.7 or later. To determine the currently installed java version run following command on your shell:
```sh
java -version
```
* Now download jython e.g. via wget (at least version 2.7):
```sh
wget http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7-b3/jython-installer-2.7-b3.jar
```
* To install jython run following line:
```sh
sudo java -jar jython-installer-2.7-b3.jar --console
[...]
Please select your language [E/g] >>> E
Do you want to read the license agreement now ? [y/N] >>> y
[...]
Do you accept the license agreement ? [Y/n] >>> Y
The following installation types are available:
1. All (everything, including sources)
2. Standard (core, library modules, demos and examples, documentation)
3. Minimum (core)
9. Standalone (a single, executable .jar)
Please select the installation type [ 1 /2/3/9] >>> 2
Do you want to install additional parts ? [y/N] >>> N
Do you want to exclude parts from the installation ? [y/N] >>> N
Please enter the target directory >>> /usr/jython
Unable to find directory /usr/jython, create it ? [Y/n] >>> Y
Please enter the java home directory (empty for using the current java runtime) >>>
[...]
Please confirm copying of files to directory /usr/jython [Y/n] >>> Y
[...]
Do you want to show the contents of README ? [y/N] >>> y
[...]
Please press Enter to proceed >>>
Congratulations! You successfully installed Jython 2.7b3 to directory /usr/jython.
```

* Install git via aptitude:
```sh
sudo aptitude install git
```
* Clone this repository:
```sh
git clone https://github.com/Catrobat/ScratchToCatrobat.git
```
* Go to the ScratchToCatrobat directory:
```sh
cd ScratchToCatrobat
```
* Make the converter script executable:
```sh
chmod +x ./converter
```
* Create output directory for your converted projects:
```sh
mkdir output
```
* The installation is finished now. The converter can now be started by calling the converter-script, e.g. via:
```sh
./converter http://scratch.mit.edu/projects/10205819/ ./output
```
