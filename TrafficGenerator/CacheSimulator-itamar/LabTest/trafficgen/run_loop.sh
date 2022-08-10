#! /bin/bash
j=$(($1))
echo ""
for (( i=0; i<$j; i++ )); do
    sudo python3 traffic_gen.py --sleep 0 &
done
