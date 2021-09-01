import socket
import os
import sys
import time
import datetime
import signal


# Define a constant for our buffer size.
BUFFER_SIZE = 1024

# Define an expiration time constant for the cached item.
EXPIRATION_TIME = 120


# A function for creating HTTP GET messages.
def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'
    return request


# A function for creating HTTP Conditional GET messages.
def prepare_conditional_get_message(file_name, tstamp):
    request = f'GET {file_name} HTTP/1.1\r\nIf-modified-since: {tstamp}\r\n\r\n'
    return request


# Based on the implemented get request
# in client, this function will extract the whole request.
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


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.
def get_line_from_server(sock):

    done = False
    line = ''
    while not done:
        char = sock.recv(1).decode()
        if char == '\r':
            pass
        elif char == '\n':
            done = True
        else:
            line = line + char
    return line


# Read a file from the socket and print it out.  (For errors primarily.)
def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while bytes_read < bytes_to_read:
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())


# Read a file from the socket and save it out.
def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while bytes_read < bytes_to_read:
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)


# Also reads a file from the socket, but modified to
# save it out to the appropriate directory.
def save_file_from_server(sock, bytes_to_read, dir_path, filename):

    f_path = dir_path + '/' + filename
    with open(f_path, 'wb') as file_to_write:
        bytes_read = 0
        while bytes_read < bytes_to_read:
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)


# Interrupt for shutting down (also used on server.)
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)


# Response message to client function that is also used on server.
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
    elif value == '523':
        message = message + value + ' Origin Is Unreachable\r\n' + date_string + '\r\n'
    return message


# Sends the response to the client with all the appropriate info
# Also used on server.
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


