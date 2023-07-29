from tkinter import *
import socket
from random import shuffle
import threading
import datetime



BS_HOST = "127.0.0.1"  # The boostrap server's hostname or IP address
BS_PORT = 12310  # The port used by the server

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 12311  # The port used by the server
USERNAME = "vjinsavkjsanvj"


root = Tk()

root.title("Client")
# specify size of window.
root.geometry("800x650")

# Create label
l = Label(root, text = "Client")
l.config(font =("Courier", 14))
l.grid(row=0, column=0)

search_file_found = False

class Client:
    def __init__(self, BS_HOST, BS_PORT, MY_HOST, MY_PORT, MY_USERNAME) -> None:
        self.BS_HOST = BS_HOST
        self.BS_PORT = BS_PORT
        self.MY_HOST = MY_HOST
        self.MY_PORT = MY_PORT
        self.MY_USERNAME = MY_USERNAME
        self.CONNECT_TO_BS_OK = False
        self.TTL = 20
        self.SEARCH_FILE_FOUNDS = []  # list to store the found files [IP, PORT, FILE_LIST]
        self.SEARCH_FILE_TIMEOUT = 5  # Search file timeout delay in seconds
        self.peer_clients = []        #[[IP, HOST, CONNCETION_STATUS(0: connected, -1: not connceted)]]
        self.MY_FILES = []
        self.ROUTING = []

    def message_with_length(self, message):
        message = " " + message
        message = str((10000+len(message)+5))[1:] + message
        message = bytes(message, encoding='utf-8')
        return message
    
    def connect_to_bs(self):
        #self.unreg_from_bs()
        message = "REG "+ self.MY_HOST + " " +str(self.MY_PORT) +" " + self.MY_USERNAME

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.MY_HOST, self.MY_PORT))
                s.connect((self.BS_HOST, self.BS_PORT))
                s.send(self.message_with_length(message))
                data = s.recv(1024).decode()
                display_event(data)
                
                toks = data.split(" ")
                
                if (len(toks) < 3):
                    raise RuntimeError("Invalid message")
                
                if (toks[1] != "REGOK"):
                    raise RuntimeError("Registration failed")
                
                num = int(toks[2])
                if (num < 0):
                    raise RuntimeError("Registration failed")
                    
                if num == 9999:
                    self.CONNECT_TO_BS_OK = False
                    display_event("failed, there is some error in the command")
                elif num == 9998:
                    self.CONNECT_TO_BS_OK = False
                    display_event("failed, already registered to you, unregister first")
                elif num == 9997:
                    self.CONNECT_TO_BS_OK = False
                    display_event(" failed, registered to another user, try a different IP and port")
                elif num == 9996:
                    self.CONNECT_TO_BS_OK = False
                    display_event("failed, can’t register. BS full.")
                elif (num == 0):
                    self.CONNECT_TO_BS_OK = True
                    self.peer_clients = []
                elif (num == 1):
                    self.CONNECT_TO_BS_OK = True
                    self.peer_clients = [[toks[3], int(toks[4]), -1]]
                else:
                    self.CONNECT_TO_BS_OK = True
                    self.peer_clients = [[toks[3], int(toks[4]), -1], [toks[5], int(toks[6]), -1]]
                display_event(self.peer_clients)
                return num
            except Exception as e:
                self.CONNECT_TO_BS_OK = False
                display_event(e)
    
    def unreg_from_bs(self):
        buffer_size = 1024
        message = "UNREG " + self.MY_HOST + " " + str(self.MY_PORT) + " " + self.MY_USERNAME
        
        display_event("---------Unregistering from Boostrap Server----------")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.BS_HOST, self.BS_PORT))
            s.send(self.message_with_length(message))
            display_event(self.message_with_length(message))
            data = s.recv(buffer_size)
            display_event(data)
    
    def leave_peers(self):
        buffer_size = 1024
        message = "LEAVE " + self.MY_HOST + " " + str(self.MY_PORT)
        display_event("---------Leaving Peers----------")
        for peers in self.peer_clients:
            if peers[2] == 0:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peers[0], peers[1]))
                    s.send(self.message_with_length(message))
                    display_event(self.message_with_length(message))
                    data = s.recv(buffer_size)
                    display_event(data)
    
    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.MY_HOST, self.MY_PORT))
            s.listen()
            try:
                while (self.CONNECT_TO_BS_OK):
                    client_socket, address = s.accept()
                    display_event(f'Connection from {address} has been established!')
                    data = client_socket.recv(1024).decode()
                    display_event(data)
                    if data == 'stop':
                        self.unreg_from_bs()
                        self.leave_peers()
                        self.SEARCH_FILE_FOUNDS = []  
                        self.peer_clients = []
                        self.MY_FILES = []
                        self.ROUTING = []
                        break
                    message = data.split(" ")

                    try:
                        msg_type = message[1]

                        if msg_type == 'JOIN':                              # --- Join Message -----
                            try:
                                routing = [message[2],                      # IP address of the join node
                                        int(message[3])]                    # Port of the join node
                                if message[2] + ":" +str(message[3]) not in ([i[0] + ":" +str(i[1]) for i in self.ROUTING]):
                                    self.ROUTING.append(routing)            # Add new node to the routing table
                                reply = "JOINOK 0"                          # Return join ok message
                                client_socket.send(self.message_with_length(reply))

                                display_event("-------- Joined Users : ---------")
                                for dat in self.ROUTING:
                                    display_event(dat)
                                display_event("-------- End of joined users : ---------")

                            except:
                                reply = "JOINOK 9999"
                                client_socket.send(self.message_with_length(reply))     # Send reply
                            
                        elif msg_type == 'LEAVE':                           # --- Leave Message -----
                            try:
                                ip = message[2]                             # IP address of the unregistering node
                                host = int(message[3])                      # Port of the unregistering node
                                for i in range(len(self.ROUTING)):
                                    if (self.ROUTING[i][0] == ip) and (self.ROUTING[i][1] == host):
                                        del self.ROUTING[i]                 # Remove the routing from the routing table
                                        break
                                reply = "LEAVEOK 0"
                                client_socket.send(self.message_with_length(reply))     # Send reply

                                display_event("-------- Joined Users : ---------")
                                for dat in self.ROUTING:
                                    print(dat)
                                display_event("-------- End of joined users : ---------")

                            except:
                                reply = "LEAVEOK 9999"                      # leave failed
                                client_socket.send(self.message_with_length(reply))     # Send reply   
                        
                        elif msg_type == 'SER':                             # --- Search Message -----
                            number_of_hops = int(message[-1])               # Remaining number of hops
                            
                            if number_of_hops > 0:
                                search_file_name = message[-2].lower()  # Search file name
                                self.get_my_files()
                                found_files = []                            # Array to store searched file name
                                for i in self.MY_FILES:
                                    if search_file_name in i.lower():
                                        found_files.append(i)
                                
                                if len(found_files)>0:                      # File found locally
                                    display_event("File Found Locally")
                                    reply = "SEROK " +str(len(found_files)) + " " + self.MY_HOST + " " + str(self.MY_PORT) + " " + str(number_of_hops) + " " + " ".join(found_files)
                                    display_event(reply)
                                    try:
                                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as searching_host:
                                            searching_host.connect((message[2], int(message[3])))
                                            searching_host.send(self.message_with_length(reply))     # Send reply
                                    except Exception as e:
                                        display_event("Error in sending already found search results")
                                        display_event(e)
                                else:                                      # File not found locally. Forward the requests to other peer hosts
                                    reply = "SER " + message[2] + " " + message[3] + " " + search_file_name + " " + str(number_of_hops - 1)         
                                    for clients in self.ROUTING:
                                        if not (clients[0] == message[2] and int(message[3]) == clients[1]):
                                            try:
                                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as searching_host:
                                                    searching_host.connect((clients[0], clients[1]))
                                                    searching_host.send(self.message_with_length(reply))     # Send reply
                                            except Exception as e:
                                                display_event("Error in forwarding")
                                                display_event(clients)
                                                display_event(e)

                        elif msg_type == 'SEROK':
                            file_count = int(message[2])
                            if file_count != 0:
                                found_files = message[6:]
                                found_files = [i.replace("\_","$change_this$").replace("_", " ").replace("$change_this$","_") for i in found_files]
                                display_search(f'IP : {message[3]} port : {message[4]} conatains the following files with # of hops :{message[5]}')
                                display_search("\t" + "\n\t".join(found_files))
                                self.SEARCH_FILE_FOUNDS.append([message[3], message[4], found_files])
                            else:
                                display_search(f'No files are found from IP: {message[3]} Port {message[4]}')
                    except Exception as e:
                        display_event(e)
            except KeyboardInterrupt:
                display_event('interrupted!')

    def join_with_peers(self):
        if len(self.peer_clients) > 0:
            Join_Message = 'JOIN ' + self.MY_HOST + " " + str(self.MY_PORT)
            Join_Message = self.message_with_length(Join_Message)
            display_event("--- Join with peers -------")
            for peers in self.peer_clients:
                display_event(f'Trying to connect IP: {peers[0]} and port: {peers[1]}')
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peers[0], peers[1]))
                    s.sendall(Join_Message)
                    data = s.recv(1024).decode()
                    message = data.split(" ")
                    if message[1] == 'JOINOK':
                        peers[2] = int(message[2])
                        if int(message[2]) == 0:
                            self.ROUTING.append([peers[0], peers[1]])
                    display_event(peers)

            display_event("--- Finish Join with peers -------")
    
    def send_messages(self, IP, PORT, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((IP, PORT))
            message = message.replace("my_host", self.MY_HOST).replace("my_port", str(self.MY_PORT))
            message = self.message_with_length(message)
            display_event(f'Sending a message: {message}')
            s.sendall(message)
    
    def search_file(self, file_name):
        self.SEARCH_FILE_FOUNDS = []
        file_name = file_name.strip()
        file_name = file_name.replace("_", "\_")
        file_name = file_name.replace(" ", "_")
        SEARCH_MESSAGE = "SER " + self.MY_HOST + " " + str(self.MY_PORT) + " " + file_name + " " + str(self.TTL)
        for users in self.ROUTING:
            try:
                SENDING_IP = users[0]
                SENDING_PORT = int(users[1])
                self.send_messages(SENDING_IP, SENDING_PORT, SEARCH_MESSAGE)
            except Exception as e:
                display_event("Error in input message")
                display_event(e)
        start_time = datetime.datetime.now()
        while ((datetime.datetime.now() - start_time).total_seconds() < self.SEARCH_FILE_TIMEOUT):
            None
        if len(self.SEARCH_FILE_FOUNDS)>0:
            display_search(f'----------Files found from {len(self.SEARCH_FILE_FOUNDS)} # of nodes------')
        else:
            display_search(f'----------No files have found before timeout------')
            
    def get_my_files(self):
        file_list = my_file_value.get().split("\n")
        file_list = [i.strip().replace("_","\_").replace(" ","_") for i in file_list]
        self.MY_FILES = file_list
    
    def stop_client_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.MY_HOST, self.MY_PORT))
            s.sendall(b"stop")

