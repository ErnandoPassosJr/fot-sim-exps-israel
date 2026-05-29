#!/usr/bin/python

from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import lg
from mininet.node import Node, RemoteController, Controller, OVSKernelSwitch
from mininet.topolib import TreeNet
import time
import argparse
from fot_network import utils_hosts
import json
import random
import sys
from pathlib import Path
sys.path.append(str(Path.cwd())+"/tatu")
from TATU import TatuReq, TatuRes

from fot_network import create_topo

parser = argparse.ArgumentParser(description = 'Params sensors')
parser.add_argument('--broker', action = 'store', dest = 'broker', required = True)
parser.add_argument('--collect', action = 'store', dest = 'collect', required = True)
parser.add_argument('--pub', action = 'store', dest = 'pub', required = True)
args = parser.parse_args()



#################################
def startNAT( root, inetIntf='eth0', subnet='10.0/8' ):
    """Start NAT/forwarding between Mininet and external network
    root: node to access iptables from
    inetIntf: interface for internet access
    subnet: Mininet subnet (default 10.0/8)="""

    # Identify the interface connecting to the mininet network
    localIntf = root.defaultIntf()

    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Create default entries for unmatched traffic
    root.cmd( 'iptables -P INPUT ACCEPT' )
    root.cmd( 'iptables -P OUTPUT ACCEPT' )
    root.cmd( 'iptables -P FORWARD DROP' )

    # Configure NAT
    root.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
    root.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )

    # Instruct the kernel to perform forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=1' )

def stopNAT( root ):
    """Stop NAT/forwarding between Mininet and external network"""
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Instruct the kernel to stop forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=0' )

def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
       by specifying manual configuration in /etc/network/interfaces
       root: a node in the root namespace (for running commands)
       intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if line not in config:
        print ('*** Adding', line.strip(), 'to', cfile)
        with open( cfile, 'a' ) as f:
            f.write( line )
        # Probably need to restart network-manager to be safe -
        # hopefully this won't disconnect you
        root.cmd( 'service network-manager restart' )

def connectToInternet( network, switch='s1', rootip='10.254', subnet='10.0/8'):
    """Connect the network to the internet
       switch: switch to connect to root namespace
       rootip: address for interface in root namespace
       subnet: Mininet subnet"""
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]

    # Create a node in root namespace
    root = Node( 'root', inNamespace=False )

    # Prevent network-manager from interfering with our interface
    fixNetworkManager( root, 'root-eth0' )

    # Create link between root NS and switch
    link = network.addLink( root, switch )
    link.intf1.setIP( rootip, prefixLen )

    # Start network that now includes link to root namespace
    network.start()

    # Start NAT and establish forwarding
    startNAT( root )

    # Establish routes from end hosts
    for host in network.hosts:
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'route add -net', subnet, 'dev', host.defaultIntf() )
        host.cmd( 'route add default gw', rootip )

    return root



def init_servers(net):
	print("Init Servers")
	s=utils_hosts.return_hosts_per_type('server')
	for i in range(0,len(s)):
		net.get(s[i].name).cmd('mosquitto &')
		net.get(s[i].name).cmdPrint('cd '+fuseki_path+'; ./fuseki-server &')
		time.sleep(15)
			
			
def init_gateways(net):
	print("Init Gateways")
	g=utils_hosts.return_hosts_per_type('gateway')
	for i in range(0,len(g)):
		print(g[i].name)
		net.get(g[i].name).cmdPrint('mosquitto &')
		#net.get('h6').cmd('python servico.py &')
	time.sleep(5)
			
		
def stop_gateways(net):
	g=utils_hosts.return_hosts_per_type('gateway')
	
	for i in range(0,len(g)):
		if((i+1)<10):
			net.get(g[i].name).cmdPrint('cd '+service_mix_path+'/0'+str(i+1)+'/bin; ./stop &')
		else:
			net.get(g[i].name).cmdPrint('cd '+service_mix_path+'/'+str(i+1)+'/bin; ./stop &')
		time.sleep(5)

def init_sensors(net):
	#tipos de sensores no arquivo sensors.py, ex: temperatureSensor, soilmoistureSensor, solarradiationSensor, ledActuator
    s=utils_hosts.return_hosts_per_type('sensor')
    ass=utils_hosts.return_association()
    datasetColumn="light"
    dataset="datasets/"+datasetColumn+"1.csv"
    for i in range(0,len(s)):
        datasetColumn=str(s[i].sensorType)
        dataset="datasets/"+datasetColumn+"1.csv"
        if((i+1)<10):
            net.get(s[i].name).cmd('python fot_devices/main_n.py --name sc0'+str(i+1)+' --broker '+str(args.broker)+' --port 0'+str(i+1)+' --dataset '+str(dataset)+' --datasetColumn '+str(datasetColumn)+' &')
        else:
            net.get(s[i].name).cmd('python fot_devices/main_n.py --name sc'+str(i+1)+' --broker '+str(args.broker)+' --port '+str(i+1)+' --dataset '+str(dataset)+' --datasetColumn '+str(datasetColumn)+' &')
        time.sleep(0.1)

def init_flow(net):
    print ("Temp: Init Flow")
    g=utils_hosts.return_hosts_per_type('gateway')
    ass=utils_hosts.return_association()
    col=str(args.collect)
    pub=str(args.pub)
    #col=60
    #pub=60000
    ind=0
    
    s=utils_hosts.return_hosts_per_type('sensor')
    for i in range(0,len(s)):
        tatuMessage = TatuReq("FLOW",collect=col,publish=pub,sensor=s[i].sensorType,device=s[i].name_iot)
        print("mosquitto_pub -h "+str(args.broker)+" -m "+tatuMessage.getTatu())
        net.get(s[i].name).cmd("mosquitto_pub -h '"+str(args.broker)+"' -t 'dev/"+s[i].name_iot+"/REQ' -m '"+tatuMessage.getTatu()+"'")
        time.sleep(0.3)
        ind+=1


if __name__ == '__main__':
	lg.setLogLevel( 'info')
	net = Mininet(link=TCLink)
	#criar switches, hosts e topologia
	create_topo.create(net)
	
	# Configurar e iniciar comunicacao externa
	rootnode = connectToInternet( net )
	
	init_gateways(net)
	
	#Iniciar sensores virtuais
	#init_sensors(net)
	
	#Iniciar fluxo de comunicacao
	#init_flow(net)
	
	#init_servers(net)
	
	
	#init_servers(net)
	net.start()
	CLI( net )
	# Shut down NAT
	stopNAT( rootnode )
	#stop_gateways(net)
	#time.sleep(15)
    
	net.stop()
