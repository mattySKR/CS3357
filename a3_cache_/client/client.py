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

    # Command line argument retrieval.
    client_args = sys.argv

    # If -proxy is a part of command line argument then we use cache.
    if client_args[1] == '-proxy':

        # Extracting the cache address.
        parsed_cache_addr = sys.argv[2]
        split_cache_host_port = parsed_cache_addr.split(':')

        # Host value for cache.
        cache_host = split_cache_host_port[0]

        # Port value for cache.
        cache_port = split_cache_host_port[1]

        # Extracting the url.
        parsed_server_url = sys.argv[3]
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
        cache_directory = ''

        # Directory + filename.
        final_path = ''

        # If just the filename in path.
        if url_length == 4:
            server_filename += split_url[3]
            final_path += '/' + server_filename

        # If dir/filename.
        elif url_length == 5:
            server_filename += split_url[4]
            cache_directory += split_url[3]
            final_path += '/' + cache_directory + '/' + server_filename

        # If dir/dir/filename.
        elif url_length == 6:
            server_filename += split_url[5]
            cache_directory += split_url[3] + '/' + split_url[4]
            final_path += '/' + cache_directory + '/' + server_filename

        # If dir/dir/dir/filename.
        elif url_length == 7:
            server_filename += split_url[6]
            cache_directory += split_url[3] + '/' + split_url[4] + '/' + split_url[5]
            final_path += '/' + cache_directory + '/' + server_filename

        # If dir/dir/dir/dir/filename.
        elif url_length == 8:
            server_filename += split_url[7]
            cache_directory += split_url[3] + '/' + split_url[4] + '/' + split_url[5] + '/' + split_url[6]
            final_path += '/' + cache_directory + '/' + server_filename

        print('Connecting to cache proxy ...')

        # Creating the client socket to connect to cache.
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((cache_host, int(cache_port)))
        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.')
            sys.exit(1)

        # The connection was successful, so we can prep and send our message.
        print('Connection to cache proxy established. Sending message...\n')

        # Preparing and sending the get message to cache proxy.
        message = prepare_get_message(server_host, server_port, final_path)
        client_socket.send(message.encode())

        # Receiving the response from cache.
        response_line = get_line_from_socket(client_socket)
        response_list = response_line.split(' ')
        headers_done = False

        # If an error is returned from the server, we dump everything sent and
        # exit right away.
        if response_list[1] != '200':
            print('Error:  An error response was received from the cache proxy.  Details:\n')
            print(response_line)
            bytes_to_read = 0

            while not headers_done:
                header_line = get_line_from_socket(client_socket)
                header_list = header_line.split(' ')
                if header_line == '':
                    headers_done = True
                elif header_list[0] == 'Content-Length:':
                    bytes_to_read = int(header_list[1])
            print_file_from_socket(client_socket, bytes_to_read)
            sys.exit(1)

        # If it's OK, we retrieve and write the file out.
        else:

            print('Success:  Cache proxy is sending file.  Downloading it now.')

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

    # We go straight to the server (since -proxy is not in command line arg)
    else:

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

        # If just the filename in path.
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
        print('Connection to server established. Sending message...\n')

        # Preparing and sending the get message to cache proxy.
        message = prepare_get_message(server_host, server_port, final_path)
        client_socket.send(message.encode())

        # Receive the response from the server and start taking a look at it.
        response_line = get_line_from_socket(client_socket)
        response_list = response_line.split(' ')
        headers_done = False

        # If an error is returned from the server, we dump everything sent and
        # exit right away.
        if response_list[1] != '200':
            print('Error:  An error response was received from the server.  Details:\n')
            print(response_line)
            bytes_to_read = 0

            while not headers_done:
                header_line = get_line_from_socket(client_socket)
                header_list = header_line.split(' ')
                if header_line == '':
                    headers_done = True
                elif header_list[0] == 'Content-Length:':
                    bytes_to_read = int(header_list[1])
            print_file_from_socket(client_socket, bytes_to_read)
            sys.exit(1)

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
