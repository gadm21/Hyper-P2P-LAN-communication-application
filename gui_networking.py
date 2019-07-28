#.......................................................................-Imports
import scapy.all as scapy
from Tkinter import *   #Will be used for the GUI
from socket import *    #Will be used for making socket connections
import string          #Will be used for string manipulation
import sys            #Will be used for handling exceptions
from threading import Thread
import Queue
from time import *
from gui_networking_helper import *
from authentication import *
import tkFileDialog as filedialog

#----------------------------------------------------------------------declarations
host= ""
port = 35000 
ADDR= (host, port)
server= socket(AF_INET, SOCK_STREAM)
server.bind((host, 35000))
server.listen(10)
server2= socket(AF_INET, SOCK_STREAM)
server2.bind((host, 7070))
server2.listen(10)
buttons= []
Users= []
#connections= []
#buf= Queue.Queue()
send_q= Queue.Queue()
recv_q= Queue.Queue()
requests= Queue.Queue()
answers= Queue.Queue()
waiting_clients_queue= Queue.Queue()
waiting_addresses_queue= Queue.Queue()
m= None 

#...................................................................callbacks

def close_opened_connections():
    global m
    if m is not None:
        m.close()
        m= None
    
            
def send(arg):
    global m
    if m is None:
        print "nowhere to send to..."
        return
    message= my_msg.get()
    my_msg.set("")
    msg_list.insert(END, message)
    send_q.put(message)
 

def freeze_buttons():
    for button in buttons:
        button.pack_forget()
        
def connect(index):
    global m
    
    if m is not None:
        if index== m.c_index:
            return
        close_opened_connections()
        if Users[index].port_scanned:
            buttons[index].config(bg= "blue")
        else: 
            buttons[index].config(bg= "powder blue")
    client_socket= can_connect(Users[index].IP, 35000)
    if client_socket is not None:
        close_opened_connections()
        buttons[index].config(bg="green")
        m= Chat_object(client_socket, send_q, recv_q, index)

def scan_callback():
    global buttons, Users, entry_field2
    print "scanning"
    delete_current_users()
    domain= target_ip_range.get()
    
    
    if '/' not in domain and domain :
        new_clients= ask_for_users(domain)
        for client in new_clients:
            user= User(client, 7070)
            if user.scan_port():
                user.authenticate()
            Users.append(user)
        if domain not in new_clients:
            user= User(domain, 7070)
            user.port_scanned= True
            user.authenticate()
            Users.append(user)  
        
    elif domain:
        
        new_clients= scan(domain)
        for client in new_clients:
            user= User(client, 7070)
            if user.scan_port():
                user.authenticate()
            Users.append(user)
    
    add_clients(buttons, left_frame, Users)


#..............................................................................stuff

def ask_for_users(domain):
    print "asking::", domain, "  for users list"
    c= socket(AF_INET, SOCK_STREAM)
    c.connect((domain, 7070))
    print "connected to ", domain, " to scan users"
    c.send("scan".encode())
    msg= c.recv(2048)
    print "recieved: ", msg
    users= msg.split('/')
    users.pop(-1)
    return users
    
    
def ask_for_auth(domain, user, pw):
    print "asking::", domain, "  for aut"
    c= socket(AF_INET, SOCK_STREAM)
    c.connect((domain, 7070))
    print "connected to ", domain, " to auth"
    c.send("authme".encode())
    msg= c.recv(2048)
    if msg=="yes":
        return True
    else: return False
    
def scan(ip):
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1,verbose=False)[0]
    clients_list = []
    for element in answered_list:
        clients_list.append(element[1].psrc)
        
    return clients_list




def delete_current_users():
    global buttons, Users
    for button in buttons:
        button.pack_forget()
    
    del buttons[:]
    del Users[:]
    
    

def add_clients (buttons, left_frame, Users):
    counter= 0
    for user in Users:
        color= "blue" if user.port_scanned else "powder blue"
        t= user.view
        button= Button(left_bottom_frame, text= t, width= 150, relief= FLAT, bg= color, command=lambda index= counter: connect(index))
        counter+= 1
        button.pack()
        buttons.append(button)
  
        


