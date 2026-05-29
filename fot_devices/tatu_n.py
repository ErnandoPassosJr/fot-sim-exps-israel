import paho.mqtt.client as pub
import sensors
import json
import sys
import time
import uuid
from pathlib import Path
sys.path.append(str(Path.cwd())+"/tatu")
sys.path.append(str(Path.cwd())+"/datasets")
from DatasetUtils import DatasetUtils
from TATU import TatuReq, TatuRes
import random
#random.seed(99)

#You don't need to change this file. Just change sensors.py and config.json

from time import sleep


procs = []
pub_client = pub.Client(client_id='', clean_session=True,protocol=pub.MQTTv31)
rttSamples=[]

class virtualSensor():
    def __init__(self, idP, deviceName, sensorName, sensorsList, met, topic, topicError, pub_client, collectTime, publishTime, dataset,datasetColumn,latency,portAgent,topicAgent):
        self.processID = idP
        self.deviceName = deviceName
        self.sensorName = sensorName
        self.sensorsList = sensorsList
        self.met = met
        self.topic = topic
        self.topicError = topicError
        self.pub_client = pub_client
        self.publishTime = publishTime
        self.collectTime = collectTime
        self.dataset=dataset
        self.latency=latency
        self.datasetColumn=datasetColumn
        self.portAgent=portAgent
        self.topicAgent=topicAgent
        self.run()
    def run(self):
        print ("Starting virtual sensor " + self.processID)

        if (self.met.upper() == "EVENT"):
            self.buildEventAnwserDevice()
        elif (self.met.upper() == "GET"):
        	self.buildGetAnwserDevice()
        elif (self.met.upper() == "FLOW"):
            #print("INIT FLOW")
            self.buildFlowAnwserDevice()
        
        print ("Stopping process " + self.processID)


    def buildFlowAnwserDevice(self):
        t = 0
        envioInicio=0
        envioMqtt=0
        try:
            if not self.sensorsList:
                raise Exception("No sensors")

            for x in self.sensorsList:
                locals()[x["name"]] = []
            total_linhas=0
            with open(self.dataset, "r", encoding="utf-8") as f:
                total_linhas = sum(1 for _ in f)
                
            if(self.dataset!=None):
                datasetObject = DatasetUtils(path=self.dataset, column=self.datasetColumn,index=random.randint(0,total_linhas),window=4500)
            datasetIndex=0
            
            if(envioInicio==0 and "registry" not in self.topicAgent):
                envioInicio=1
                print(datasetObject.getValue(2))
                vet=[]
                vet.append(datasetObject.getValue(random.randint(1,total_linhas-3)))
                vet.append(datasetObject.getValue(random.randint(1,total_linhas-2)))
                vet.append(datasetObject.getValue(random.randint(1,total_linhas-1)))
                topicTemp="iot/edge/unknown/port_"+str(self.portAgent)
                msgDictTemp={"port":self.portAgent,"value":str(vet),"timestamp":str(time.perf_counter())}
                msgFinalTemp=json.dumps(msgDictTemp)
                self.pub_client.publish(topicTemp, msgFinalTemp)
            
            while True:
                for i in self.sensorsList:
                    sensorName=i["name"]
                    methodFLOW = getattr(sensors, sensorName)
                    retrieved = locals()[i["name"]]
                    retrieved.append(str(methodFLOW()))
                
                t = t + int(self.collectTime)
                arrayValues = []
                if (t >= int(self.publishTime)):
                    if(self.sensorName!=None):
                        header = {"method":"FLOW", "device":self.deviceName, "sensor":self.sensorName, "time":{"collect":self.collectTime,"publish":self.publishTime}}
                    else:
                        header = {"method":"FLOW", "device":self.deviceName, "time":{"collect":self.collectTime,"publish":self.publishTime}}
                    for y in self.sensorsList:
                        if(self.dataset==None):
                            for i in range(len(locals()[y["name"]])):
                                arrayValues.append(locals()[y["name"]][i])
                                #print(locals()[y["name"]][i])
                        #dataset ativo
                        else:
                            for i in range(len(locals()[y["name"]])):
                                arrayValues.append(str(datasetObject.getValue(datasetIndex)))
                                datasetIndex+=1
                            #dataset acess to index
                        locals()[y["name"]] = []
                    payload = {"sensors":arrayValues}
                    responseModel = {"header":header, "payload":payload}
                    tatuMessage=""
                    if(self.latency!=None):
                        tatuMessage = TatuRes("FLOW",collect=self.collectTime,publish=self.publishTime,sensor=self.sensorName,device=self.deviceName,sample=arrayValues,messageId=str(uuid.uuid4()),messageTimeStamp=time.perf_counter())
                    else:
                        tatuMessage = TatuRes("FLOW",collect=self.collectTime,publish=self.publishTime,sensor=self.sensorName,device=self.deviceName,sample=arrayValues)
                    
                    msgDict={"port":self.portAgent,"value":str(arrayValues),"timestamp":str(time.perf_counter())}
                    msgFinal=json.dumps(msgDict)
                    if(envioMqtt==0):
                        self.pub_client.publish(self.topicAgent, msgFinal)
                        envioMqtt=1
                    t = 0
                    arrayValues = []
                sleep(int(self.collectTime)/1000)
        except Exception as e:
            errorMessage = "There is no Sensor"
            #errorMessage = "There is no " + sensorName + " sensor in device " + deviceName
            errorNumber = 1
            responseModel = {"code":"ERROR", "number":errorNumber, "message":errorMessage}
            response = json.dumps(responseModel)
            print(e) 
            self.pub_client.publish(self.topicError, response)


