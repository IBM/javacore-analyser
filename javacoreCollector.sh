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

for i in $(seq 1 $count); do
    echo "[$(date)] Generating javacore #$i..."
    if [[ -n "$libertyPath" ]]; then
        echo "command: $libertyPath/wlp/bin/server javadump $server"
        "$libertyPath"/wlp/bin/server javadump $server
    else
        kill -3 $javaPid
    fi
    if [ $i -lt $count ]; then
        sleep $interval
    fi
done

exit 1
