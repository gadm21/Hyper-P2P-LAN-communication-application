import scapy.all as scapy
from Tkinter import *   #Will be used for the GUI
from socket import *    #Will be used for making socket connections
import string          #Will be used for string manipulation
import sys            #Will be used for handling exceptions
from time import *
from threading import Thread
import Queue 


class Data:
    def __init__(self):
        self.username= "nothing"
    def editUsername(self, u):
        self.username= u
        
my_data= Data()

class Chat_object:
    def __init__(self, c, s_q, r_q, c_index):
        self.send_queue= s_q
        self.recv_queue= r_q
        self.client= c
        self.index= c_index
        #CHAT_THREAD= Thread(target= start_chat, args= (client,))
        self.send_thread= Thread(target= self.send)
        self.recv_thread= Thread(target= self.recv)
        self.send_thread.daemon= True
        self.recv_thread.daemon= True
        self.work= True
        self.send_thread.start()
        self.recv_thread.start()
            
    def send(self):
        while self.work:
            if not self.send_queue.empty():
                try:
                    message= self.send_queue.get()
                    self.client.send(message)
                except:
                    print "unable to send"
            sleep(1)
            
    def recv(self):
        while self.work:
            
            try:
                message= self.client.recv(1024)
                print "message: ", message
                if message== "closeplz":
                    self.close()
                else: self.recv_queue.put(message)
            except:
                print "unable to recieve"
            sleep(1)
            
    def close(self):
        #try:
        self.work= False
        self.client.send("closeplz".encode())
        self.client.close()
        #except:
            #print "error closing m"
        

def can_connect(ip, port):
    addr= (ip, port)
    print "connecting to: ", ip, "  :  ", port
    try:
        client_socket= socket(AF_INET, SOCK_STREAM)
        client_socket.connect(addr)
        return client_socket
    except:
        print "unable to connect"
        return None
    
    
    
    
def handle_incoming_connections(server, waiting_clients_queue, waiting_addresses_queue):
    print "handling incoming connections..."
    while True:
        try:
            client, client_address= server.accept()
            waiting_clients_queue.put(client)
            waiting_addresses_queue.put(client_address)
            
        except:
            print "server is unable to accept clients"
    print "main server closed"
    
def handle_incoming_queries(server2, requests, answers):
    print "handling incoming queries"
    while True:
        #try:
        print "handling incoming queries inside"
        client, client_address= server2.accept()
        print "got a query"
        msg= client.recv(1024)
        print "it says, ", msg
        username= my_data.username
        if msg== "auth":
            if username== "nothing":
                client.send("no".encode())
            else: client.send(username.encode())
        if msg== "authme":
            credentials= (client.recv(1024)).split('/')
            requests.put("authme")
            requests.put(credentials[0])
            requests.put(credentials[1])
            print "credentials: ", credentials[0], " : ", credentials[1]
            while answers.emtpy():
                pass
            reply= answers.get()
            answers.get() # get the last message: "end"
            print "reply on authentication request ", reply
            client.send(reply.encode())
        if msg== "scan":
            print "getting users list"
            requests.put("scan")
            users= ""
            while True:
                if not answers.empty():
                    user= answers.get()
                    print "got: ", user
                    if user== "end": break
                    users+= user+ '/'
            client.send(users.encode())
            print "done"
        if msg=="file":
            filename= client.recv(1024)
            requests.put("file")
            requests.put(filename)
            while answers.empty():
                pass
            reply= answers.get()
            answers.get() #get the last message: "end"
            print "reply on file sending request ", reply
            client.send(reply.encode())
        else: print "can't define this message"
        #except:
            #print "error with queries server"
            



class User:
    def __init__(self, ip, port):
        self.port_scanned= False
        self.authenticated= False
        self.IP= ip
        self.Port= port
        self.view= ip
    
    def scan_port(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(0.7)
        try:
            s.connect((self.IP, self.Port))
            s.send("close".encode())
            s.close()
            self.port_scanned= True
            return True
        except:
            return False
    
    def authenticate(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect((self.IP, self.Port))
            s.send("auth".encode())
            response= s.recv(1024)
            print "response: ", response
            if response!= "no":
                self.view= response
            s.close()
            self.authenticated= True
            return True
        except:
            return False