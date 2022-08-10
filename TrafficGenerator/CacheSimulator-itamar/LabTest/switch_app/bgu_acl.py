#!/usr/bin/env python
"""
Cache mechanism for spectrum2
"""
import sys
import socket
import struct
import errno
import signal
import time
from python_sdk_api.sx_api import *
import bgu_acl_trap_utils as trap_utils
import argparse
from insertion_alg import InsertionAlg

parser = argparse.ArgumentParser(description='smart cache app')
parser.add_argument('--timeout',default=60,type=int, help='timeout [sec]')
parser.add_argument('--insertion_threshold',default=1.5,type=float, help='cache insertion threshold')
parser.add_argument('--aging_factor',default=0.99,type=float, help='cache insertion aging factor')
parser.add_argument('--cache_size',default=300,type=int, help='cache size')


args = parser.parse_args()
"""
improvments:
2. use C instead of python
3. activity bit instead of fifo eviction
"""
# globals:
assert(args.cache_size>1)
assert(args.aging_factor<=1)
CACHE_ENTRIES = args.cache_size
incoming_traffic_port = 0x16500 # labelport 2 - vm 22
CACHE_MISS_PORT= 0x16900 # labelport 3 
CACHE_HIT_PORT= 0x17900 # labelport 7
# C pointers
direction = None
acl_list = []
hit_pbs_id = None
miss_pbs_id = None
key_handle = None
region_id = None
acl_id = None
acl_id_arr = None
group_id = None
host_fd = None
rule_arr = None
offsets_list = None
rule = None
current_entry = 0
# cache related
cache_offset2ip = ['']*CACHE_ENTRIES # offset to ip
cache_ip2offset = {} # ip to offset

print("[+] opening sdk")
rc, handle = sx_api_open(None)
print(("sx_api_open handle:0x%x , rc %d " % (handle, rc)))
if (rc != SX_STATUS_SUCCESS):
    print("Failed to open api handle.\nPlease check that SDK is running.")
    sys.exit(rc)


def assign_sx_ip_addr_v4(struct_field,addr):
    # ip_addr = sx_ip_addr_t()
    struct_field.version = SX_IP_VERSION_IPV4
    struct_field.addr.ipv4.s_addr =  struct.unpack('>I', socket.inet_pton(socket.AF_INET, addr))[0]


