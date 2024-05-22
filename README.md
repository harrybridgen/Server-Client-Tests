# MiniQuest Client-Server Test

This repository contains a simple client-server tests for 2D games.
It consists of 3 tests, each in its own directory: `test1`, `test2`, and `test3`.

* Test1 uses TCP and JSON to send messages between the client and server.
* Test2 uses TCP and strings to send messages between the client and server.
* Test3 uses UDP and strings to send messages between the client and server. Test3 also implements client-side prediction and event based updates.

## Requirements
* Python
* Pip
* PyGame

## Getting Started

To run the a client and server, follow these steps:

1. Clone this repository to your local machine.
2. Open a terminal and navigate to a `server` directory with the following command:
    ```
    cd clientservertest/testX/server
    ```
        
3. Run the following command to start the server:

    ```
    python server.py
    ```

4. Open another terminal and navigate to a `client` directory with the following command:
    ```
    cd clientservertest/testX/client
    ```
        
5. Run the following command to start the client:

    ```
    python client.py
    ```

## Usage

Once the client and server are running, you can interact with the client application. The client will send requests to the server, and the server will respond accordingly.

 