#{"sensors":[{"humiditySensor":["50","47"]},{"temperatureSensor":["28","29"]}]}


    #TODO: verify self. in params
    def buildEventAnwserDevice(self):
        # Request: {"method":"EVENT", "sensor":"sensorName", "time":{"collect":collectTime}}
         
        try:
            arrayValues = []
            retrieved = []
            header = {"method":"EVENT", "device":self.deviceName, "sensor":self.sensorName, "time":{"collect":self.collectTime,"publish":self.publishTime}}
            methodEvent = getattr(sensors, self.sensorName)
            value = methodEvent()
            retrieved.append(str(value))
            #retrieved.append(value)
            sensorValues = {self.sensorName:retrieved}
            arrayValues.append(sensorValues)
            payload = {"sensors":arrayValues}
            responseModel = {"header":header, "payload":payload}
            response = json.dumps(responseModel)
            self.pub_client.publish(self.topic, response)
            while True:
                sleep(self.collectTime)
                self.publishTime = self.publishTime + self.collectTime
                aux = methodEvent()
                if aux!=value:
                    arrayValues = []
                    retrieved = []
                    header = {"method":"EVENT", "device":self.deviceName, "sensor":self.sensorName, "time":{"collect":self.collectTime,"publish":self.publishTime}}
                    value = aux
                    retrieved.append(str(value))
                    #retrieved.append(value)
                    sensorValues = {self.sensorName:retrieved}
                    arrayValues.append(sensorValues)
                    payload = {"sensors":arrayValues}
                    responseModel = {"header":header, "payload":payload}
                    response = json.dumps(responseModel)
                    self.pub_client.publish(self.topic, response)
        except:
            errorMessage = "There is no " + self.sensorName + " sensor in device " + self.deviceName
            errorNumber = 1
            responseModel = {"code":"ERROR", "number":errorNumber, "message":errorMessage}
            response = json.dumps(responseModel)
            self.pub_client.publish(self.topicError, response)
            
    
    def buildGetAnwserDevice(self):
        # Request: {"method": "GET", "sensor": "sensorName"}
        try:
            if not self.sensorsList:
                raise Exception("No deviecs")
            
            for x in self.sensorsList:
                locals()[x["name"]] = []
            
            for i in self.sensorsList:
                sensorName= i["name"]
                methodGet = getattr(sensors, sensorName)
                retrieved = locals()[i["name"]]
                retrieved.append(str(methodGet()))
					
            #print("methodGET")

            arrayValues = []

            header = {"method":"GET", "device":self.deviceName, "sensor":self.sensorName}
                    
            for y in self.sensorsList:
                sensorValues = {y["name"]:locals()[y["name"]]}
                arrayValues.append(sensorValues)
                locals()[y["name"]] = []
            
            payload = {"sensors":arrayValues}
            
            responseModel = {"header":header, "payload":payload}
            response = json.dumps(responseModel)
            
            self.pub_client.publish(self.topic, response)

        except:
            errorMessage = "There is no " + self.sensorName + " sensor in device " + self.deviceName
            errorNumber = 1
            responseModel = {"code":"ERROR", "number":errorNumber, "message":errorMessage}
            response = json.dumps(responseModel)
            pub_client.publish(self.topicError, response)
 

 
    #TODO: verify self. in params
    def buildPostAnwserDevice(self):
        try:
            methodPost = getattr(sensors, self.sensorName)
            methodPost(value)

            #Request: {"method":"POST", "sensor":"sensorName", "value":value}
            responseModel = {"code":"POST","method":"POST", "sensor":self.sensorName, "value":value}
            response = json.dumps(responseModel)
            self.pub_client.publish(self.topic, response)
        except:
            errorMessage = "There is no " + self.sensorName + " sensor in device " + self.deviceName
            errorNumber = 1
            responseModel = {"code":"ERROR", "number":errorNumber, "message":errorMessage}
            response = json.dumps(responseModel)
            self.pub_client.publish(self.topicError, response)



