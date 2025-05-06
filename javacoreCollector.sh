#Copyright IBM Corp. 2025 - 2025
#SPDX-License-Identifier: Apache-2.0

#!/bin/bash
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
    fi
done

# Validation
if [[ -z "$libertyPath" && -z "$javaPid" ]]; then
    echo "Error: You must provide either 'libertyPath' or 'javaPid'."
    echo "  ./javacoreCollector.sh libertyPath=/opt/ibm/liberty"
    echo "  ./javacoreCollector.sh javaPid=12345"
    exit 1
 fi

[ -z "$interval" ] && interval=5
[ -z "$count" ] && count=10

if [[ -n "$libertyPath" ]]; then
    echo "Liberty path provided: $libertyPath"
    #libertyPath=$libertyPath
else
    echo "Java PID provided: $javaPid and javacores count $count"
    for i in $(seq 1 $count); do
        echo "[$(date)] Generating javacore #$i..."
        kill -3 $javaPid
        if [ $i -lt $count ]; then
            sleep $interval
        fi
    done
fi

exit 1