def region_create(key_handle, region_size):
    " This function creates acl region  "
    region_id_p = new_sx_acl_region_id_t_p()

    rc = sx_api_acl_region_set(handle,
                               SX_ACCESS_CMD_CREATE,
                               key_handle,
                               0,
                               region_size,
                               region_id_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to create region"

    region_id = sx_acl_region_id_t_p_value(region_id_p)
    print("Created region %d, rc: %d" % (region_id, rc))
    return region_id


def region_destroy(region_id):
    " This function destroys acl region  "
    region_id_p = new_sx_acl_region_id_t_p()
    sx_acl_region_id_t_p_assign(region_id_p, region_id)

    rc = sx_api_acl_region_set(handle,
                               SX_ACCESS_CMD_DESTROY,
                               0,
                               0,
                               0,
                               region_id_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to create region"
    print("Destroyed region %d, rc: %d" % (region_id, rc))


def key_create():
    " This function creates flex acl key and returns handle to it  "
    key_handle_p = new_sx_acl_key_type_t_p()
    key_arr = new_sx_acl_key_t_arr(1)
    sx_acl_key_t_arr_setitem(key_arr, 0, FLEX_ACL_KEY_DIP)

    rc = sx_api_acl_flex_key_set(handle,
                                 SX_ACCESS_CMD_CREATE,
                                 key_arr,
                                 1,
                                 key_handle_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to create flex key"

    key_handle = sx_acl_key_type_t_p_value(key_handle_p)
    print("Created key %d, rc: %d" % (key_handle, rc))
    return key_handle


def key_destroy(key_handle):
    " This function destroy  flex acl key "
    key_handle_p = new_sx_acl_key_type_t_p()
    sx_acl_key_type_t_p_assign(key_handle_p, key_handle)

    key_arr = new_sx_acl_key_t_arr(1)
    sx_acl_key_t_arr_setitem(key_arr, 0, 0)

    rc = sx_api_acl_flex_key_set(handle,
                                 SX_ACCESS_CMD_DELETE,
                                 key_arr,
                                 0,
                                 key_handle_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to destroy flex key"
    print("Destroyed key %d, rc: %d" % (key_handle, rc))


def acl_create(region_id, direction):
    " This function creates flex acl and returns acl id  "
    acl_id_p = new_sx_acl_id_t_p()
    acl_region_group = sx_acl_region_group_t()
    acl_region_group.regions.acl_packet_agnostic.region = region_id

    rc = sx_api_acl_set(handle,
                        SX_ACCESS_CMD_CREATE,
                        SX_ACL_TYPE_PACKET_TYPES_AGNOSTIC,
                        direction,
                        acl_region_group,
                        acl_id_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to create acl"

    acl_id = sx_acl_id_t_p_value(acl_id_p)
    print("Created acl %d, rc: %d" % (acl_id, rc))
    return acl_id


def acl_destroy(acl_id, region_id):
    " This function destroy  flex acl key "
    acl_id_p = new_sx_acl_id_t_p()
    sx_acl_id_t_p_assign(acl_id_p, acl_id)

    acl_region_group = sx_acl_region_group_t()
    acl_region_group.regions.acl_packet_agnostic.region = region_id

    rc = sx_api_acl_set(handle,
                        SX_ACCESS_CMD_DESTROY,
                        SX_ACL_TYPE_PACKET_TYPES_AGNOSTIC,
                        0,
                        acl_region_group,
                        acl_id_p)
    if (SX_STATUS_SUCCESS != rc):
        print("Error - Failed to destroy acl%d , rc = %d" % (acl_id, rc))
    else:
        print("Destroyed acl %d, rc: %d" % (acl_id, rc))
    delete_sx_acl_id_t_p(acl_id_p)


# def group_create(acl_id_arr, acls_num, direction):
#     " This function creates flex acl and returns acl id  "
#     group_id_p = new_sx_acl_id_t_p()

#     rc = sx_api_acl_group_set(handle,
#                               SX_ACCESS_CMD_CREATE,
#                               direction,
#                               acl_id_arr,
#                               0,
#                               group_id_p)
#     assert SX_STATUS_SUCCESS == rc, "Failed to create group"

#     rc = sx_api_acl_group_set(handle,
#                               SX_ACCESS_CMD_SET,
#                               direction,
#                               acl_id_arr,
#                               acls_num,
#                               group_id_p)
#     assert SX_STATUS_SUCCESS == rc, "Failed to add acls to group"

#     group_id_internal = sx_acl_id_t_p_value(group_id_p)
#     print("Created group %d, rc: %d" % (group_id_internal, rc))
#     for i in range(0, acls_num):
#         print("acl id = %d " % sx_acl_id_t_arr_getitem(acl_id_arr, i))

#     delete_sx_acl_id_t_p(group_id_p)
#     return group_id_internal


# def group_destroy(group_id):
#     " This function destroy  flex acl key "
#     group_id_p = new_sx_acl_id_t_p()
#     sx_acl_id_t_p_assign(group_id_p, group_id)
#     acl_id_arr = new_sx_acl_id_t_arr(5)
#     sx_acl_id_t_arr_setitem(acl_id_arr, 0, group_id)

#     direction = 0
#     rc = sx_api_acl_group_set(handle,
#                               SX_ACCESS_CMD_DESTROY,
#                               direction,
#                               acl_id_arr,
#                               0,
#                               group_id_p)
#     if (SX_STATUS_SUCCESS != rc):
#         print("Error: Failed to destroy group",group_id)

#     print("Destroyed group %d, rc: %d" % (group_id, rc))
#     delete_sx_acl_id_t_p(group_id_p)



def pbs_create(ports):
    pbs_id_p = new_sx_acl_pbs_id_t_p()
    pbs_entry = sx_acl_pbs_entry_t()
    pbs_entry.entry_type = SX_ACL_PBS_ENTRY_TYPE_UNICAST
    pbs_entry.port_num = len(ports)
    pbs_entry.log_ports = new_sx_port_log_id_t_arr(len(ports))
    for i, port in enumerate(ports):
        sx_port_log_id_t_arr_setitem(pbs_entry.log_ports, i, port)
    rc = sx_api_acl_policy_based_switching_set(handle,
                                               SX_ACCESS_CMD_ADD,
                                               0,
                                               pbs_entry,
                                               pbs_id_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to create pbs, rc = %d" % (rc)
    return sx_acl_pbs_id_t_p_value(pbs_id_p)
 
 
def pbs_delete(pbs_id):
    pbs_id_p = new_sx_acl_pbs_id_t_p()
    sx_acl_pbs_id_t_p_assign(pbs_id_p, pbs_id)
    pbs_entry = sx_acl_pbs_entry_t()
    rc = sx_api_acl_policy_based_switching_set(handle,
                                               SX_ACCESS_CMD_DELETE,
                                               0,
                                               pbs_entry,
                                               pbs_id_p)
    assert SX_STATUS_SUCCESS == rc, "Failed to delete pbs %d, rc = %d" % (pbs_id, rc)
 


def make_rule(ip='1.1.80.1',default=False):
    rule = sx_flex_acl_flex_rule_t()
    rule.valid = 1
    sx_lib_flex_acl_rule_init(0, 10, rule)
    
    key_desc = sx_flex_acl_key_desc_t()
    key_desc.key_id = FLEX_ACL_KEY_DIP
    if default:
        assign_sx_ip_addr_v4(key_desc.key.dip,ip)
        assign_sx_ip_addr_v4(key_desc.mask.dip,'0.0.0.0')
    else:
        assign_sx_ip_addr_v4(key_desc.key.dip,ip)
        assign_sx_ip_addr_v4(key_desc.mask.dip,'255.255.255.255')

    #rule.key_desc_list_p = new_sx_flex_acl_key_desc_t_arr(5)
    sx_flex_acl_key_desc_t_arr_setitem(rule.key_desc_list_p, 0, key_desc)
    rule.key_desc_count = 1

    # action1 = sx_flex_acl_flex_action_t()
    # action1.type = SX_FLEX_ACL_ACTION_SET_TTL
    # action1.fields.action_set_ttl.ttl_val = 100
    # action2 = sx_flex_acl_flex_action_t()
    # action2.type = SX_FLEX_ACL_ACTION_SET_VLAN
    # action2.fields.action_set_vlan.cmd = SX_ACL_FLEX_SET_VLAN_CMD_TYPE_PUSH
    # action2.fields.action_set_vlan.vlan_id = 6
    if default:
        rule.action_list_p = new_sx_flex_acl_flex_action_t_arr(2)
        action1 = sx_flex_acl_flex_action_t()
        action1.type = SX_FLEX_ACL_ACTION_TRAP
        action1.fields.action_trap.action = SX_ACL_TRAP_ACTION_TYPE_TRAP
        action1.fields.action_trap.trap_id = trap_utils.CACHE_TRAP_ID

        action2 = sx_flex_acl_flex_action_t()
        action2.type = SX_FLEX_ACL_ACTION_PBS
        action2.fields.action_pbs.pbs_id = miss_pbs_id
        sx_flex_acl_flex_action_t_arr_setitem(rule.action_list_p, 0, action1)
        sx_flex_acl_flex_action_t_arr_setitem(rule.action_list_p, 1, action2)
        rule.action_count = 2
    
    else:
        rule.action_list_p = new_sx_flex_acl_flex_action_t_arr(1)
        action1 = sx_flex_acl_flex_action_t()
        action1.type = SX_FLEX_ACL_ACTION_PBS
        action1.fields.action_pbs.pbs_id = hit_pbs_id
        sx_flex_acl_flex_action_t_arr_setitem(rule.action_list_p, 0, action1)
        rule.action_count = 1
    return rule


def delete_rule(rule):
    # print('delete_sx_flex_acl_flex_action_t_arr')
    # delete_sx_flex_acl_flex_action_t_arr(rule.action_list_p)
    # print('rule deinit')
    sx_lib_flex_acl_rule_deinit(rule)
    # print('deleted rule')
    return rule


def rule_set(local_rule, region_id, offset, access):
    ''' This function sets rule, where access is the choose for adding or deleting rule
    SX_ACCESS_CMD_SET - set the Rule
    SX_ACCESS_CMD_DELETE - remove the rule'''
    
    rule_arr = new_sx_flex_acl_flex_rule_t_arr(1)
    # default_rule = make_rule(default=True)
    # rule_example = make_rule(ip='1.1.80.1',default=False)
    sx_flex_acl_flex_rule_t_arr_setitem(rule_arr, 0, local_rule)
    # sx_flex_acl_flex_rule_t_arr_setitem(rule_arr, 1, default_rule)

    offsets_list = new_sx_acl_rule_offset_t_arr(1)
    sx_acl_rule_offset_t_arr_setitem(offsets_list, 0, offset)
    # sx_acl_rule_offset_t_arr_setitem(offsets_list, 1, CACHE_ENTRIES)

    rc = sx_api_acl_flex_rules_set(handle,
                                   access,
                                   region_id,
                                   offsets_list,
                                   rule_arr,
                                   1)
    
    if (SX_STATUS_SUCCESS != rc):
        print("Error-  Failed to change rule offset",offset)
        return -1

    if access == SX_ACCESS_CMD_SET:
        print("Added rule offset  %d, to region %d,  rc: %d" % (offset, region_id, rc))
    else:
        print("Deleted rule offset  %d, region %d,  rc: %d" % (offset, region_id, rc))

    # delete_sx_flex_acl_key_desc_t_arr(rule.key_desc_list_p)
    # delete_sx_flex_acl_flex_action_t_arr(rule.action_list_p)

    # TODO make function deinit rule to prevent memory leak: delete_sx_flex_acl_flex_action_t_arr(default_rule.action_list_p)
    delete_sx_flex_acl_flex_rule_t_arr(rule_arr)
    delete_sx_acl_rule_offset_t_arr(offsets_list)

def deinit_cahce_app():
    print("deinit cache app - started")
    global cache_offset2ip
    rc = sx_api_acl_port_bind_set(handle,
                                      SX_ACCESS_CMD_UNBIND,
                                      incoming_traffic_port,
                                      acl_id)
    print("port %d unbound from  acl %d  rc: %d" % (incoming_traffic_port, acl_id, rc))

    
    
    default_rule = make_rule(default=True)
    for i in range(CACHE_ENTRIES):
        ip = cache_offset2ip[i]
        if ip != '':
            rule_set(default_rule,region_id, i, SX_ACCESS_CMD_DELETE)
    # delete default rule
    rule_set(default_rule,region_id, CACHE_ENTRIES, SX_ACCESS_CMD_DELETE) 
    acl_destroy(acl_list[0], region_id)
    for pbs_id in [hit_pbs_id,miss_pbs_id]:
        pbs_delete(pbs_id=pbs_id)
    region_destroy(region_id)
    key_destroy(key_handle)
    trap_utils.host_ifc_close(handle, host_fd)
    print("deinit cache app - Done")
    sx_api_close(handle)


def init_cache_app():
    global direction
    global acl_list
    global hit_pbs_id
    global miss_pbs_id
    global key_handle
    global region_id
    global acl_id
    global acl_id_arr
    global host_fd

    direction =  SX_ACL_DIRECTION_INGRESS
    hit_pbs_id = pbs_create([CACHE_HIT_PORT])
    miss_pbs_id = pbs_create([CACHE_MISS_PORT])

    host_fd = trap_utils.create_and_register_host_ifc(handle=handle)

    key_handle = key_create()
    region_id = region_create(key_handle, region_size=CACHE_ENTRIES+1)

    acl_id = acl_create(region_id, direction)
    acl_list.append(acl_id)
    
    print("init cache app done")


def signal_handler(sig, frame):
    deinit_cahce_app()
    sys.exit(0)

def recv_pkt(fd_p,bgu_insertion_alg):#, sma):
    """ prepre rules """
    global rule_arr
    global offsets_list
    # global rule
    global current_entry
    global cache_ip2offset
    global cache_offset2ip
    
    
    """ handle new packet """
    pkt_size = 200 # 2000 
    pkt_size_p = new_uint32_t_p()
    uint32_t_p_assign(pkt_size_p, pkt_size)
    pkt = new_uint8_t_arr(pkt_size)
    recv_info_p = new_sx_receive_info_t_p()
    rc = sx_lib_host_ifc_recv(fd_p, pkt, pkt_size_p, recv_info_p) # TODO can be recv list, TODO truncate

    if rc != 0:
        print("exit with error, rc %d" % rc)
        exit(rc)
        # print("[recv] Packet recv info:")
    if recv_info_p.is_lag:
        print("Source LAG 0x%x" % recv_info_p.source_lag_port)
    
    pkt_size = uint32_t_p_value(pkt_size_p)
    #   print("Packet size: %d" % pkt_size)

    if (pkt_size > 34):
        ip = '.'.join([str(uint8_t_arr_getitem(pkt,iii)) for iii in range(30, 34)])
        # header = [str(uint8_t_arr_getitem(pkt,iii)) for iii in range(80)]
        # print (header)
            # pkt_bytes.append(uint8_t_arr_getitem(pkt, iii))
        # print ("got trapped packet: ",pkt_bytes)
        # print("ip is: ",pkt_bytes[38:42])
        # print ("got trapped packet, ip: ",ip)

        """ add new rule """
        # sma.enqueue([str(bytearray(pkt_bytes)), recv_info_p.source_log_port])
        # print("\n ip:",ip,"cache:\n",cache_ip2offset)
        if ip not in cache_ip2offset.keys():
            insert_to_cache = bgu_insertion_alg.process_packet(ip)
            if insert_to_cache:
        # if cache_ip2offset.get(ip,True):
            # print("making rule for: ",ip)
                rule = make_rule(ip=ip) # TODO use globals and only set ip
                sx_flex_acl_flex_rule_t_arr_setitem(rule_arr, 0, rule)
                sx_acl_rule_offset_t_arr_setitem(offsets_list, 0, current_entry)
                rc = sx_api_acl_flex_rules_set(handle,
                                            SX_ACCESS_CMD_SET,
                                            region_id,
                                            offsets_list,
                                            rule_arr,
                                            1)
                delete_rule(rule)
                if SX_STATUS_SUCCESS != rc:
                    print( "Failed to add rule offset, %d, ip: %s "%(current_entry,ip))
                else:
                    # print( "add rule to offset, %d, ip: %s "%(current_entry,ip))
                    # evicted_ip = cache_offset2ip[current_entry]
                    # if  evicted_ip != '':
                    #     # print("evicting"+evicted_ip)
                    #     cache_ip2offset.pop(evicted_ip)
                    cache_ip2offset.pop(cache_offset2ip[current_entry],None)
                    cache_ip2offset[ip] = current_entry
                    cache_offset2ip[current_entry] = ip
                    current_entry += 1
                    current_entry = current_entry % CACHE_ENTRIES
            # else:
                # print('ignoring, ip already in cache',ip,' offset: ',cache_ip2offset[ip])
    # print('delete pkt_size_p')
    delete_uint32_t_p(pkt_size_p)
    # print('delete pkt')
    delete_uint8_t_arr(pkt)
    # print('delete recv_info_p')
    delete_sx_receive_info_t_p(recv_info_p)
    # print('done recive')
    return

def main(args):
    bgu_insertion_alg = InsertionAlg(args.aging_factor,args.insertion_threshold)
    init_cache_app() # TODO recored entries in json so it can be deinited !
    signal.signal(signal.SIGINT, signal_handler)
    # the rule hard coded now with action discard
    default_rule = make_rule(default=True)
    rule_set(default_rule,region_id, CACHE_ENTRIES, SX_ACCESS_CMD_SET)
    global rule_arr
    global offsets_list
    global rule
    rule_arr = new_sx_flex_acl_flex_rule_t_arr(1)   # TODO - size to 1?
    offsets_list = new_sx_acl_rule_offset_t_arr(1) # TODO - size to 1?
    rule = make_rule(ip='1.1.80.1',default=False)
    
    rc = sx_api_acl_port_bind_set(handle,
                                  SX_ACCESS_CMD_BIND,
                                  incoming_traffic_port,
                                  acl_id)
    print("Port %d is bound to acl %d  rc: %d" % (incoming_traffic_port, acl_id, rc))

    # set_50_rules(region_id)
    sx_api_dbg_generate_dump(handle, "/tmp/flex_acl_dump_log")
    # get_50_rules(region_id)
    
    t_start = time.time()
    t_end = t_start + args.timeout
    
    # if args.deinit:
    while time.time()<t_end:
        try:
            recv_pkt(host_fd,bgu_insertion_alg)#, sma)
            # time.sleep(0.1)
        except Exception as e:
            print("Error: ", e)
            deinit_cahce_app()        
            sys.exit(1)
    
    deinit_cahce_app()


    print("finished")


if __name__ == "__main__":
    main(args)
