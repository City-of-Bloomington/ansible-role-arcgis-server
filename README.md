# ansible-role-arcgis-server
Ansible role for setting up Ubuntu to host ArcGIS Server

This role does not actually install and set up ArcGIS server.  Much of that installation has to happen in the web interface.  So, this really just prepares the linux machine so that ArcGIS Server will install cleanly.

## ArcGIS User
The ArcGIS installers assume that the user running the installer is the user that the software will run as.  This means we need to create the ArcGIS system user as a regular user with a shell and a password.  Also, it is most convenient to set the ArcGIS user's home directory to the installation directory.

This is essentially what the Ansible role sets up:

`useradd -m -s /bin/bash -d /srv/arcgis arcgis`

## Installing ArcGIS Server
Copy the ArcGIS Server installation tarball across to the server, along with the license key file.  I usually put them in /usr/local/src.  You'll need to untar them an run the "Setup" scripts.

Again, this must be done as the arcgis user....

```bash
su arcgis
cd /usr/local/src/ArcGISServer
./Setup -v -m silent -l Yes -a /usr/local/src/ArcGISServer_XXX.prvc -d /srv
```

### Starting at Boot
The ArcGIS installation includes a systemd service file that can be installed.  You cannot create symlinks to the file, because of file permissions.  You must copy the service file to /etc/systemd/system.

Also, the file permissions on the service file that ArcGIS ships are too restrictive for systemd.  You must make the service file world readable for systemd to use the service.

```bash
sudo -i
cd /srv/arcgis/server/framework/etc/scripts
cp arcgisserver.service /etc/systemd/system
chmod 664 /etc/systemd/system/arcgisserver.service
exit

sudo systemctl enable arcgisserver
sudo service arcgisserver start
```
## Installing ArcGIS WebAdaptor

The tomcat8 user must:
* have a shell
* have a password
* have a home directory
* have permission to write to it's home


The WebAdaptor is a tomcat war, but it relies on stuff installed on the hard drive as well.

It is critical that, the install script is able to write to $HOME/.webadaptor. (where $HOME is tomcat8's home directory) This is the directory where the Tomcat webapp will store all it's configuration data.  The installer WILL NOT error out if it cannot write to this directory.  In fact, the attempts to write to this directory are never logged, even in verbose mode.


To run the install script, you must `su` up to tomcat8.  You cannot do this with sudo, as it will preserve your environment, instead of using tomcat8's.

After installation, once everything is working, we'll remove tomcat8's password and shell.

### Install the WAR
The installer will create /srv/arcgis/webadaptor.  In there, you'll find the war file to be deployed.  Copy it to tomcat's webapps directory.

*IMPORTANT* Carefully watch catalina.out and deal with any and all WARNINGs that show up.  These are indicitve of something wrong with the installation, even if none of the installers errored out.


### Create Apache configuration
We like to have Apache front for Tomcat, because it's much easier to deal with SSL keys that way.  Even though this server only has this one web application, we need to create a minimal Apache conf for it.  Here, we just send all traffic directly over to Tomcat.

We do not even need an Alias or Directory, since we're not going to attempt to have Apache serve files directly out of the arcgis webapp.

/etc/apache2/sites-enabled/conf.d/arcgis-webadaptor.conf
```apache
JkMount /arcgis/* ajp13_worker
```

### WebAdaptor configuration
Once you can navigate to https://arcgis-server/arcgis/webadaptor you can run the webadaptor configuration.  This will connect the web adaptor to our ArcGIS Server, which right now, also happens to be running on the same server.

This can be run by any user you like.  The script navigates to the various web sites to do the configuration.  The web sites do not allow this to be done, except at localhost, and we are not installing a GUI.

```bash
cd /srv/arcgis/webadaptor/java/tools

./configurewebadaptor.sh -m server \
-w https://arcgis-server.bloomington.in.gov/arcgis/webadaptor \
-g https://arcgis-server.bloomington.in.gov:6443 \
-u arcgis -p SECRET_PASSWORD \
-a true
```