def find_by_address(address):
    for index, button in enumerate(buttons):
        if button['text']== address:
            return index
    return -1



def send_recv_event():
    
    if not recv_q.empty():
        message=  "--> " + recv_q.get()
        msg_list.insert(END, message)
    left_frame.after(500, send_recv_event)
    
def can_send_file(file_name):
    global m
    
    c= socket(AF_INET, SOCK_STREAM)
    ip= Users[m.index].IP
    c.connect((ip, 7070))
    c.send("file".encode())
    c.send(file_name.encode())
    msg= c.recv(1024)
    
    print "waiting for reply for sending file or not"
    if msg== "yes": return True
    else: return False
        
def check_event():
    global m
    if not waiting_addresses_queue.empty() and not waiting_clients_queue.empty():
        address= waiting_addresses_queue.get()
        client= waiting_clients_queue.get()
        index= find_by_address(address[0])
        if index>-1:
            buttons[index].config(bg= "green")
        close_opened_connections()
        m= Chat_object(client, send_q, recv_q, index)
    right_frame.after(4000, check_event)
    right_frame.after(7000, community_service)
    left_frame.after(500, send_recv_event)
    
def community_service():
    if not requests.empty():
        request= requests.get()
        
        if request== "scan":
            put_users()
            
        if request== "authme":
            user= requests.get()
            pw= requests.get()
            print "community service is active for: ", user, " : ", pw
            if custom_auth(user, pw):
                answers.put("yes")
            else: answers.put("no")
        
        if request== "file":
            filename= requests.get()
            #per_win= Toplevel()
           # Label(per_win, text= "want to receive"+ filename+ "?").pack()
            #Button(per_win, text= "yes", command= acceptfile(filename) ).pack()
          #  Button(per_win, text= "no", command= denyfile ).pack()
            acceptfile(filename)
        answers.put("end")
    right_frame.after(3000, community_service) 


def denyfile():
    answers.put("no")

def acceptfile(filename):
    answers.put("yes")
    
    msg_list.insert(END, "recieving file...")
    directory= filedialog.askdirectory()
    server= socket(AF_INET, SOCK_STREAM)
    server.bind(("", 8080))
    server.listen(1)
    print "waiting to recieve file"
    c, a= server.accept()
    print "got a connection"
    with open(os.path.join(directory, filename), 'w') as file:
        data= c.recv(1024)
        while data != "end":
            print "getting data"
            file.write(data)
            data= c.recv(1024)
    msg_list.insert(END, "done")
    
    
def put_users():
    global Users
    
    for user in Users:
        answers.put(user.IP)
    
def send_file():
    global m
    if m is None:
        print "no connection to send file to"
        return 

    file_name= filedialog.askopenfilename()
    print "file name", file_name
    if not can_send_file(file_name):
        print "other user declined the send file request"
        return
    
    print "user accepted to receive file"
    print "conneccting to him"
    c= socket(AF_INET, SOCK_STREAM)
    ip= Users[m.index].IP
    c.connect((ip, 8080))   
    
    print "connection established"
    
    f = open(file_name, "r")
    msg_list.insert(END, "sending file...")
    
    l = f.read(1024)
    while l:
        print "sending data"
        c.send(l.encode())
        l= f.read(1024)
    c.send("end".encode())
    msg_list.insert(END, "done")
        
def authenticate():
    global my_data
    domain= target_ip_range.get()
    
    if '/' not in domain and domain :
        user= my_msg2.get()
        pw= my_msg3.get()
        if ask_for_auth(domain, user, pw):
            login_button['bg']= "green"
            my_data.editUsername(user)
        else: login_button['bg']= "blue"
        
    else:
        if authenticate_mail(my_msg2.get(), my_msg3.get()):
            login_button['bg']= "green"
            username= my_msg2.get()
            my_data.editUsername(username)
        else: login_button['bg']= "blue"
        
def custom_auth(user, pw):
    print "custom_scanning: ", user, " : ", pw
    return authenticate_mail(user, pw)
#..............................................................................................................        
#..............................................................................................................
#..............................................................................................................
#..............................................................................................................        
#..............................................................................................................
#..............................................................................................................

