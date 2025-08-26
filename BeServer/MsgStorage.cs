namespace BeServer;

public static class MsgStorage
{
    // PING: '{"m":"ping","ts":1756191187}'
    // AUTH: '{"m":"status","subsystem":"auth","error":0,"status":"approved","client_token":"ZEOKPFPFEVYSSBGRFFP5AS2QDV65J5KU73YGGNF2OV5REYDWSSDA"}'
    // POLY: '{"m":"policy","id":0,"ts":1756191187,"folders":{"extra_folders":"remove_from_client","items":[],"preferences":{}},"scripts":{},"advanced_settings":{"rate_limit_local_peers":true,"folder_defaults.use_tracker":true,"folder_defaults.lan_discovery_mode":3,"use_synctrash_folder":true,"folder_defaults.known_hosts":"","folder_defaults.delete_unknown_files":false,"notify_file_edit_conflict_time_diff":0,"recheck_locked_files_interval":600,"download_priority":0,"lan_encrypt_data":true,"max_file_size_for_versioning":1000,"folder_rescan_interval":86400,"sync_trash_ttl":30,"transfer_job_unused_files_cleanup_timeout":0,"history_time_limit":30,"bind_port":3839,"bind_interface":"","use_only_bind_interface":false,"tracker_mode":"lb","overwrite_changes":1,"peer_queue_factor":"20.0","events_logging_level":5,"advanced_preallocate":false,"agent_resources_update_interval":60,"agent_status_update_interval":"1","events_logging_filter":"0,0,0,12,0;960,267386880,3264,0,0,0,0","unbuffered_io":false,"ignore_symlinks":false,"transfer_job_skip_locked_files":true,"logger_mask":-1,"prefer_utp2_lan":true,"net.udp_ipv6_mtu":1300,"net.udp_ipv4_mtu":1300,"prefer_net_over_disk_operations":true,"file_deduplication":false,"fix_conflicting_paths":true,"sync_extended_attributes":false,"async_io":false,"disk_worker_pool_size":4,"fs_query_file_id":false,"torrent_min_piece_size":1048576,"max_chunk_size":0,"disk_min_free_space_gb":0,"disk_min_free_space":"5","tunnel_protocols":"tcp;utp3;proxy;proxy_utp3","allow_pause_from_ui":true,"mc_can_manage_bandwidth_limit":false,"allowed_peers":[],"file_delay":"","upnp":true,"tunnel_ciphers":"DHE-PSK-AES128-GCM-SHA256;DHE-PSK-AES256-GCM-SHA384","net.enable_utp2":true,"net.enable_utp3":true,"net.speed_hard_limit_kbps":122070,"system_native_placeholders":true,"recreate_placeholders_on_removal":true},"connectivity_settings":{"trackers":"","events_servers":"","ping_interval":300},"schedule":[],"licensed":true,"storages":[],"filePolicies":{},"tags":[{"name":"VIRTUAL","value":"true","modified":1756191187},{"name":"AGENT_NAME","value":"FakeAgent_758123321D16EC18","modified":0},{"name":"AGENT_ID","value":"EA2ULYEX7D6TG4MA758123321D16EC18","modified":0}]}'
    // CONFIRM: '{"m":"confirm","id":"2","data":{"priority":0}}'
    private static string _authConfirm = "{\"m\":\"status\",\"subsystem\":\"auth\",\"error\":0,\"status\":\"approved\",\"client_token\":\"ZEOKPFPFEVYSSBGRFFP5AS2QDV65J5KU73YGGNF2OV5REYDWSSDA\"}";
    private static string _confirmMsg = "{{\"m\":\"confirm\",\"id\":\"{0}\",\"data\":{{\"priority\":0}}}}";
    private static string _pingMsg = "{{\"m\":\"ping\",\"ts\":{0}}}";
    private static int _confirmId = 1;

    public static string GetAuthConfirm()
    {
        return _authConfirm;
    }
    
    public static string GetConfirmMsg()
    {
        return string.Format(_confirmMsg, _confirmId++);
    }

    public static string GetPingMsg()
    {
        return string.Format(_pingMsg, DateTimeOffset.UtcNow.ToUnixTimeSeconds());
    }
}
