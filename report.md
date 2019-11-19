<h1>COMP3331 Computer Networks</h1> 
<h1>Assignment Report</h1>

<p align="center">Written by Yutong, Ji. </p>

<p align="center">zid: z5191511</p>

<h2>Program Design</h2>

This assignment is using python3.7, which can be run via command `python3 server.py [server_port] [block_duration] [timeout]` for server and `python3 client.py localhost [server_port]` for client.

For this project, there are four python files and a txt file, namely `server.py`, `client.py`, `user.py` and `help_functions.py` and `credientials.txt`. 

The `server.py` implements most of server functionality and it is using python OOP together with multithreading to handle multiple connections with clients and realise the communication between clients and server. Generally, the threads are allocated accrodingly. The server itself uses two threads without connecting to any client, one for the timer and another one to listen for connections from clients. Whenever a client is accepted from the server, a new thread is created to deal with the commnuication with this client, if this client leaves the chat, this thread associated with the client will be closed. 

The `client.py` implements the client side application, which supports both Client-server and P2P communications. Mulit-threading is also applied to establish P2P connections. The client is easy to set up, after connecting to server, it can start messging to server through command line interface. All the messaged typed in will be processed and sent to server. However, the client will only do minor message process which are related to P2P communications, other commands related to server will be processed at server side.

The `user.py` is a help file for server. It only has a user class which stores all relevant information of a client object and some methods to manipulate the data. It makes easier for the server to store, get and handle requests from clients.

The `help_functions.py` only has few functions help to transform data format or user finding.  

<h2>Message format</h2>

#### Message format

client to server:

`<command> <name(if require)> <other information(if necessary)>`

Sever to client:

- error
  - `Error: <error detail>`
- others
  - `System: <other information>`

#### Description

All the messages sending between client and server are a single string, different parts are separated by space. To be more specific, the first word of the string always be an indicator. For instance, if a message `message Yoda hi` is sent to server, the first word `message` tells the server that it is asking for a messaging service. Similarly, if it starts with `broadcast`, it is a broadcast message. However, if the first word is not recognised by the server, an error message will be sent back to the client. To inform the client there is an error message, all error messages will begin with `Error`. 

Warnings and some other messages sent from server will start with `System:` except messages generated from `broadcast`(not the login, logout message) and `message` commands.  

<h2>System description</h2>



<h2>Design issues and future improvements</h2>