def on_disconnect(mqttc, obj, msg):
    print("disconnected tatu!")

def on_connect(mqttc, obj, flags, rc):
    topic="dev/"+obj["deviceName"]+"/RES/#"
    mqttc.subscribe(topic)

def on_message(mqttc, obj, msg):
    global rttSamples
    tatu_msg=json.loads(msg.payload)
    if('messageId' in tatu_msg["header"]):
        rtt=time.perf_counter()-float(tatu_msg["header"]["messageTimeStamp"])
        if(len(rttSamples)==4):
            rttSamples=[]
        rttSamples.append(rtt*1000)
        
            


def main(data, msg):
    mqttBroker = data["mqttBroker"]
    mqttPort = data["mqttPort"]
    mqttUsername = data["mqttUsername"]
    mqttPassword = data["mqttPassword"]
    deviceName = data["deviceName"]
    topic = data["topicPrefix"] + deviceName + data["topicRes"]
    topicError = data["topicPrefix"] + deviceName + data["topicErr"]
    sensorsList = data["sensors"]
    sensorName=None
    dataset=data["dataset"]
    datasetColumn=data["datasetColumn"]
    topicAgent=data["topicAgent"]
    portAgent=data["portAgent"]
    msgJson = json.loads(msg.payload)
    if(msgJson.get('sensor')!=None):
        sensorName = msgJson["sensor"]
    met = msgJson["method"]
    latency = data["latency"]
    messageId=None
    messageTimeStamp=None
    if(latency!=None):
        latency=True
    found = 0
    if(sensorName!=None):
        for sen in sensorsList:
            if (sen["name"]==sensorName):
                sensorsList = []
                sensorsList.append(sen)
                found = 1
                break
        if not found:
            sensorsList = []
    
    
        
    
    #print("-------------------------------------------------")
    #print("| Topic: " + str(msg.topic))
    #print("| Message: " + str(msg.payload))
    #print("-------------------------------------------------")
    if(sensorName!=None):
        idP = met + "_" + deviceName + "_" + sensorName
    else:
        idP = met + "_" + deviceName
    pub_client.user_data_set(data)
    pub_client.on_disconnect = on_disconnect
    if(latency!=None):
        pub_client.on_connect = on_connect
        pub_client.on_message = on_message
    pub_client.connect(mqttBroker, mqttPort, 60)
    pub_client.loop_start()
    
    
    if (met.upper()=="POST"):
        pass
    else:
        if (met.upper()=="GET"):
            collectTime = 0
            publishTime = 0
        elif (met.upper()=="FLOW"):
            time = msgJson["time"]
            collectTime = time["collect"]
            publishTime = time["publish"]
        elif (met.upper()=="EVENT"):
            time = msgJson["time"]
            collectTime = time["collect"]
            publishTime = 0

        sensor = virtualSensor(idP, deviceName, sensorName, sensorsList, met, topic, topicError, pub_client, collectTime, publishTime,dataset,datasetColumn,latency,portAgent,topicAgent)
        
