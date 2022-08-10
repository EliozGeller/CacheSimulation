from python_sdk_api.sx_api import *

SWID = 0
CACHE_TRAP_ID = SX_TRAP_ID_ACL_MIN+1

def host_ifc_open(handle):
    ''' Opening fd for traps '''
    trap_fd = new_sx_fd_t_p()
    rc = sx_api_host_ifc_open(handle, trap_fd)
    if rc != SX_STATUS_SUCCESS:
        print("Failed to open host_ifc trap_fd, rc=[%d] " % (rc))
        sys.exit(errno.EACCES)
    return trap_fd


def host_ifc_close(handle, fd):
    ''' Closing host ifc '''
    trap_fd = new_sx_fd_t_p()
    sx_fd_t_p_assign(trap_fd, fd)

    rc = sx_api_host_ifc_close(handle, trap_fd)
    if rc != SX_STATUS_SUCCESS:
        print("Failed to close host_ifc trap_fd, rc=[%d] " % (rc))
        sys.exit(errno.EACCES)


def host_ifc_trap_group_handle(handle, cmd, trap_group):
    ''' SET or UNSET trap group '''
    trap_group_attr_p = new_sx_trap_group_attributes_t_p()
    trap_group_attr = sx_trap_group_attributes_t()
    trap_group_attr.prio = 1
    # trap_group_attr.truncate_mode = SX_TRUNCATE_MODE_DISABLE
    # trap_group_attr.truncate_size = 0
    trap_group_attr.truncate_mode = SX_TRUNCATE_MODE_ENABLE
    trap_group_attr.truncate_size = 48
    trap_group_attr.control_type = SX_CONTROL_TYPE_DEFAULT
    trap_group_attr.is_monitor = False
    trap_group_attr.add_timestamp = False
    sx_trap_group_attributes_t_p_assign(trap_group_attr_p, trap_group_attr)

    rc = sx_api_host_ifc_trap_group_ext_set(handle, cmd, SWID, trap_group, trap_group_attr_p)
    if rc != SX_STATUS_SUCCESS:
        print("sx_api_host_ifc_trap_group_ext_set failed, [cmd = %d, rc = %d]" % (cmd, rc))
        sys.exit(errno.EACCES)


def host_ifc_trap_id_set_handle(handle, cmd, trap_id, trap_group):
    ''' SET/UNSET trap id association to the relevant trap group '''
    trap_key_p = new_sx_host_ifc_trap_key_t_p()
    trap_key_p.type = HOST_IFC_TRAP_KEY_TRAP_ID_E
    trap_key_p.trap_key_attr.trap_id = trap_id

    trap_attr_p = new_sx_host_ifc_trap_attr_t_p()
    trap_attr_p.attr.trap_id_attr.trap_group = trap_group

    if cmd == SX_ACCESS_CMD_SET:
        trap_attr_p.attr.trap_id_attr.trap_action = SX_TRAP_ACTION_SET_FW_DEFAULT
    else:
        trap_attr_p.attr.trap_id_attr.trap_action = SX_TRAP_ACTION_DISCARD

    rc = sx_api_host_ifc_trap_id_ext_set(handle, cmd, trap_key_p, trap_attr_p)
    if rc != SX_STATUS_SUCCESS:
        print("sx_api_host_ifc_trap_id_ext_set failed, [cmd = %d, rc = %d]" % (cmd, rc))
        sys.exit(errno.EACCES)


def host_ifc_trap_id_register_handle(handle, cmd, trap_id, user_channel, fd):
    ''' REGISTER/DEREGISTER trap id association to the relevant user channel '''
    user_channel_p = new_sx_user_channel_t_p()

    if cmd == SX_ACCESS_CMD_REGISTER:
        user_channel = sx_user_channel_t()
        user_channel.type = SX_USER_CHANNEL_TYPE_FD
        user_channel.channel.fd = copy_sx_fd_t_p(fd)

    sx_user_channel_t_p_assign(user_channel_p, user_channel)
    rc = sx_api_host_ifc_trap_id_register_set(handle, cmd, SWID, trap_id, user_channel_p)
    if rc != SX_STATUS_SUCCESS:
        sys.exit(errno.EACCES)

    if cmd == SX_ACCESS_CMD_REGISTER:
        user_channel = sx_user_channel_t_p_value(user_channel_p)

    return user_channel


def trap_ext_configuration_example(handle, trap_id, trap_group):
    fd = host_ifc_open(handle)
    host_ifc_trap_group_handle(handle, SX_ACCESS_CMD_SET, trap_group)
    host_ifc_trap_id_set_handle(handle, SX_ACCESS_CMD_SET, trap_id, trap_group)
    user_channel = host_ifc_trap_id_register_handle(handle, SX_ACCESS_CMD_REGISTER, trap_id, None, fd)
    return fd


def create_fdb_trap_entry():
    mac_list_p = new_sx_fdb_uc_mac_addr_params_t_arr(1)
    data_cnt_p = new_uint32_t_p()
    uint32_t_p_assign(data_cnt_p, 1)
    mac_addr = ether_addr(NVnet.PERMISSIVE_LIDv2)

    mac_entry = sx_fdb_uc_mac_addr_params_t()
    mac_entry.mac_addr = mac_addr
    mac_entry.fid_vid = 1          # Filtering Identifier, VID for static MAC
    # mac_entry.log_port = PORT
    mac_entry.entry_type = SX_FDB_UC_STATIC
    mac_entry.action = SX_FDB_ACTION_TRAP
    sx_fdb_uc_mac_addr_params_t_arr_setitem(mac_list_p, SWID, mac_entry)

    rc = sx_api_fdb_uc_mac_addr_set(handle, SX_ACCESS_CMD_ADD, SWID, mac_list_p, data_cnt_p)
    data_cnt = uint32_t_p_value(data_cnt_p)
    print("sx_api_fdb_uc_mac_addr_set added %d enties, rc: %d " % (data_cnt, rc))

def create_and_register_host_ifc(handle):
    trap_id = CACHE_TRAP_ID
    trap_group = 12
    return trap_ext_configuration_example(handle, trap_id, trap_group)

def recv_pkt(fd_p, sma):
    # recv parameters
    pkt_size = 2000
    pkt_size_p = new_uint32_t_p()
    uint32_t_p_assign(pkt_size_p, pkt_size)
    pkt = new_uint8_t_arr(pkt_size)
    recv_info_p = new_sx_receive_info_t_p()
    rc = sx_lib_host_ifc_recv(fd_p, pkt, pkt_size_p, recv_info_p)
#    print("[recv] recv on fd")
    if rc != 0:
        print("exit with error, rc %d" % rc)
        exit(rc)
    # print("[recv] Packet recv info:")
    if recv_info_p.is_lag:
        print("Source LAG 0x%x" % recv_info_p.source_lag_port)
#   print("Source log port 0x%x" % recv_info_p.source_log_port)
#   print("Recv trap id: %d" % recv_info_p.trap_id)
    pkt_size = uint32_t_p_value(pkt_size_p)
#   print("Packet size: %d" % pkt_size)

    if (pkt_size > 0):
        pkt_bytes = []
        for iii in range(0, pkt_size):
            pkt_bytes.append(uint8_t_arr_getitem(pkt, iii))

    sma.enqueue([str(bytearray(pkt_bytes)), recv_info_p.source_log_port])
    return

