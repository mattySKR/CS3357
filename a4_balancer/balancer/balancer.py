import socket
import os
import sys
import datetime
import signal
import random

# Define a constant for our buffer size.
BUFFER_SIZE = 1024

# Define an expiration time constant for the cached item.
TIMEOUT_VALUE = 120.00

# Define the file name to use from the performance test
PERFORMANCE_TEST_FILE = 'test.jpg'


# A function for creating HTTP GET messages.
def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'
    return request


# Create an HTTP response.
def prepare_response_message(value, server_info, server_file):

    message = 'HTTP/1.1 '
    if value == '301':
        message = message + value + ' Moved Permanently' + ' \r\n' + 'Location: ' + 'http://' + str(server_info) + str(server_file) + ' \r\n'
    return message


# Send the given response and file back to the client.
def send_response_to_client(sock, code, s_info, s_file, file_name):

    if (file_name.endswith('.html')) or (file_name.endswith('.htm')):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    # Get size of file.
    file_size = os.path.getsize(file_name)

    # Construct header and send it.
    header = prepare_response_message(code, s_info, s_file) + 'Content-Type: ' + type + ' \r\n' + 'Content-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it.
    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break


# Read a file from the socket and print it out.  (For errors primarily.)
def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while bytes_read < bytes_to_read:
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())


# Signal handler for graceful exiting.
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)


# Retrieve servers' host and port from the command line and put them
# into a 2D-array in an organized fashion.
def extract_servers_from_com_line(length, args):

    server_2d_array = []
    # if one server in the list
    if length > 1:

        server1 = args[1].split(':')
        server_2d_array = [[server1[0],server1[1]]]

        if length > 2:

            server2 = args[2].split(':')
            server_2d_array = [[server1[0],server1[1]], [server2[0], server2[1]]]

            if length > 3:

                server3 = args[3].split(':')
                server_2d_array = [[server1[0],server1[1]], [server2[0], server2[1]], [server3[0], server3[1]]]

                if length > 4:

                    server4 = args[4].split(':')
                    server_2d_array = [[server1[0],server1[1]], [server2[0], server2[1]], [server3[0], server3[1]], [server4[0], server4[1]]]

                    if length > 5:

                        server5 = args[5].split(':')
                        server_2d_array = [[server1[0],server1[1]], [server2[0], server2[1]], [server3[0], server3[1]], [server4[0], server4[1]],
                                           [server5[0], server5[1]]]

    else:

        print('Not enough arguments')

    return server_2d_array


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
def get_line_from_client(sock):

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


# Save file from socket
def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while bytes_read < bytes_to_read:
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)


# Determines the max range for the interval from which
# the random number will be chosen
def list_index_max_range(list_size):

    max_range = 0
    if list_size == 2:
        max_range = 3
    elif list_size == 3:
        max_range = 6
    elif list_size == 4:
        max_range = 10
    elif list_size == 5:
        max_range = 15
    elif list_size == 6:
        max_range = 21

    return max_range


# Picks the index from the list based on the
# random number pick
def server_picker(rand_num):

    index_chosen = 0
    if rand_num == 1:
        index_chosen = 0

    elif rand_num in range(2,4):
        index_chosen = 1

    elif rand_num in range(4,7):
        index_chosen = 2

    elif rand_num in range(7,11):
        index_chosen = 3

    elif rand_num in range(11,16):
        index_chosen = 4

    elif rand_num in range(16,22):
        index_chosen = 5

    return index_chosen