def display_event(content):
    show_events.config(state= NORMAL)
    show_events.insert(END, f'[{str(datetime.datetime.now())}] ')
    show_events.insert(END, content)
    show_events.insert(END, "\n")
    show_events.config(state= DISABLED)

def display_search(content):
    search_results.config(state= NORMAL)
    search_results.insert(END, content)
    search_results.insert(END, "\n")
    search_results.config(state= DISABLED) 
     
# Start the server
def start_client():
    global BS_HOST, BS_PORT, HOST, PORT, USERNAME, client, listenThread
    
    BS_HOST = Boostrap_Server_IP_value.get()
    BS_PORT = int(Boostrap_Server_Port_value.get())
    HOST = Client_Server_IP_value.get()
    PORT = int(Client_Server_Port_value.get())
    USERNAME = Client_Server_username_value.get()
    client = Client(BS_HOST, BS_PORT, HOST, PORT, USERNAME)
    client.connect_to_bs()
    client.join_with_peers()
    listenThread = threading.Thread(target=client.listen, daemon=True)
    listenThread.start()
    if client.CONNECT_TO_BS_OK:
        start_button['state'] = DISABLED
        stop_button['state'] = NORMAL
        search_button['state'] = NORMAL

def stop_client():
    global client
    client.stop_client_server()
    start_button['state'] = NORMAL
    stop_button['state'] = DISABLED
    search_button['state'] = DISABLED
    
