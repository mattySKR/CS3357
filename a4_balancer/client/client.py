import socket
import sys


# Define a constant for our buffer size.
BUFFER_SIZE = 1024


# A function for creating HTTP GET messages.
def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'
    return request


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.
def get_line_from_socket(sock):

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


# Based on the implemented get request
# in client, this function will extract the whole request.
def get_line_from_balancer(sock):

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
            elif counter == 5:
                done = True
            else:
                done = False
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


# Our main function.
def main():

    parsed_server_url = sys.argv[1]
    split_url = parsed_server_url.split('/')
    split_server_host_port = split_url[2].split(':')

    # Host value for server.
    server_host = split_server_host_port[0]

    # Port value for cache.
    server_port = split_server_host_port[1]

    # Getting the length of the url list.
    url_length = len(split_url)

    # Filename to retrieve.
    server_filename = ''

    # Directory to create in cache.
    server_directory = ''

    # Directory + filename.
    final_path = ''

    # If just the filename in path. This stuff is irrelevant in
    # this assignment implementation. As mentioned in README file
    if url_length == 4:
        server_filename += split_url[3]
        final_path += '/' + server_filename

    # If dir/filename.
    elif url_length == 5:
        server_filename += split_url[4]
        server_directory += split_url[3]
        final_path += '/' + server_directory + '/' + server_filename

    # If dir/dir/filename.
    elif url_length == 6:
        server_filename += split_url[5]
        server_directory += split_url[3] + '/' + split_url[4]
        final_path += '/' + server_directory + '/' + server_filename

    # If dir/dir/dir/filename.
    elif url_length == 7:
        server_filename += split_url[6]
        server_directory += split_url[3] + '/' + split_url[4] + '/' + split_url[5]
        final_path += '/' + server_directory + '/' + server_filename

    # If dir/dir/dir/dir/filename.
    elif url_length == 8:
        server_filename += split_url[7]
        server_directory += split_url[3] + '/' + split_url[4] + '/' + split_url[5] + '/' + split_url[6]
        final_path += '/' + server_directory + '/' + server_filename

    print('Connecting to server ...')

    # Creating the client socket to connect to server.
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, int(server_port)))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # The connection was successful, so we can prep and send our message.
    print('Connection to load balancer established. Sending message...\n')

    # Preparing and sending the get message to cache proxy.
    message = prepare_get_message(server_host, server_port, final_path)
    client_socket.send(message.encode())

    # Receive the response from the server and start taking a look at it.
    response_line = get_line_from_socket(client_socket)

    response_list = response_line.split(' ')

    response_list2 = get_line_from_socket(client_socket)
    print(response_line + '\n' + response_list2 + '\n')
    updated_url = response_list2.split(' ')[1]

    split_url_list = updated_url.split('/')

    server_file = split_url_list[3]
    server_updated_host = split_url_list[2].split(':')[0]
    server_updated_port = split_url_list[2].split(':')[1]
    headers_done = False

    # If an error is returned from the server, we dump everything sent and
    # exit right away.
    if response_list[1] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        bytes_to_read = 0

        while not headers_done:
            header_line = get_line_from_socket(client_socket)
            header_list = header_line.split(' ')
            if header_line == '':
                headers_done = True
            elif header_list[0] == 'Content-Length:':
                bytes_to_read = int(header_list[1])
        print_file_from_socket(client_socket, bytes_to_read)

    # --------------------------------------------------------------------
    # At this point we have being redirected by the balancer to the server
    # --------------------------------------------------------------------

    print('Connecting to the redirected server ...')

    # Creating the client socket to connect to server.
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_updated_host, int(server_updated_port)))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # The connection was successful, so we can prep and send our message.
    print('Connection to redirected server established. Sending message...\n')

    # Preparing and sending the get message to cache proxy.
    message = prepare_get_message(server_updated_host, server_updated_port, server_file)
    client_socket.send(message.encode())

    # Receive the response from the server and start taking a look at it.
    response_line = get_line_from_socket(client_socket)
    response_list = response_line.split(' ')
    headers_done = False

    # If an error is returned from the server, we dump everything sent and
    # exit right away.
    if response_list[1] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        bytes_to_read = 0

        while not headers_done:
            header_line = get_line_from_socket(client_socket)
            header_list = header_line.split(' ')
            if header_line == '':
                headers_done = True
            elif header_list[0] == 'Content-Length:':
                bytes_to_read = int(header_list[1])
        print_file_from_socket(client_socket, bytes_to_read)

    # If it's OK, we retrieve and write the file out.
    else:

        print('Success:  Server is sending file.  Downloading it now.')

        # If requested file begins with a / we strip it off.
        while server_filename[0] == '/':
            server_filename = server_filename[1:]

        # Go through headers and find the size of the file, then save it.
        bytes_to_read = 0
        while not headers_done:
            header_line = get_line_from_socket(client_socket)
            header_list = header_line.split(' ')
            if header_line == '':
                headers_done = True
            elif header_list[0] == 'Content-Length:':
                bytes_to_read = int(header_list[1])
        save_file_from_socket(client_socket, bytes_to_read, server_filename)

if __name__ == '__main__':
    main()
