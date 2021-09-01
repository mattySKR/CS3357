import socket
import os
import datetime
import signal
import sys
import time

# Constant for our buffer size.
BUFFER_SIZE = 1024


# Signal handler for graceful exiting.
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)


# Create an HTTP response.
def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '304':
        message = message + value + ' Version Not Modified\r\n' + date_string + '\r\n'
    return message


# Send the given response and file back to the client.
def send_response_to_client(sock, code, file_name):

    # Determine content type of file.
    if (file_name.endswith('.jpg')) or (file_name.endswith('.jpeg')):
        type = 'image/jpeg'
    elif file_name.endswith('.gif'):
        type = 'image/gif'
    elif file_name.endswith('.png'):
        type = 'image/jpegpng'
    elif (file_name.endswith('.html')) or (file_name.endswith('.htm')):
        type = 'text/html'
    else:
        type = 'application/octet-stream'
    
    # Get size of file.
    file_size = os.path.getsize(file_name)

    # Construct header and send it.
    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it.
    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break


# Based on the implemented get and conditional get requests
# in client or cache, we will extract the whole request
def get_line_from_socket(sock):

    done = False
    line = ''
    counter = 0
    while not done:
        char = sock.recv(1).decode()
        if char == '\r':
            pass
        elif char == '\n':
            counter = counter + 1
            if counter == 1:
                line = line + char
            elif counter == 3:
                done = True
            else:
                done = False
        else:
            line = line + char
    return line


# Our main function.
def main():

    # Register our signal handler for shutting down.
    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)
    
    # Keep the server running forever.
    while 1:

        print('Waiting for incoming client connection ...')
        conn, addr = server_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...\n')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.
        request = get_line_from_socket(conn)
        request_list = request.split()

        # If requested file begins with a / we strip it off.
        req_file = request_list[1]
        while req_file[0] == '/':
            req_file = req_file[1:]

        # Properly prints out the conditional GET from cache
        if request.split()[3] == 'If-modified-since:':

            cond_request = request.split()
            print('Received request: ' + cond_request[0] + ' ' + cond_request[1] +
                  ' ' + cond_request[2] + '\n' + cond_request[3] + ' ' +
                  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(cond_request[4]))) + ' GMT\n')

        # Otherwise it is not a conditional GET, so print out normally
        else:
            print('Received request:  ' + request + '\n')

        # If we did not get a GET command respond with a 501.
        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_response_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond with a 505.
        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_response_to_client(conn, '505', '505.html')

        # If the cache requests the version check for the file.
        elif (request_list[3] == 'If-modified-since:') & (os.path.exists(req_file)):
            print('Checking the timestamp of the requested file ...')

            modified_rfc = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(request_list[4]))) + ' GMT'

            # If requested file begins with a / we strip it off.
            req_file = request_list[1]
            while req_file[0] == '/':
                req_file = req_file[1:]

            # Get the timestamp of the server's file version.
            server_file_timestamp = os.path.getmtime(req_file)

            # Checking if the requested file has been modified since and if so then.
            if server_file_timestamp > float(request_list[4]):

                print('The requested file has been modified since ', modified_rfc)
                print('Preparing to send the newer version now ...')
                print('Sending an updated version to cache!\n')
                send_response_to_client(conn, '200', req_file)

            # If not modified, then send '304 Not Modified' back
            else:
                print('The requested file has not been modified since ...')
                print('Sending "304 - Not Modified" to cache!\n')
                send_response_to_client(conn, '304', '304.html')

        # We have the right request and version, so check if file exists.
        else:

            # If requested file begins with a / we strip it off.
            req_file = request_list[1]
            while req_file[0] == '/':
                req_file = req_file[1:]

            # Check if requested file exists and report a 404 if not.
            if not os.path.exists(req_file):
                print('Requested file does not exist ... responding with error!\n')
                send_response_to_client(conn, '404', '404.html')

            # File exists, so prepare to send it!
            else:
                print('Requested file good to go!  Sending file ...\n')
                send_response_to_client(conn, '200', req_file)
                
        # We are all done with this client, so close the connection and
        # Go back to get another one!
        conn.close()

if __name__ == '__main__':
    main()

