#! /bin/sh

### BEGIN INIT INFO
# Provides:				HaltRebootService
# Required-Start:		$remote_fs $syslog
# Required-Stop:		
# Default-Start:		2 3 4 5
# Default-Stop:			
# Short-Description:	RPi Halt and Reboot Daemon
# Description:			Halt and Reboot Daemon for Raspberry PI Using P5 I/O GPIO28(IN) [Btn], GPIO29(OUT) [LED-GREEN], GPIO29(OUT) [LED-RED]
### END INIT INFO



#Phyton Script Location & Parameter
DAEMON_NAME=HaltRebootDaemon

SCRIPT_DIR=/usr/local/bin/$DAEMON_NAME
SCRIPT_NAME=$DAEMON_NAME.py

DAEMON=$SCRIPT_DIR/$SCRIPT_NAME

DAEMON_ARGS="--log /var/log/$DAEMON_NAME.log"

DAEMON_USER=root

PIDFILE=/var/run/$DAEMON_NAME.pid



# Exit if the package is not installed
if [ -x "$DAEMON" ] 
then
	echo "" >> /dev/null
else
	echo "file $DAEMON not exist or permission error!"
	exit 0
fi


# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.2-14) to ensure that this file is present
# and status_of_proc is working.
. /lib/lsb/init-functions



do_start () {
log_daemon_msg "Starting $DAEMON_NAME"
echo "$DAEMON_ARGS"
start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_ARGS > /dev/null
log_end_msg $?

}

do_stop () {
log_daemon_msg "Stopping $DAEMON_NAME"
start-stop-daemon --stop --pidfile $PIDFILE --retry 10 > /dev/null
log_end_msg $?
rm -f $PIDFILE > /dev/null
}


case "$1" in
 
start|stop)
do_${1}
;;
 
restart|reload|force-reload)
do_stop
do_start
;;
 
status)
status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
;;

*)
echo "Usage: /etc/init.d/$DAEMON_NAME.sh {start|stop|restart|status}"
exit 1
;;
 
esac
exit 0 
