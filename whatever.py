#!/usr/bin/python
import requests
import os
import json
import yaml
import re
from pprint import pprint


pattern = re.compile(r'(neu|bu)-(\d+)-(\d+)')
server_list = []
switch_map = { 'cisco-17-42': 'MOC-NEU-PODB-R3C17-1',
                'cisco-19-42': 'MOC-NEU-PODB-R3C19-1',
                'bu-cisco-23-40': 'r4-pA-c23-nexus3548'}

user = os.environ.get('HIL_USERNAME')
password = os.environ.get('HIL_PASSWORD')
url = os.environ.get('HIL_ENDPOINT') + '/v0/'
r = requests.get(url+'nodes/all', auth=(user, password), verify=True)
all_nodes = json.loads(r.content)

ignore_list = ['neu-19-10', 'bu-23-101']

netbox_servers = []
servers_3 = []
servers_5 = []
servers_15 = []
servers_17 = []
servers_19 = []
servers_21 = []
servers_23 = []
count = 0

def show_node(node):
    api = 'node/' + node
    node_details = requests.get(url+api, auth=(user, password), verify=True)
    return json.loads(node_details.content)

def parse_node(node):

    coordinates = pattern.match(node['name'])

    node_info = {}
    node_info['name'] = node['name']
    node_info['height'] = "1"


    # Set role
    if node['project'] in ['maas', 'openshift', 'openshift-staging', 'curator-openshift']:
        node_info['role'] = node['project']
    elif node['project'] == 'ceph':
        node_info['role'] = 'research-ceph'
    elif node['project'] == 'idan-cnv':
        node_info['role'] = 'moc-infra'
    else:
        node_info['role'] = 'BMI'

    # Figure out and set model
    try:
        if node['metadata']['model'] == '"dell-m620"':
            node_info['manufacturer'] = "Dell Inc."
            node_info['model'] = 'PowerEdge M620'
        elif node['metadata']['model'] == '"r720"':
            node_info['manufacturer'] = "Dell Inc."
            node_info['model'] = 'PowerEdge R720'
            node_info['height'] = "2"
        elif node['metadata']['model'] == '"cisco-c220"':
            node_info['manufacturer'] = 'Cisco'
            node_info['model'] = 'C220'
        elif node['metadata']['model'] == '"lenovo-x3550-M5"':
            node_info['manufacturer'] = 'Lenovo'
            node_info['model'] = 'lenovo-x3550-M5'
        elif node['metadata']['model'] == '"intel"':
            node_info['manufacturer'] = 'Intel Corporation'
            node_info['model'] = 'S2600WTT'
            node_info['height'] = "2"
        else:
            node_info['model'] = node['metadata']['model']
            node_info['manufacturer'] = 'Generic'
    except:
        node_info['model'] = 'PowerEdge R620'
        node_info['manufacturer'] = 'Dell Inc.'

    # Figure out and set coordinates
    rack = coordinates.group(2)

    if int(coordinates.group(3)) < 100:
        rackpos = coordinates.group(3)
        node_info ['rackpos'] = rackpos
    else:
        rackpos = str(int(coordinates.group(3)) - 100)
        node_info['parent_device'] = 'kumo_dell_blades'
        node_info['height'] = "0"
        node_info ['parent_device_bay'] = 'Slot ' + rackpos

    node_info['rack'] = rack

    # Gather and set NIC information
    node_info['nics'] = []

    if rack != '23':
        ipmi_switch = 'ipmi-cage' + rack
    else:
        ipmi_switch = 'r4-pA-c23-catalyst3650'

    if rack != '23':
        node_info['nics'].append(
                            {'name': 'ipmi',
                             'switch_hostname': ipmi_switch,
                             'switchport': 'GigabitEthernet 1/1/' + rackpos,
                             'type': '1000Base-t (1GE)' }
                             )

    for nic in node['nics']:
        if nic['macaddr'] == 'nomacaddr':
            mac_addr = '00:00:00:00:00:00'
        else:
            mac_addr = nic['macaddr']

        try:
            switch_hostname = switch_map[nic['switch']]
            switchport = nic['port']
        except:
            switch_hostname = 'rbr-0' + nic['port'][0]
            if nic['switch'] == 'brocade_forty':
                switchport = "FortyGigabitEthernet " + nic['port']
            else:
                switchport = "TenGigabitEthernet " + nic['port']

        node_info['nics'].append(
                            {'name': nic['label'],
                             'mac_address': mac_addr,
                             'switch_hostname': switch_hostname,
                             'switchport': switchport}
                             )
    return node_info


for node in all_nodes:
    count += 1

    if node in ignore_list:
        continue

    print("processing node number: " + str(count) + " out of " + str(len(all_nodes)))
    print("node name: " + node)
    if 'oct' in node or 'bu-21-' in node:
        continue
    server_data = parse_node(show_node(node))
    rack_number = server_data['rack']

    if 'rackpos' in server_data and server_data['rackpos'] == '41':
        continue

    if rack_number == '3':
        servers_3.append(server_data)
    elif rack_number == '5':
        servers_5.append(server_data)
    elif rack_number == '15':
        servers_15.append(server_data)
    elif rack_number == '17':
        servers_17.append(server_data)
    elif rack_number == '19':
        servers_19.append(server_data)
    elif rack_number == '21':
        servers_21.append(server_data)
    elif rack_number == '23':
        servers_23.append(server_data)
    else:
        print('error')
        print(node)
        print(server_data)

rack_3 = {'site': 'MGHPCC', 'location': 'Row3/PodB', 'rack': 'Row3/PodB/Cage3', 'servers': servers_3}
rack_5 = {'site': 'MGHPCC', 'location': 'Row3/PodB', 'rack': 'Row3/PodB/Cage5', 'servers': servers_5}
rack_15 = {'site': 'MGHPCC', 'location': 'Row3/PodB', 'rack': 'Row3/PodB/Cage15', 'servers': servers_15}
rack_17 = {'site': 'MGHPCC', 'location': 'Row3/PodB', 'rack': 'Row3/PodB/Cage17', 'servers': servers_17}
rack_19 = {'site': 'MGHPCC', 'location': 'Row3/PodB', 'rack': 'Row3/PodB/Cage19', 'servers': servers_19}
rack_21 = {'site': 'MGHPCC', 'location': 'Row4/PodA', 'rack': 'Row4/PodA/Cage21', 'servers': servers_21}
rack_23 = {'site': 'MGHPCC', 'location': 'Row4/PodA', 'rack': 'Row4/PodA/Cage23', 'servers': servers_23}

netbox_servers.append(rack_3)
netbox_servers.append(rack_5)
netbox_servers.append(rack_15)
netbox_servers.append(rack_17)
netbox_servers.append(rack_19)
netbox_servers.append(rack_21)
netbox_servers.append(rack_23)

with open('netbox_servers.yaml', 'w') as yaml_file:
    yaml.dump({"netbox_servers": netbox_servers}, yaml_file)
