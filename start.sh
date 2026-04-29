#!/bin/sh
source /root/miniconda3/etc/profile.d/conda.sh && conda activate xhb_py39
base_dir=`pwd`
profile="xhb-prod"
app_name="xhb_backend"
server_port=28001
if [ ! -f ${app_name}/app/main.py ]; then
  echo "请将本脚本放在与 ${app_name} 同级目录后再执行"
  exit 1
fi

PID=`ps -ef | grep app.main |grep "profile=${profile}" | grep -v grep | awk '{print $2}'`;
if [ ${PID}x != x ]; then
    echo "Shutting down ${app_name} PID[$PID]..."
    kill $PID ;
fi

for i in {1..10}; do
  PID=`ps -ef | grep app.main |grep "profile=${profile}" | grep -v grep | awk '{print $2}'`;
  if [ ${PID}x != x ]; then
    echo "Waiting ${i} seconds..."
    sleep 1
  else
    break
  fi
done

PID=`ps -ef | grep app.main |grep "profile=${profile}" | grep -v grep | awk '{print $2}'`;
if [ ${PID}x != x ];then
    echo "Shutting down force ${app_name} PID[$PID]..."
    kill -9 $PID ;
fi
cd ${app_name}
#nohup python -m app.main --profile=$profile &
nohup python -m app.main --profile=$profile > /dev/null 2>&1  &
cd ..
sleep 2
echo "启动结果："
echo `ps -ef | grep ${app_name}/main |grep "profile ${profile}" | grep -v grep`
echo "curl http://127.0.0.1:${server_port}/"
echo `curl http://127.0.0.1:${server_port}/`
