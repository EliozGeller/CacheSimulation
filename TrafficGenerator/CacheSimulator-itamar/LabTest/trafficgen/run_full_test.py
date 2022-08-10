#!/usr/bin/ python 

import os
import sys
import subprocess
import time
import argparse
import json

def main(args):
    switch_name = 'r-arch-sw18'
    output_dir = '/mtrsysgwork/oshabtai/work/trafficgen/CacheSimulator/LabTest/trafficgen/data/'
    bgu_script_path = '/mtrsysgwork/oshabtai/work/trafficgen/CacheSimulator/LabTest/switch_app/bgu_acl.py'
    ingress_int = ''
    test_params = {'threads':args.threads,
                    'threadinterpacketgap':args.sleep,
                    'cache_size':args.cache_size,
                    'num_dst':args.dest_num,
                    'aging_factor:':args.aging_factor,
                    'insertion_thresh':args.insertion_threshold
                    }
    assert(args.sleep==0)
    switch_ssh = f'admin@{switch_name}'
    switch_counters_log_path = f'{output_dir}/{args.name}_counters.txt'
    switch_acl_log_path_pre = f'{output_dir}/{args.name}_acl_dump_pre.txt'
    switch_acl_log_path_post = f'{output_dir}/{args.name}_acl_dump_after.txt'
    report_path = f'{output_dir}/{args.name}.json'

    cmd = f"mkdir -p {output_dir}"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error creating output dir'

    cmd = f"ssh {switch_ssh} sonic-clear counters"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error cleaning switch counters'
    
    cmd = f"ssh {switch_ssh} docker exec syncd sx_api_flex_acl_dump.py > {switch_acl_log_path_pre}"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error getting acl dump before execution'

    cmd = f"ssh {switch_ssh} docker cp {bgu_script_path} syncd:/"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,f'Error copying switch cache script: {cmd}'

    cmd = f"ssh {switch_ssh} docker exec syncd python bgu_acl.py --timeout 25 --insertion_threshold {args.insertion_threshold} --aging_factor {args.aging_factor} --cache_size {args.cache_size} &"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error copying switch cache script'

    time.sleep(2)
    cmd = f"./run_loop.sh {args.threads}"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error running traffic'
    time.sleep(30+args.threads*0.1)

    cmd = f"ssh {switch_ssh} show int counters > {switch_counters_log_path}"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error collecting switch counters'
    
    with open(switch_counters_log_path,'r') as f:
        lines =  f.readlines()
        
        transmitted = int((list(filter(lambda a: a!='',lines[4].split(' ')))[2]).replace(',',''))
        test_params['transmitted'] = transmitted
        hit = int((list(filter(lambda a: a!='',lines[5].split(' ')))[9]).replace(',',''))
        # print(list(filter(lambda a: a!='',lines[5].split(' '))))
        test_params['hit'] = hit
        miss = int((list(filter(lambda a: a!='',lines[9].split(' ')))[9]).replace(',',''))
        test_params['miss'] = miss
        test_params['hit_ratio'] = (hit/(transmitted+1))
        print(f'total sent:{transmitted}, hit_ratio {(hit/(transmitted+1))}')
    
    time.sleep(10)
    # ping to kill job on switch
    cmd = f"ping 1.45.99.23 -I ens7 -c1 -W1"
    rv = subprocess.call(cmd, shell=True)
    time.sleep(1)

    cmd = f"ssh {switch_ssh} docker exec syncd sx_api_flex_acl_dump.py > {switch_acl_log_path_post}"
    rv = subprocess.call(cmd, shell=True)
    assert(rv==0) ,'Error getting acl dump before execution'


    with open(report_path, 'w') as fp:
        json.dump(test_params, fp, indent=4)
    print (f'Done - report path: {report_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--name', dest='name',type=str,default='test')
    parser.add_argument('--cache_size', dest='cache_size',type=int, default=100,
                    help='entries in cache')
    parser.add_argument('--aging_factor', dest='aging_factor', default=0.99,type=float,
                    help='cache aging factor')
    parser.add_argument('--insertion_threshold', dest='insertion_threshold', default=1.5,type=float,
                    help='cache insertion_threshold')
                    
    
    parser.add_argument('--threads', dest='threads',type=int, default=10,
                    help='simultanious sender threads')
    parser.add_argument('--dest_num', dest='dest_num',type=int, default=4000,
                    help='unique dest')
    parser.add_argument('--sleep', dest='sleep', default=0,type=float,
                    help='interpacket gap [sec]')

    parser.add_argument('-v', dest='verbose', action='store_const',
                    const=True, default=False,
                    help='show ip, packets per dest')
    # parser.add_argument('-v', dest='verbose', action='store_const',
    #                 const=True, default=False,
    #                 help='show ip, packets per dest')

    args = parser.parse_args()
    main(args)