def search_files():
    search_results.config(state= NORMAL)
    search_results.delete("1.0","end")
    if len(search_file_name_value.get())>0:
        search_results.insert(END, f'[{str(datetime.datetime.now())}] ')
        search_results.insert(END, f'Searching file name: {search_file_name_value.get()}')
        search_results.insert(END, "\n")
        searchThread = threading.Thread(target=client.search_file, args=(search_file_name_value.get(),), daemon=True)
        searchThread.start()
        search_results.config(state= DISABLED)
    else:
        search_results.insert(END, f'Enter a file name to search...')
        search_results.config(state= DISABLED)


##_______________________ GUI _______________________

# Get Server Details
Boostrap_Server_IP_Label = Label(root, text = "Boostrap Server IP: ")
Boostrap_Server_IP_Label.grid(row=1, column=0)

Boostrap_Server_IP_value = Entry(root, bd = 5)
Boostrap_Server_IP_value.grid(row=1, column=1)
Boostrap_Server_IP_value.insert(0, BS_HOST)

Boostrap_Server_Port_Label = Label(root, text = "Boostrap Server Port: ")
Boostrap_Server_Port_Label.grid(row=1, column=3)

Boostrap_Server_Port_value = Entry(root, bd = 5)
Boostrap_Server_Port_value.grid(row=1, column=4)
Boostrap_Server_Port_value.insert(0, str(BS_PORT))

