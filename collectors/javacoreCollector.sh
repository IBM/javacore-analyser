#!/bin/bash

#Copyright IBM Corp. 2025 - 2025
#SPDX-License-Identifier: Apache-2.0

echo "executing javacore collector script"
current=`date`
echo "Current time: $current"
for arg in "$@"; do
    if [[ $arg == libertyPath=* ]]; then
        libertyPath="${arg#libertyPath=}"
    elif [[ $arg == javaPid=* ]]; then
        javaPid="${arg#javaPid=}"
    elif [[ $arg == count=*  ]]; then
        count="${arg#count=}"
    elif [[ $arg == interval=* ]]; then
        interval="${arg#interval=}"
    elif [[ $arg == server=* ]]; then
        server="${arg#server=}"
    elif [[ $arg == javacoresDir=* ]]; then
        javacoresDir="${arg#javacoresDir=}"
    fi
done

# Validation
validated=false
if [ -n "${libertyPath}" ] && [ -n "${server}" ]; then
    validated=true
elif [ -n "${javaPid}" ] && [ -n "${javacoresDir}" ]; then
    validated=true
else
    validated=false
fi
if [ "$validated" = false ]; then
    echo "Invalid arguments provided."
    echo "You must provide either libertyPath with server name or javaPid with javacores dir arguments:"
    echo "  ./javacoreCollector.sh libertyPath=/opt/ibm/liberty server=server_name"
    echo "  ./javacoreCollector.sh javaPid=12345 javacoresDir=/path/to/javacores"
    echo ""
    echo "Optional arguments:"
    echo ""
    echo "   count - number of Javacores (default: 10)"
    echo "   interval - interval in seconds to gather javacores (default: 30)"
    echo ""
    echo "Examples:"
    echo "   ./javacoreCollector.sh libertyPath=/opt/ibm/liberty server=clm count=5 interval=60"
    echo "   ./javacoreCollector.sh javaPid=12345 javacoresDir=/my_app/javacores count=5 interval=60"
    exit 1
 fi

[ -z "$interval" ] && interval=30
[ -z "$count" ] && count=10


if [[ -n "$libertyPath" ]]; then
    echo "Liberty path provided: $libertyPath"
    javacoresDir="$libertyPath/servers/$server/"
    export WLP_USER_DIR=$libertyPath
    verbosegcDir="$libertyPath/servers/$server"
else
    echo "Java PID provided: $javaPid"
    verbosegcDir=
fi

mkdir javacore_data
echo "Ulimit" >> javacore_data/ulimit.txt
ulimit -a>>javacore_data/ulimit.txt

for i in $(seq 1 $count); do

    file_name=javacore_data/iteration${i}.txt
    echo "Writing current system resources usage to $file_name"
    echo "List of processes">>"$file_name"
    ps aux>>"$file_name"
    echo "Memory usage">>"$file_name"
    free -k>>"$file_name"
    echo "Disk usage">>"$file_name"
    df -h>>"$file_name"

    echo "[$(date)] Generating javacore #$i..."
    if [[ -n "$libertyPath" ]]; then
        echo "Running following command: $libertyPath/wlp/bin/server javadump $server"
        "$libertyPath"/wlp/bin/server javadump $server
    else
        kill -3 $javaPid
    fi
    if [ $i -lt $count ]; then
        sleep $interval
    fi
done


echo "Creating archive file"
#copy all javacore files newer than script starting time
cp -vf `find $javacoresDir javacore*.txt -newermt "$current"` javacore_data
#copy verbose gc files if they exist
if [ -n "$verbosegcDir" ]; then
    cp -vf $libertyPath/servers/$server/verbosegc.txt* javacore_data
fi
tar -czvf javacores.tar.gz javacore_data
echo "Javacores and verbose gc data saved to javacores.tar.gz archive."
echo "Deleting javacore_data dir"
rm -rfv javacore_data

exit 1
