import socket 
from _thread import *
import sys
from collections import defaultdict as df
import time
import os

class Server:
    def __init__(self):
        self.rooms = df(list)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def accept_connections(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.server.bind((self.ip_address, int(self.port)))
        self.server.listen(100)

        while True:
            connection, address = self.server.accept()
            print(str(address[0]) + ":" + str(address[1]) + " Connected")

            start_new_thread(self.clientThread, (connection,))

        self.server.close()

    def clientThread(self, connection):
        user_id = connection.recv(1024).decode().replace("User ", "")
        room_id = connection.recv(1024).decode().replace("Join ", "")

        if room_id not in self.rooms:
            self.rooms[room_id] = [(connection, user_id)]  # Create a new room
            connection.send("New Group created".encode())
            self.broadcast(f"{user_id} joined the chat", connection, room_id)
        else:
            self.rooms[room_id].append((connection, user_id))
            connection.send("Welcome to chat room".encode())
            self.broadcast(f"{user_id} joined the chat", connection, room_id)

        while True:
            try:
                message = connection.recv(1024)
                print(str(message.decode()))
                if message:
                    if str(message.decode()) == "FILE":
                        self.broadcastFile(connection, room_id, user_id)
                    elif message.decode().startswith("@"):
                        self.sendPrivateMessage(message.decode(), room_id)
                    else:
                        message_to_send = "<" + str(user_id) + "> " + message.decode()
                        self.broadcast(message_to_send, connection, room_id)

                else:
                    self.remove(connection, room_id)
                    self.broadcast(f"{user_id} left the chat", None, room_id)
                    break
            except Exception as e:
                print(repr(e))
                print("Client disconnected earlier")
                break
    
    def broadcastFile(self, connection, room_id, user_id):
        file_name = connection.recv(1024).decode()
        lenOfFile = connection.recv(1024).decode()
        file_dir = f"shared_files/{room_id}"
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, file_name)

        for client, _ in self.rooms[room_id]:
            if client != connection:
                try: 
                    client.send("FILE".encode())
                    time.sleep(0.1)
                    client.send(file_name.encode())
                    time.sleep(0.1)
                    client.send(lenOfFile.encode())
                    time.sleep(0.1)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

        total = 0
        print(file_name, lenOfFile)
        with open(file_path, 'wb') as file:
            while str(total) != lenOfFile:
                data = connection.recv(1024)
                total += len(data)
                for client, _ in self.rooms[room_id]:
                    if client != connection:
                        try: 
                            client.send(data)
                        except:
                            client.close()
                            self.remove(client, room_id)
                file.write(data)
        print("File received and stored:", file_path)

    def broadcast(self, message_to_send, connection, room_id):
        for client, _ in self.rooms[room_id]:
            if client != connection:
                try:
                    client.send(message_to_send.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

    def sendPrivateMessage(self, message, room_id):
        recipient, private_message = message.split(" ", 1)
        recipient = recipient[1:]  # Remove "@" symbol
        for client, user_id in self.rooms[room_id]:
            if user_id == recipient:
                try:
                    client.send(f"(Private) {user_id}: {private_message}".encode())
                except:
                    client.close()
                    self.remove(client, room_id)
    
    def remove(self, connection, room_id):
        if connection in [client for client, _ in self.rooms[room_id]]:
            self.rooms[room_id] = [(client, user_id) for client, user_id in self.rooms[room_id] if client != connection]


if __name__ == "__main__":
    ip_address = "192.168.236.73"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)