Client_Server_IP_Label = Label(root, text = "My IP: ")
Client_Server_IP_Label.grid(row=2, column=0)

Client_Server_IP_value = Entry(root, bd = 5)
Client_Server_IP_value.grid(row=2, column=1)
Client_Server_IP_value.insert(0, HOST)

Client_Server_Port_Label = Label(root, text = "My Port: ")
Client_Server_Port_Label.grid(row=2, column=3)

Client_Server_Port_value = Entry(root, bd = 5)
Client_Server_Port_value.grid(row=2, column=4)
Client_Server_Port_value.insert(0, str(PORT))

Client_Server_username_Label = Label(root, text = "My Username: ")
Client_Server_username_Label.grid(row=2, column=5)

Client_Server_username_value = Entry(root, bd = 5)
Client_Server_username_value.grid(row=2, column=6)
Client_Server_username_value.insert(0, USERNAME)

# Create button for start.
start_button = Button(root, text = "Start", command = start_client)
start_button.grid(row=2, column=7)

# Create button for stop.
stop_button = Button(root, text = "stop", command = stop_client, state=DISABLED)
stop_button.grid(row=2, column=8)



#_____________________My files___________________
# Create my file label
my_file_name_Label = Label(root, text = "My files: ")
my_file_name_Label.grid(row=3, column=0)

my_file_value= Text(root, height = 5, width = 88)
my_file_value.grid(row=4, column=0, columnspan =20)
scrollb_my_file = Scrollbar(root, command=my_file_value.yview)
scrollb_my_file.grid(row=4, column=8, sticky='nsew')
my_file_value['yscrollcommand'] = scrollb_my_file.set
my_file_value.insert(END,"Adventures of Tintin\nJack and Jill\nGlee\nThe Vampire Diarie\nKing Arthur\nWindows XP")

#_____________________Search files___________________
# Create Search box to find files
search_file_name_Label = Label(root, text = "Search File: ")
search_file_name_Label.grid(row=5, column=0)

search_file_name_value = Entry(root, bd = 5)
search_file_name_value.grid(row=5, column=1)

# Create button for search.
search_button = Button(root, text = "Search", command = search_files, state=DISABLED)
search_button.grid(row=5, column=3,)

# Create text widget and specify size.
search_results = Text(root, height = 10, width = 88, state=DISABLED)
search_results.grid(row=6, column=0, columnspan =20)
scrollb_search_results = Scrollbar(root, command=search_results.yview)
scrollb_search_results.grid(row=6, column=8, sticky='nsew')
search_results['yscrollcommand'] = scrollb_search_results.set

#_____________________Events___________________
# Create event label
show_events_Label = Label(root, text = "Events log: ")
show_events_Label.grid(row=7, column=0)

# Create text widget and specify size.
show_events = Text(root, height = 15, width = 88, state=DISABLED)
show_events.grid(row=8, column=0, columnspan =20)
scrollb_show_events = Scrollbar(root, command=show_events.yview)
scrollb_show_events.grid(row=8, column=8, sticky='nsew')
show_events['yscrollcommand'] = scrollb_show_events.set

mainloop()