# Our main function.
def main():

    # Run balancer as server forever.
    while True:

        balancer_args = sys.argv
        args_length = len(balancer_args)

        server_array = extract_servers_from_com_line(args_length, balancer_args)

        print('Connecting to the servers from the list ...')
        print('Please wait ...\n')

        # Initializing
        balancer_sockets = [None] * (args_length-1)
        performance_times = [0] * (args_length-1)

        # Getting all the connections to servers
        for x in range(0, args_length-1):

            # Creating the client socket to connect to cache.
            try:

                balancer_sockets[x] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                balancer_sockets[x].connect((server_array[x][0],int(server_array[x][1])))
                print('Connection to server established at: ' + server_array[x][0] + ':' + server_array[x][1] + '\n')

            except ConnectionRefusedError:
                print('Error:  That host or port is not accepting connections.')
                return False

            # Preparing and sending the get message to cache proxy.
            message = prepare_get_message(server_array[x][0], int(server_array[x][1]), PERFORMANCE_TEST_FILE)
            balancer_sockets[x].send(message.encode())

            # Time before the transfer
            timestamp_before = datetime.datetime.now().timestamp()

            # Receiving the response from server.
            done = False
            line = ''
            while not done:
                char = balancer_sockets[x].recv(1).decode()
                if char == '\r':
                    pass
                elif char == '\n':
                    done = True
                else:
                    line = line + char

            # Receiving the response from cache.
            response_line = line
            response_list = response_line.split(' ')
            headers_done = False

            if response_list[1] != '200':
                print('Error:  An error response was received from server.\n')

            # If it's OK, we retrieve and write the file out.
            else:

                # Go through headers and find the size of the file, then save it.
                bytes_to_read = 0

                while not headers_done:

                    done = False
                    line = ''
                    while not done:
                        char = balancer_sockets[x].recv(1).decode()
                        if char == '\r':
                            pass
                        elif char == '\n':
                            done = True
                        else:
                            line = line + char

                    header_line = line
                    header_list = header_line.split(' ')
                    if header_line == '':
                        headers_done = True
                    elif header_list[0] == 'Content-Length:':
                        bytes_to_read = int(header_list[1])

                # Saving the file
                with open(PERFORMANCE_TEST_FILE, 'wb') as file_to_write:
                    bytes_read = 0
                    while bytes_read < bytes_to_read:
                        chunk = balancer_sockets[x].recv(BUFFER_SIZE)
                        bytes_read += len(chunk)
                        file_to_write.write(chunk)

                # Time after the transfer is complete
                timestamp_after = datetime.datetime.now().timestamp()

                # Getting the difference between before and after times
                timestamp_final = timestamp_after - timestamp_before

                # Putting the times in the array along with server info for each time
                performance_times[x] = str(timestamp_final) + ':' + str(server_array[x][0]) + ':' + str(server_array[x][1])

        print('Executing a performance test on servers ... Please hang on ...')
        print('List of server performance times is finalized ...\n')

        # Sorting from slowest to fastest times
        performance_times = sorted(performance_times, reverse=True)

        # -------------------------------------------------------
        # We are now ready to accept the requests from the client
        # -------------------------------------------------------

        # Register our signal handler for shutting down.
        signal.signal(signal.SIGINT, signal_handler)

        # Create the socket.  We will ask this to work on any interface and to pick
        # a free port at random.  We'll print this out for clients to use.
        balancer_socket_for_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        balancer_socket_for_client.bind(('', 0))
        print('Will wait for client connections at port ' + str(balancer_socket_for_client.getsockname()[1]))
        balancer_socket_for_client.listen(1)
        # Setting the timeout value
        balancer_socket_for_client.settimeout(TIMEOUT_VALUE)

        # Keep the server running forever.
        while 1:

            # Getting the max range for the random number pick based on the array size
            max_range_for_randomizer = list_index_max_range(len(performance_times))

            # Generating the random number in the proper range
            random_pick = random.randint(1,max_range_for_randomizer)

            #  Now, we get the index for the performance_times list, which
            # determines the chosen server based on the random number generator
            chosen_index = server_picker(random_pick)

            # Extracting the chosen server info from the list
            server_chosen = str(performance_times[chosen_index])
            server_chosen_list = server_chosen.split(':')
            server_chosen_host = server_chosen_list[1]
            server_chosen_port = server_chosen_list[2]
            server_for_client = server_chosen_host + ':' + server_chosen_port

            print('Waiting for incoming client connection ...')

            try:
                conn, addr = balancer_socket_for_client.accept()
                print('Accepted connection from client address:', addr)
                print('Connection to client established, waiting to receive message...\n')

            except:
                break

            # We obtain our request from the socket.  We look at the request and
            # figure out what to do based on the contents of things.
            request = get_line_from_client(conn)
            request_list = request.split()
            req = request_list[0] + ' ' + request_list[1] + ' ' + request_list[2]
            print('Received request:  ' + req + '\n')

            print('Redirecting the client to the server ... Please hang on ...')
            print('Client has been redirected ...')

            # Extracting the filename from the request
            server_req_filename = request_list[1]

            # Sending 301 message to client with Location: header
            send_response_to_client(conn, '301', server_for_client, server_req_filename, '301.html')

            conn.close()


if __name__ == '__main__':
    main()