# Our main function.
def main():

    # Signal for shutting down
    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.
    # Same way as on server.
    cache_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cache_socket.bind(('', 0))
    print('Cache proxy is waiting for client connections at port ' + str(cache_socket.getsockname()[1]))
    cache_socket.listen()

    while 1:

        print('Cache proxy is waiting for incoming client connection ...')
        conn, addr = cache_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...\n')

        # Receive the request from client.
        request = get_line_from_socket(conn)
        print('Received request:  ' + request + '\n')
        request_list = request.split()

        # If we did not get a GET command respond to client with a 501.
        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_response_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond to client with a 505.
        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_response_to_client(conn, '505', '505.html')

        # We have the right request and version, so check if file exists.
        else:

            # If requested file begins with a / we strip it off.
            req_file = request_list[1]

            # Splitting the host:port into 2 parts.
            server_info = request_list[4].split(':')

            # Host value for the server.
            server_host = server_info[0]

            # Port value for the server.
            server_port = server_info[1]

            # Creating another cache socket for communication with the server.
            try:

                cache_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cache_socket2.connect((server_host, int(server_port)))

            # If not able to connect to server, then send 523 message to client and quit.
            except ConnectionRefusedError:

                print('Error:  That host or port is not accepting connections.')
                print('Sending "523 - Origin Is Unreachable" message to client ...\n')
                send_response_to_client(conn,'523','523.html')
                sys.exit(1)

            # If we have directories followed by the filename then split them apart.
            dir_file_list = os.path.split(req_file)

            # Define the name of the directory to be created.
            path_for_file = server_host + '_' + server_port + dir_file_list[0]

            # Separating the path from the filename.
            naked_filename = dir_file_list[1]

            # Path/filename format.
            client_file = path_for_file + '/' + naked_filename

            # If the requested file not in cache then retrieve from server.
            if not os.path.exists(client_file):

                print('Requested file does not exist in cache ...')
                print('Connecting to the server to retrieve the file ...')

                # The connection was successful, so we can prep and send our message.
                print('Connection to server established. Sending message...\n')

                # Send original GET request to the server.
                message = prepare_get_message(server_host, server_port, req_file)
                cache_socket2.send(message.encode())

                # Receiving the response from the server.
                response_line = get_line_from_server(cache_socket2)
                response_list = response_line.split(' ')
                headers_done = False

                # If the server does not have the requested file,
                # then send 404 message to the client.
                if response_list[1] == '404':

                    print('Requested file does not exist ... responding with error!')
                    print('Checking if there exists a previously cached version ...')

                    # Checking to see if cache had previously cached the file
                    # that the server does not have anymore. If so, then delete
                    # the cached version.
                    if os.path.exists(client_file):

                        try:
                            os.remove(client_file)
                            print('Previously cached version has also been deleted ...')

                        except OSError as e:
                            print('Error: %s : %s' % (client_file, e.strerror))

                    # Otherwise, do nothing.
                    else:
                        print('No such version ...')

                    print('Sending 404 error to the client ...\n')
                    send_response_to_client(conn, '404', '404.html')

                # Otherwise receive the file from server and send to client.
                else:

                    print('Success:  Server is sending file.  Downloading it now.')

                    # Checking if the requested path already exists
                    # to avoid the error from duplicate directories.
                    if not os.path.exists(path_for_file):

                        # Creating the needed path.
                        os.makedirs(path_for_file)

                    # Otherwise, do nothing.
                    else:
                        pass

                    # Go through headers and find the size of the file, then save it.
                    bytes_to_read = 0
                    while not headers_done:
                        header_line = get_line_from_server(cache_socket2)
                        header_list = header_line.split(' ')
                        if header_line == '':
                            headers_done = True
                        elif header_list[0] == 'Content-Length:':
                            bytes_to_read = int(header_list[1])
                    save_file_from_server(cache_socket2, bytes_to_read, path_for_file, naked_filename)

                    print('Requested file good to go!  Sending file ...')
                    send_response_to_client(conn,'200', client_file)

            # Cache has the file locally, so do the timestamp stuff.
            else:

                # Timestamp of the requested file in cache.
                last_modified = os.path.getmtime(client_file)

                # Current time.
                curr_time = time.time()

                # Subtracting the cache file timestamp from the current time
                # to compare with EXPIRATION_TIME constant.
                expiry_indicator = curr_time - last_modified

                # If the file has not expired, then check if the server
                # has the modified version of that file.
                if expiry_indicator < EXPIRATION_TIME:

                    print('File has NOT expired ...')
                    print('Issuing a conditional GET request to web server to check if the server version has been modified since then')
                    print("Connecting to the server now ...")
                    print('Connection to server established. Sending message...\n')

                    # Send a conditional GET request to the server.
                    message = prepare_conditional_get_message(req_file, last_modified)
                    cache_socket2.send(message.encode())

                    # Receive the response from the server.
                    response_line = get_line_from_server(cache_socket2)
                    response_list = response_line.split(' ')
                    headers_done = False

                    # In case the server version was deleted
                    if response_list[1] == '404':

                        # Checking to see if cache had previously cached the file
                        # that the server does not have anymore. If so, then delete
                        # the cached version.
                        if os.path.exists(client_file):

                            print('Requested file does not exist ... responding with error!')
                            try:
                                os.remove(client_file)
                                print('Previously cached version has also been deleted ...')

                            except OSError as e:
                                print('Error: %s : %s' % (client_file, e.strerror))

                        # Otherwise, do nothing.
                        else:
                            print('No such version ...')

                        print('Sending 404 error to the client ...\n')
                        send_response_to_client(conn, '404', '404.html')

                    # If server sends 304 message, then send 304 message to the client.
                    elif response_list[1] == '304':

                        bytes_to_read = 0
                        while not headers_done:
                            header_line = get_line_from_server(cache_socket2)
                            header_list = header_line.split(' ')
                            if header_line == '':
                                headers_done = True
                            elif header_list[0] == 'Content-Length:':
                                bytes_to_read = int(header_list[1])
                        print_file_from_socket(cache_socket2, bytes_to_read)

                        print('\nRequested file has not been modified ...')
                        print('Sending the cached version to the client!\n')

                        send_response_to_client(conn, '200', client_file)

                    # Otherwise, the file has been modified,
                    # so receive the new version and update its own, accordingly.
                    else:

                        bytes_to_read = 0
                        while not headers_done:
                            header_line = get_line_from_server(cache_socket2)
                            header_list = header_line.split(' ')
                            if header_line == '':
                                headers_done = True
                            elif header_list[0] == 'Content-Length:':
                                bytes_to_read = int(header_list[1])
                        save_file_from_server(cache_socket2, bytes_to_read, path_for_file, naked_filename)

                        print('Requested file good to go!  Sending file ...')
                        send_response_to_client(conn,'200', client_file)

                # If the cache file version has expired, then get the requested file
                # from the server.
                else:

                    print('Requested file has expired ...')
                    print('Connecting to the server to retrieve the file ...')
                    print('Connection to server established. Sending message...\n')

                    # Send an original GET request to the server.
                    message = prepare_get_message(server_host, server_port, req_file)
                    cache_socket2.send(message.encode())

                    # Receive the response from the server.
                    response_line = get_line_from_socket(cache_socket2)
                    response_list = response_line.split(' ')
                    headers_done = False

                    # If the server does not have the requested file,
                    # then send 404 message to the client.
                    if response_list[1] == '404':

                        # Checking to see if cache had previously cached the file
                        # that the server does not have anymore. If so, then delete
                        # the cached version.
                        if os.path.exists(client_file):

                            print('Requested file does not exist ... responding with error!')
                            try:
                                os.remove(client_file)
                                print('Previously cached version has also been deleted ...')

                            except OSError as e:
                                print('Error: %s : %s' % (client_file, e.strerror))

                        # Otherwise, do nothing.
                        else:
                            print('No such version ...')

                        print('Sending 404 error to the client ...\n')
                        send_response_to_client(conn, '404', '404.html')

                    # Otherwise, download the file from server and send to the client.
                    else:

                        print('Success:  Server is sending file.  Downloading it now.')
                        bytes_to_read = 0
                        while not headers_done:
                            header_line = get_line_from_server(cache_socket2)
                            header_list = header_line.split(' ')
                            if header_line == '':
                                headers_done = True
                            elif header_list[0] == 'Content-Length:':
                                bytes_to_read = int(header_list[1])
                        save_file_from_server(cache_socket2, bytes_to_read, path_for_file, naked_filename)

                        print('Requested file good to go!  Sending file ...')
                        send_response_to_client(conn,'200', client_file)

        # We are all done with this client, so close the connection and
        # Go back to get another one!

        conn.close()


if __name__ == '__main__':
    main()
