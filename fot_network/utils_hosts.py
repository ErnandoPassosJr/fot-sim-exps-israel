import json
import fileinput
from operator import itemgetter

data_hosts="fot_network/data_hosts.json"
association_hosts="fot_network/association_hosts.json"
config_tatu="config.json"

class to_object(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)
			

def return_hosts():
	f=open(data_hosts,'r')
	lines=len(f.readlines())
	f.close()
	f=open(data_hosts,'r')
	st2=[]
	st2=f.readlines()
	f.close()
	hosts=[]
	for i in range(0,(lines)):
		hosts.append(to_object(st2[i]))
	return hosts


def return_hosts_json():
	f=open(data_hosts,'r')
	lines=len(f.readlines())
	f.close()
	f=open(data_hosts,'r')
	st2=[]
	st2=f.readlines()
	f.close()
	hosts=[]
	for i in range(0,(lines)):
		hosts.append(st2[i])
	return hosts

def return_association():
	f=open(association_hosts,'r')
	lines=len(f.readlines())
	f.close()
	f=open(association_hosts,'r')
	st2=[]
	st2=f.readlines()
	f.close()
	devices=[]
	for i in range(0,(lines)):
		if(to_object(st2[i]).name_gateway!='cloud'):
			devices.append(to_object(st2[i]))
	return devices
		
def return_hosts_per_type(type_host):
	hosts=return_hosts()
	re = []
	for i in range(0,len(hosts)):
		if (hosts[i].type==type_host) :
			re.append(hosts[i])
	return re

	
def write_host(st):
	x=open(data_hosts,'a')
	x.write(st+"\n")
	x.close()

def generate_data_hosts(args):
    h=[]
    x=open(data_hosts,'w')
    x.close()
    sensorType=["temperature","humidity","light","voltage"]
    indiceSensor=0
    for i in range(0,int(args.sensor)):
        st=""
        if((i+1)<10):
            st="{\"type\":\"sensor\",\"name\":\"h"+str(i+1)+"\",\"name_iot\":\"sc0"+str(i+1)+"\",\"ip\":\"10.0.0."+str(i+1)+"\",\"sensorType\":\""+str(sensorType[indiceSensor])+"\"}"
        else:
            st="{\"type\":\"sensor\",\"name\":\"h"+str(i+1)+"\",\"name_iot\":\"sc"+str(i+1)+"\",\"ip\":\"10.0.0."+str(i+1)+"\",\"sensorType\":\""+str(sensorType[indiceSensor])+"\"}"
        write_host(st)
        indiceSensor+=1
        if(indiceSensor==(len(sensorType))):
            indiceSensor=0
            
def write_hosts(h):
	for i in range(0,len(h)):
		write_host(json.dumps(h[i]))


def return_host_per_name(name_host):
	#print("utils")
	h=return_hosts()
	#print("utils2")
	for i in range(0,len(h)):
		if(str(h[i].name)==name_host or str(h[i].name_iot)==name_host):
			#print(h[i].name)
			return h[i]


def update_flow(value):
	a_file = open(config_tatu, "r")
	json_object = json.load(a_file)
	a_file.close()
	if(json_object["publish"]!=value):
		json_object["publish"] = int(value)
		json_object["collect"] = int(value)
		a_file = open(config_tatu, "w")
		json.dump(json_object, a_file)
		a_file.close()

def get_pub():
	with open(config_tatu) as f:
		data = json.load(f)
	pub=data["publish"]
	return pub