def main_menu():
    global root, my_msg, msg_list,target_ip_range, top_frame, right_frame, left_frame
    global left_bottom_frame, left_top_frame, my_msg2, my_msg3, login_button
    root= Tk()
    root.geometry("700x450")
    
    top_frame= Frame(root, width= 700, height= 50, bg= "gray", relief= SUNKEN)
    top_frame.pack_propagate(0)
    left_frame= Frame(root, width= 200, height= 400, bg= "steel blue", relief= SUNKEN)
    left_frame.pack_propagate(0)
    left_frame.grid_propagate(0)
    right_frame= Frame(root, width= 500, height= 400, bg= "powder blue", relief= SUNKEN)
    right_frame.pack_propagate(0)
    right_frame.grid_propagate(0)
    top_frame.pack( side= TOP)
    right_frame.pack(side= RIGHT)
    left_frame.pack( side= LEFT)
    
    left_top_frame= Frame(left_frame, width= 200, height= 35, bg= "steel blue", relief= SUNKEN)
    left_top_frame.pack_propagate(0)
    left_top_frame.grid_propagate(0)
    left_bottom_frame= Frame(left_frame, width= 200, height= 350, bg= "steel blue", relief= SUNKEN)
    left_bottom_frame.pack_propagate(0)
    left_bottom_frame.grid_propagate(0)
    left_top_frame.pack(side= TOP)
    left_bottom_frame.pack()
    
    right_top_frame= Frame(right_frame, width= 500, height= 25, bg= "steel blue", relief= FLAT)
    right_middle_frame= Frame(right_frame, width= 500, height= 350, bg= "powder blue", relief= FLAT)
    right_bottom_frame= Frame(right_frame, width= 500, height= 25, bg= "steel blue", relief= FLAT)
    right_top_frame.pack_propagate(0)
    right_middle_frame.pack_propagate(0)
    right_bottom_frame.pack_propagate(0)
    right_top_frame.grid_propagate(0)
    right_middle_frame.grid_propagate(0)
    right_bottom_frame.grid_propagate(0)
    right_top_frame.pack()
    right_middle_frame.pack()
    right_bottom_frame.pack()
    
    my_msg = StringVar()
    my_msg2 = StringVar()
    my_msg3 = StringVar()
    
    entry_field = Entry(right_bottom_frame, textvariable=my_msg, bg= "yellow", width= 50)
    login_button= Button(right_top_frame, text= "auth", command= authenticate, bg= "powder blue", relief= FLAT)
    file_button= Button(right_top_frame, text= "send file", command= send_file, bg= "powder blue", relief= FLAT)
    entry_field2 = Entry(right_top_frame, textvariable=my_msg2, bg= "powder blue", width= 25)
    entry_field3 = Entry(right_top_frame, textvariable=my_msg3, show="*", bg= "powder blue", width= 25)
    entry_field2.grid(row= 0, column= 0)
    entry_field3.grid(row= 0, column= 1)
    login_button.grid(row= 0, column= 2)
    file_button.grid(row= 0, column= 3)
    entry_field.pack()
    entry_field.bind("<Return>", send)
    
    target_ip_range = StringVar() 
    entry_field2 = Entry(left_top_frame, textvariable=target_ip_range, bg= "yellow", width= 25)
    entry_field2.grid(row=0, column=0)
    
    scan_button= Button(left_top_frame, text= "scan", command= scan_callback, bg= "yellow", relief= FLAT)
    scan_button.grid(row= 0, column= 1)
    
    msg_list = Listbox(right_middle_frame, height=100, width=100, bg= "powder blue", relief= FLAT)
    msg_list.pack(side= RIGHT)
    
    right_frame.after(5000, check_event)
    server_thread= Thread(target= handle_incoming_connections, 
                          args= (server, waiting_clients_queue, waiting_addresses_queue,))
    server_thread.daemon= True
    server_thread.start()

    server_thread2= Thread(target= handle_incoming_queries, 
                          args= (server2, requests, answers, ))
    server_thread2.daemon= True
    server_thread2.start()
    
    #button1= Button(left_frame, text= "hi", width= 150, command= reset)
    #button1.pack()
    #buttons.append(button1)
    
    
    #top_frame.after(1000, stuff)
    
 
    
    root.mainloop()


main_menu()

close_opened_connections()