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

def show_node(node):
    api = 'node/' + node
    node_details = requests.get(url+api, auth=(user, password), verify=True)
    return json.loads(node_details.content)

def parse_node(node):

    location = pattern.match(node['name'])

    node_info = {}
    node_info['name'] = node['name']
    node_info['role'] = 'BMI'
    node_info['height'] = "1"

    # Figure out and set model
    try:
        if node['metadata']['model'] == 'dell-m620':
            node_info['manufacturer'] = "Dell Inc."
            node_info['model'] = 'PowerEdge M620'
        elif node['metadata']['model'] == 'cisco-c220':
            node_info['manufacturer'] = "Cisco"
            node_info['model'] = 'C220'
        else:
            node_info['model'] = node['metadata']['model']
            node_info['manufacturer'] = "Generic"
    except:
        node_info['model'] = 'PowerEdge R620'
        node_info['manufacturer'] = 'Dell Inc.'

    # Figure out and set location
    node_info['rack'] = location.group(2)

    if int(location.group(3)) < 100:
        node_info['rackpos'] = location.group(3)
    else:
        node_info['rackpos'] = str(int(location.group(3)) - 100)

    # Gather and set NIC information
    if node['nics'] != []:
        node_info['nics'] = []

        for nic in node['nics']:

            try:
                switch_hostname = switch_map[nic['switch']]
                switchport = 'Ethernet' + nic['port']
            except:
                switch_hostname = 'rbr-0' + nic['port'][0]
                if nic['switch'] == 'brocade_forty':
                    switchport = "FortyGigabitEthernet " + nic['port']
                else:
                    switchport = "TenGigabitEthernet " + nic['port']

            node_info['nics'].append(
                                {'name': nic['label'],
                                 'mac_address': nic['macaddr'],
                                 'switch_hostname': switch_hostname,
                                 'switchport': switchport}
                                 )
    return node_info

pprint(parse_node(show_node('neu-19-6')))
# for node in json.loads(r.content):
#     parse_node(show_node(node))
