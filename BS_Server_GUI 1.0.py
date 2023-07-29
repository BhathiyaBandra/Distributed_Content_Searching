from tkinter import *
import socket
from random import shuffle
import threading
import datetime

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 12310  # Port to listen on (non-privileged ports are > 1023)

maximum_length = 100
users = []

server_status = False


def message_with_length(message):
    '''
    Helper function to prepend the length of the message to the message itself
    Args:
        message (str): message to prepend the length
    Returns:
        str: Prepended message
    '''
    message = " " + message
    message = str((10000+len(message)+5))[1:] + message
    message = bytes(message, encoding='utf-8')
    return message


def check_ip_address(ip_address):
    try:
        socket.inet_aton(ip_address)
        return ip_address
    except socket.error:
        raise ValueError

# Register message
def REG(message):
    msg_data = {'IP_address': '',
                'port_no':'',
                'username': ''
                }
    # Check whether the message fields are ok
    try: 
        msg_data['IP_address'] = str(message[2].strip())
        msg_data['port_no'] = int(message[3].strip())
        msg_data['username'] = str(message[4].strip())
    except Exception as e:
        display_message(e)
        return "REGOK 9999"   # Return Error message if the fields have some error
    
    # [ i[2] for i in users] returns the username list

    if msg_data['username'] in [ i[2] for i in users]:
        return "REGOK 9998"
    elif msg_data['IP_address'] + ":" + str(msg_data['port_no']) in [ i[0] + ':' + str(i[1]) for i in users]:
        return "REGOK 9997"
    elif len(users)>maximum_length:
        return "REGOK 9996"
    else:
        val = ''
        if len(users)>= 2:
            user_list = [i for i in range(len(users))]
            shuffle(user_list)
            val = users[user_list[0]][0] + ' ' + str(users[user_list[0]][1]) + ' ' + users[user_list[1]][0] + ' ' + str(users[user_list[1]][1]) + ' '
            users.append([msg_data['IP_address'], msg_data['port_no'], msg_data['username']])

            display_message("----------User list ------------")
            for i in users:
                display_message(i)
            display_message("----------End of user list ------------")
            
            return "REGOK 2 " + val
        elif len(users) == 1:
            val = str(users[0][0]) + " " + str(users[0][1])
            users.append([msg_data['IP_address'], msg_data['port_no'], msg_data['username']])
            
            display_message("----------User list ------------")
            for i in users:
                display_message(i)
            display_message("----------End of user list ------------")

            return "REGOK 1 " + val
        else:
            users.append([msg_data['IP_address'], msg_data['port_no'], msg_data['username']])

            display_message("----------User list ------------")
            for i in users:
                display_message(i)
            display_message("----------End of user list ------------")

            return "REGOK 0"


# Unregister message
def UNREG(message):
    msg_data = {'IP_address': '',
                'port_no':'',
                'username': ''
                }
            
    try: 
        msg_data['IP_address'] = str(message[2].strip())
        msg_data['port_no'] = int(message[3].strip())
        msg_data['username'] = str(message[4].strip())
    except Exception as e:
        display_message(e)
        return "REGOK 9999"
    
    if msg_data['username'] in [ i[2] for i in users]:
        if msg_data['IP_address'] + ":" + str(msg_data['port_no']) in [ i[0] + ':' + str(i[1]) for i in users]:
            for indx in range(len(users)):
                if (msg_data['IP_address'] == users[indx][0]) and (msg_data['port_no'] == users[indx][1]) and (msg_data['username'] == users[indx][2]):
                    del users[indx]
                    return "UNROK 0"
            else:
                return "REGOK 9999"


#Parse the incoming messages
def parse_message(message):
    try:
        msg_type = message[1]
        
        # Register Message
        if msg_type.upper() == 'REG':
            return REG(message)
        elif msg_type.upper() == 'UNREG':
            return UNREG(message)
    except Exception as e:
        display_message(f'error in received message {" ".join(message)}')
        display_message(e)

  

##_______________________ GUI _______________________

root = Tk()

root.title("Boostrap Server")
# specify size of window.
root.geometry("700x400")

# Create label
l = Label(root, text = "Boostrap Server")
l.config(font =("Courier", 14))
l.grid(row=0, column=0)


# Get Server Details
Server_IP_Label = Label(root, text = "Server IP: ")
Server_IP_Label.grid(row=1, column=0)

Server_IP_value = Entry(root, bd = 5)
Server_IP_value.grid(row=1, column=1)
Server_IP_value.insert(0, HOST)

Server_Port_Label = Label(root, text = "Server Port: ")
Server_Port_Label.grid(row=1, column=3)

Server_Port_value = Entry(root, bd = 5)
Server_Port_value.grid(row=1, column=4)
Server_Port_value.insert(0, str(PORT))


def display_message(content):
    message_display.config(state= NORMAL)
    message_display.insert(END, f'[{str(datetime.datetime.now())}] ')
    message_display.insert(END, content)
    message_display.insert(END, "\n")
    message_display.config(state= DISABLED)

# Start the server
def Boostrap_server():
    global server_status, HOST, PORT
    
    HOST = Server_IP_value.get()
    PORT = int(Server_Port_value.get())
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while server_status:
            client_socket, address = s.accept()
            data = client_socket.recv(1024).decode()
            if data == 'stop':
                display_message("-----------------Server Stopped-----------------")
                break
            display_message(f'Connection from {address} has been established!')
            data = data.split(" ")
            display_message(data)
            response = parse_message(data)
            response = message_with_length(response)
            client_socket.send(response)
            client_socket.close()
        start_button['state'] = NORMAL
        stop_button['state'] = DISABLED

def start_server():
    global listenThread, server_status,users
    users = []
    listenThread = threading.Thread(target=Boostrap_server, daemon=True)
    start_button['state'] = DISABLED
    stop_button['state'] = NORMAL
    server_status = True
    listenThread.start()
    message_display.config(state= NORMAL)
    message_display.delete("1.0","end")
    message_display.config(state= DISABLED)
    display_message('-----------Boostrap Server Started------------')

def stop_server():
    global server_status
    server_status = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"stop")
        


# Create button for start.
start_button = Button(root, text = "Start", command = start_server)
start_button.grid(row=1, column=5)

# Create button for stop.
stop_button = Button(root, text = "stop", command = stop_server, state=DISABLED)
stop_button.grid(row=1, column=6)

# Create text widget and specify size.
message_display = Text(root, height = 20, width = 90)
message_display.grid(row=2, column=0, columnspan =20)
scrollb = Scrollbar(root, command=message_display.yview)
scrollb.grid(row=2, column=16, sticky='nsew')
message_display['yscrollcommand'] = scrollb.set

mainloop()
