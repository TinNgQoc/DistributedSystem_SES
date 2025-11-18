#!/bin/bash
# Run 15 SES processes in parallel, log output to demo_logs/pid_<id>.txt

mkdir -p demo_logs
for i in {0..14}
do
  python3 run_node.py $i > demo_logs/pid_$i.txt 2>&1 &
done

echo "Started 15 SES processes."

echo "To check running processes:"
echo "  ps aux | grep run_node.py"

echo "To kill a process (example: PID 1234):"
echo "  kill 1234"

echo "To stop all SES processes:"
echo "  pkill -f run_node.py"
