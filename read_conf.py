from ciscoconfparse2 import CiscoConfParse
from flask import Flask,render_template,request,redirect,url_for
import os,requests,json,pprint,re

class read:

    def Interface_detail(interface_value):
        # This function is used to read the interface configuration
        feature_list_on_interface =[]
        PAgP=["auto","desirable"]
        LACP =["active", "passive"]
        #check the configuration of the interfaces
        interface_children = interface_value.children
        for config_det in interface_children:
            private_vlan = config_det.re_match_typed(regex=r'\sswitchport\smode\sprivate-vlan?(\S.*)') #mode private-vlan host
            pruning = config_det.re_match_typed(regex=r'\sswitchport\strunk\spruning?(\S.*)')
            voice_vlan = config_det.re_match_typed(regex=r'\sswitchport\svoice?(\S.*)')
            data_vlan = config_det.re_match_typed(regex=r'\sswitchport\saccess?(\S.*)')
            stp_port = config_det.re_match_typed(regex=r'\sspanning-tree\sport-priority?(\S.*)')
            portfast = config_det.re_match_typed(regex=r'\sspanning-tree\sportfast?(\S.*)')
            root_guard = config_det.re_match_typed(regex=r'\sspanning-tree\sguard\sroot?(\S.*)')
            Flex_links = config_det.re_match_typed(regex=r'\sswitchport\sbackup\sinterface?(\S.*)')
            storm_control = config_det.re_match_typed(regex=r'\sstorm-control?(\S.*)')
            protected = config_det.re_match_typed(regex=r'\sswitchport\sprotected?(\S.*)')
            port_security = config_det.re_match_typed(regex=r'\sswitchport\sport-security?(\S.*)')
            port_udld = config_det.re_match_typed(regex=r'\sudld\sport?(\S.*)')
            lldp = config_det.re_match_typed(regex=r'\slldp?(\S.*)')
            IPv6 = config_det.re_match_typed(regex=r'\sipv6?(\S.*)')
            Etherchannel_Type = config_det.re_match_typed('^\schannel-group\s\d\smode\s+(\S.+)')
            mode_access = config_det.re_match_typed(regex=r'\sswitchport\smode\saccess?(\S.*)')
            mode_trunk = config_det.re_match_typed(regex=r'\sswitchport\smode\strunk?(\S.*)')
            directed_broadcast = config_det.re_match_typed(regex=r'\sip\sdirected-broadcast?(\S.*)')
            description = config_det.re_match_typed(regex=r'\sdescription?(\S.*)')

            if not private_vlan == "":
                feature_list_on_interface.append(["Private_Vlan",""])
            if not pruning == "":
                feature_list_on_interface.append(["Pruning",""])
            if not voice_vlan== "":
                feature_list_on_interface.append(["Voice VLAN","Y"])
            if not data_vlan== "":
                feature_list_on_interface.append(["Data VLAN","Y"])
            if not stp_port== "":
                feature_list_on_interface.append(["STP port cost",""])
            if not portfast== "":
                feature_list_on_interface.append(["Portfast",""])
            if not root_guard== "":
                feature_list_on_interface.append(["RootGuard",""])
            if not Flex_links == "":
                feature_list_on_interface.append(["Flex Links",""])
            if not storm_control== "":
                feature_list_on_interface.append(["Storm Control",""])
            if not protected == "":
                feature_list_on_interface.append(["Protected port",""])
            if not port_security == "":
                feature_list_on_interface.append(["Port Security",""])
            if not port_udld == "":
                feature_list_on_interface.append(["UDLD",""])
            if not lldp == "":
                feature_list_on_interface.append(["LLDP",""])
            if not IPv6 == "":
                feature_list_on_interface.append(["IPv6",""])
            # Figuring out the type of Etherchannel mode on the interface
            if not Etherchannel_Type== "":
                if Etherchannel_Type in PAgP:
                    feature_list_on_interface.append(["EtherChannel PAgP",""])
                if Etherchannel_Type in LACP:
                    feature_list_on_interface.append(["EtherChannel LACP",""])
            if not mode_access == "":
                feature_list_on_interface.append(["Access mode","Y"])
            if not mode_trunk == "":
                feature_list_on_interface.append(["Trunk mode","Y"])
            if not directed_broadcast == "":
                feature_list_on_interface.append(["Directed Broadcast",""])
            if not description == "":
                feature_list_on_interface.append(["Description","Y"])

        #combine all the features on the interface together in a list and send it back
        return(feature_list_on_interface)

    def Checking_features(sw_file):
        # ecoen66 added some additional unsupported features
        additional_unsupported = {'RIP':'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing',\
        'EIGRP':'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing',\
        'OSPFv2':'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing',\
        'OSPFv3':'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing',\
        'BGP':'https://documentation.meraki.com/MX/Networks_and_Routing/Border_Gateway_Protocol_(BGP)',\
        'IS-IS':'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing',\
        'VRF': 'https://documentation.meraki.com/MS/Layer_3_Switching/MS_Layer_3_Switching_and_Routing'\
        }
        
        additional_More_info = {'RIP':'Not Supported',\
        'EIGRP':'Not Supported',\
        'OSPFv2':'Supported on MS250 and above',\
        'OSPFv3':'Not Supported',\
        'BGP':'Currently supported on MX only',\
        'IS-IS':'Not Supported',\
        'VRF': 'Not Supported'\
        }

        # Connect to the server where we have the list of unsupported features on Meraki MS and the links associated to those features
        unsupported_features_raw = requests.get('http://msfeatures.netdecorators.com:7900/return_list_unsupported')
        unsupported_features = json.loads(unsupported_features_raw.text)
        unsupported_features.update(additional_unsupported)
        More_info_raw = requests.get('http://msfeatures.netdecorators.com:7900/return_more_info')
        More_info = json.loads(More_info_raw.text)
        More_info.update(additional_More_info)
        
        
        Features_configured = []

        # Here we will go through parsing/reading Cisco Catalyst configuration file and capture specific configuration
        parse =  CiscoConfParse(sw_file, syntax='ios', factory=True)

        #FUTURE ENHANCMENT - Add catalyst command then add it to a in dic()
        hostname = parse.find_objects('^hostname')
        interface = parse.find_objects('^interface')
        vtp = parse.find_objects('^vtp')
        mls = parse.find_objects('^mls')
        spanning = parse.find_objects('^spanning')
        snmp = parse.find_objects('^snmp')
        logging_host = parse.find_objects('^logging')
        ntp = parse.find_objects('^ntp')
        access_list = parse.find_objects('^access-list')
        extended_access_list = parse.find_objects('^ip\saccess-list')
        port_mirror = parse.find_objects('^monitor')
        aaa = parse.find_objects('^aaa')
        netflow = parse.find_objects('^flow\sexporter')
        dhcp = parse.find_objects('^ip\sdhcp\spool')
        banner = parse.find_objects('^banner')
        radius = parse.find_objects('^radius-server')
        radius2 = parse.find_objects('^radius\sserver')
        http_server = parse.find_objects('^ip\shttp')
        stack = parse.find_objects('^switch')
        mab_VLAN_mac = parse.find_objects('^mab\srequest\sformat')
        VLAN = parse.find_objects('^vlan')
        VPMS = parse.find_objects('^vpms')
        uplinkfast = parse.find_objects('^spanning-tree\suplinkfast')
        backbonefast = parse.find_objects('^spanning-tree\sbackbonefast')
        Loopguard = parse.find_objects('spanning-tree\sloopguard')
        DHCP_Snooping = parse.find_objects('ip\sdhcp\ssnooping')
        IP_Source_Guard = parse.find_objects('ip\ssource\sbinding')
        ARP_Inspection = parse.find_objects('^ip\sarp\sinspection')
        ARP_ACL = parse.find_objects('^arp\saccess-list')
        psp = parse.find_objects('^psp')
        UDLD = parse.find_objects('^udld')
        logging = parse.find_objects('^logging')
        ip_sla = parse.find_objects('^ip\ssla')
        Multicast_igmp = parse.find_objects('^ip\sigmp')
        Multicast_pim = parse.find_objects('^ip\spim')
        static_routing = parse.find_objects('^ip\sroute')
        ipv6 = parse.find_objects('^ipv6')
        rip = parse.find_objects('^router rip')
        eigrp = parse.find_objects('^router eigrp')
        ospfv3 = parse.find_objects('^router ospfv3')
        ospf = parse.find_objects('^router ospf')
        bgp = parse.find_objects('^router bgp')
        isis = parse.find_objects('^router isis')
        vrf = parse.find_objects('^vrf')


        # Build main dictionary of all the features the script can read
        a = {
        "Hostname": [hostname,"Y"],
        "Interface": [interface,"Y"],
        "VTP": [vtp,""],
        "QoS": [mls,""],
        "Spanning Tree": [spanning,""], #check the type of STP
        "SNMP": [snmp,""],
        "Syslog": [logging_host,""],
        "NTP": [ntp,""], #can't be configured
        "Access-list": [access_list,""],
        "Port mirroring": [port_mirror,""],
        "AAA": [aaa,""],
        "Extended access-list": [extended_access_list,""],
        "NetFlow": [netflow,""],     #can't be configured
        "DHCP server": [dhcp,""],
        "banner": [banner,""],
        "radius": [radius,""],
        "radius": [radius2,""],
        "HTTP server": [http_server,""],
        "Stack": [stack,""],
        "MAB VLAN MAC Auth": [mab_VLAN_mac,""],     #can't be configured
        "Layer 2 VLAN": [VLAN,""],
        "VPMS": [VPMS,""],     #can't be configured
        "STP Uplinkfast": [uplinkfast,""], #can't be configured
        "STP Backbonefast": [backbonefast,""], #can't be configured
        "STP LoopGuard": [Loopguard,""],
        "DHCP Snooping": [DHCP_Snooping,""],
        "IP Source Binding": [IP_Source_Guard,""],
        "ARP Inspection": [ARP_Inspection,""],
        "ARP Access-list": [ARP_ACL,""],
        "Protocol Storm Protection": [psp,""],
        "UDLD": [UDLD,""],
        "Logging": [logging,""],
        "IP SLA": [ip_sla,""],
        "Multicast IGMP": [Multicast_igmp,""],
        "Multicast PIM": [Multicast_pim,""],
        "Static routing": [static_routing,""],
        "IPv6": [ipv6,""],
        "RIP": [rip,""],     #can't be configured
        "EIGRP": [eigrp,""],     #can't be configured
        "OSPFv2": [ospf,""],
        "OSPFv3": [ospfv3,""],     #can't be configured
        "BGP": [bgp,""],     #can't be configured
        "IS-IS": [isis,""],     #can't be configured
        "VRF": [vrf,""]
        }

        # Running a loop to take out the unconfigured features and only focus on what is configured
        for key, value in a.items():
            if not value[0]:
                print(f'---------------{key} is not configured')
            else:
                for detail in value[0]:
                    #Lookup the type of STP
                    STP_Type = detail.re_match_typed('^spanning-tree\smode\s+(\S.+)')
                    translatable = ""
                    if not STP_Type== "":
                        if STP_Type=="rapid-pvst":
                            translatable = "Y"
                        Features_configured.append([STP_Type,translatable])

                    # As some of the configuration will be nested under the interface config, hence we have this if statement and send the interface name to Interface_detail function to get the subconfig of the interface
                    if key == "Interface":
                        check_features = read.Interface_detail(detail)
                        print(f"======{check_features}")
                        #Go through a loop to read the return of the config under the interface and then add them to the main list (Features_configured)
                        x = 0
                        while x < len(check_features):
                            Features_configured.append(check_features[x])
                            x +=1

                    detail = detail.text
                    print(f"{key} and value is {detail}")
                    Features_configured.append([key,value[1]])
        #Only capture unique values in a new list
        aux_features_config = []
        for entry in Features_configured:
            if entry not in aux_features_config:
                aux_features_config.append(entry)

        return aux_features_config, unsupported_features,More_info
