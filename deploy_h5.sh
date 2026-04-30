#!/usr/bin/env bash
set -eu pipefail
current_dir=`pwd`
target_dir="/Users/liwei/shared/projects/jhl/xiaohebao/frontend_h5"
cd $target_dir
pnpm build
rsync -avz --delete --progress ${target_dir}/dist qingren@152.136.236.144:/data/www/xhb.juxin.pro/
cd $current_dir