ScratchToCatrobat
=================
A tool for converting Scratch projects into Catrobat programs.

Catrobat is a visual programming language and set of creativity tools for smartphones, tablets, and mobile browsers. Catrobat programs can be written by using the Catroid programming system on Android phones and tablets, using Catroid, or Catty for iPhones.

For more information oriented towards developers please visit our [developers page](http://developer.catrobat.org/).

# License

[License](http://developer.catrobat.org/licenses) of our project (mainly AGPL v3).

The Following License Header should be used for all python and java source files.

## License Header for Python source files
<pre lang="python"><code>
#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
</code></pre>

## License Header for Java source files
<pre lang="java"><code>
/*
 * ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
 * Copyright (C) 2013-2015 The Catrobat Team
 * (http://developer.catrobat.org/credits)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * An additional term exception under section 7 of the GNU Affero
 * General Public License, version 3, is available at
 * http://developer.catrobat.org/license_additional_term
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 */
</code></pre>

#Setup for Debian (Wheezy 7.x):

* First of all you have to refresh your package lists via:
```sh
sudo apt-get update
```
* Now install python (if not already installed) (minimum allowed version 2.7):
```sh
sudo apt-get install python
```
* Install sox via aptitude (needed for sound conversion):
```sh
sudo apt-get install sox
```
* Jython 2.7 requires java version 1.7 or later. To determine the currently installed java version run the following command on your shell:
```sh
java -version
```
* Now, download jython e.g. by using wget (at least version 2.7):
```sh
wget http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7.0/jython-installer-2.7.0.jar
```
* To install jython issue the following command:
```sh
sudo java -jar jython-installer-2.7.0.jar --console
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
Congratulations! You successfully installed Jython 2.7 to directory /usr/jython.
```

* Install git via apt-get:
```sh
sudo apt-get install git
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
chmod +x ./run
```

* You can now start the conversion process, e.g. by issuing the following command:
```sh
./run http://scratch.mit.edu/projects/10205819/ ./data/output
```

Here, the first parameter tells the script which scratch project should be converted.
The second parameter (optional) represents the (absolute or relative) path to the output folder where the converted Catrobat program is finally stored.

For more details on how to use the script, please execute the following line:
```sh
./run --help
```
