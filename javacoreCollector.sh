#!/bin/bash

#Copyright IBM Corp. 2025 - 2025
#SPDX-License-Identifier: Apache-2.0

echo "executing javacore collector script"
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
    fi
done

# Validation
if [[ -z "$libertyPath" && -z "$javaPid" ]]; then
    echo "You must provide either libertyPath or javaPid arguments:"
    echo "  ./javacoreCollector.sh libertyPath=/opt/ibm/liberty"
    echo "  ./javacoreCollector.sh javaPid=12345"
    echo "Optional arguments:"
    echo ""
    echo "   count - number of Javacores (default: 10)"
    echo "   interval - interval in seconds to gather javacores (default: 30)"
    echo "   server - server name for Liberty"
    echo ""
    echo "Examples:"
    echo "   ./javacoreCollector.sh libertyPath=/opt/ibm/liberty server=clm count=5 interval=60"
    echo "   ./javacoreCollector.sh javaPid=12345 count=5 interval=60"
    exit 1
 fi

[ -z "$interval" ] && interval=30
[ -z "$count" ] && count=10
[ -z "$server" ] && server=""

if [[ -n "$libertyPath" ]]; then
    echo "Liberty path provided: $libertyPath"
    export WLP_USER_DIR=$libertyPath
else
    echo "Java PID provided: $javaPid and javacores count $count"
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
cp -vfr $libertyPath/servers/clm/javacore*.txt javacore_data
cp -vfr $libertyPath/servers/clm/verbosegc.txt* javacore_data
tar -czvf javacores.tar.gz javacore_data
echo "Javacores and verbose gc data saved to javacores.tar.gz archive."
echo "Deleting javacore_data dir"
rm -rfv javacore_data

exit 1
