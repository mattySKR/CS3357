from socket import *
import os


# creating TCP welcoming socket
server_socket = socket(AF_INET,SOCK_STREAM)

# -------------------------------------------------SOME FUNCTIONS----------------------------------------------------------------------------------------------------------------


# adds ./ in the case of 'filename' or adds . in the case of '/filename'
def file_starts_with_slash(the_input_list):

    if the_input_list[1].startswith('/'):

        fl = '.' + the_input_list[1]
    else:
        fl = './' + the_input_list[1]

    return fl

# file reader
def str_reader(f_name):

    f = open(f_name, 'r')
    f1 = f.read()
    f.close()
    return f1

# ---------------------------------------------------ALL

try:

    # binding with a port number
    server_socket.bind(('localhost', 8000))

    # server will listen to one client connection only (TCP requests)
    server_socket.listen(1)

    # running infinitely
    while True:

        # when the client establishes a connection, the server accepts/completes the connection with client
        connection_socket,client_address = server_socket.accept()

        # receive and decode the request from the client
        get_from_client = connection_socket.recv(4096).decode()

        # splitting the request so we can properly add . or ./ to the file name
        formatted_input = get_from_client.split()
        stripped_filename = file_starts_with_slash(formatted_input)
        print(stripped_filename)

        # if the file DNE
        if not os.path.isfile(stripped_filename):

            header1 = '\n\nHTTP/1.1 404 Not Found\r\n\n'
            final_string1 = str_reader('404.html')
            header1 += final_string1
            connection_socket.send(header1.encode())

        # if error 505
        elif 'HTTP/1.1' not in formatted_input:

            header2 = '\n\nHTTP/1.1 505 Version Not Supported\r\n\n'
            final_string2 = str_reader('505.html')
            header2 += final_string2
            connection_socket.send(header2.encode())

        # if error 501
        elif 'HTTP/1.1' in formatted_input and 'GET' not in formatted_input:

            header3 = '\n\nHTTP/1.1 501 Method Not Implemented\r\n\n'
            final_string3 = str_reader('505.html')
            header3 += final_string3
            connection_socket.send(header3.encode())

        # if image or gif
        elif ('.jpg' or '.jpeg' or '.gif') in stripped_filename:

            msg = '\nHTTP/1.1 200 OK\r\n'

            # open file and read bytes
            b1 = open(stripped_filename, 'rb')
            b2 = b1.read()
            b1.close()
            # file length
            cont_length = len(b2)

            msg += 'Content-Length: %d\r\n' % cont_length

            if ('.jpg' or '.jpeg') in stripped_filename:
                msg += 'Content-Type: jpg/jpeg; charset = utf-8\r\n'

            else:
                msg += 'Content-Type: gif; charset = utf-8\r\n'

            # send the header go client
            connection_socket.send(msg.encode())

            # open file and read in bytes
            bin_f = open(stripped_filename, "rb")

            # while the whole is not transferred, keep going
            while True:

                # read the file contents into the client socket
                connection_socket.send(bin_f.read())

                # if reached the end of the file (0 byte):
                if not bin_f.read():
                    break

            bin_f.close()

        # if the file is txt or html
        else:

            text_or_html_file = str_reader(stripped_filename)
            file_to_client = '\nHTTP/1.1 200 OK\r\n'
            file_to_client += 'Content-Length: %d\r\n' % len(text_or_html_file.encode())
            file_to_client += text_or_html_file
            connection_socket.send(file_to_client.encode())

        # closing the client socket connection
        connection_socket.close()

except KeyboardInterrupt:
    print('\nServer shutting down due to user interrupt...\n')

except Exception as exc:
    print('Error occurred:\n')
    print(exc)

# close the server connection
server_socket.close()

