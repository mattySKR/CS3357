from socket import *
import argparse

# creating parser
parser = argparse.ArgumentParser()

# adding arguments to the parser
parser.add_argument(action='store', dest='host_name',  help='host name the server is executing on')
parser.add_argument(type=int, action='store', dest='port_number',  help='port number the server is listening to')
parser.add_argument(action='store', dest='file_name',  help='name of the file to download')

args = parser.parse_args()

# setting up the client socket
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((args.host_name, args.port_number))  # connecting with the server given the server name and port number

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

print('\n\nSince the file name is already mentioned through command line, you only need to input the method and HTTP version for the request')
print('Type the command below. Need to type --> GET HTTP/1.1\n')

list1 = input()
list1 = list1.split()

# inserting the file name argument in between 'GET' and 'HTTP/1.1' (in the case of the proper request)
list1.insert(1, args.file_name)

# ----------------------------------------------------SOME FUNCTIONS----------------------------------------------------------------------------------------------------------


def list_to_string(s):

    str1 = ' '
    return str1.join(s)

client_input = list_to_string(list1)


# stripping of anything to just have a file name
def filename_abort_slash(f_name):

    if f_name.startswith('/'):

        strip = f_name.split('/')
        return strip[1]

    else:
        return f_name

# --------------------------------------SENDING REQUEST AND RECEIVING RESPONSE FROM SERVER------------------------------------------------------------------------------------

# sending request to the server
client_socket.send(client_input.encode())

# receiving response from the server
server_response = client_socket.recv(8192).decode()

# --------------------------------------ACCEPTING/PROCESSING DIFFERENT SERVER RESPONSES---------------------------------------------------------------------------------------

# if error 505 or 501
if ('505' or '501') in server_response:

    print(server_response)

# if client request was approved by the server
elif 'Content-Length' in server_response:

    # if the requested file is html or text
    if 'Content-Type' not in server_response:

        stripped_filename = filename_abort_slash(args.file_name)
        file_to_save1 = open(stripped_filename, "a")
        file_to_save1.write(server_response)

        # getting the rest of the chunks from the server
        while True:

            # keep receiving the file chunks
            server_response_the_rest = client_socket.recv(4096).decode()
            file_to_save1.write(server_response_the_rest)

            # if all the chunks transferred then exit then finished
            if not server_response_the_rest:
                break

        file_to_save1.close()

        # opening the locally saved file to read its lines
        file_to_save2 = open(stripped_filename, "r")
        lines = file_to_save2.read().splitlines()

        file_to_save2.close()

        # printing out the header
        print(lines[0])
        print(lines[1])
        print(lines[2])
        print('\n')

        # deleting the header stuff from the file
        del lines[0:3]

        # overwriting the same local file with the final contents so that we get the file the client requested
        finale_file = open(stripped_filename, "w")
        line = '\n'.join(lines)
        finale_file.write(line)

        finale_file.close()

    # if the requested file is .jpeg or .jpg or .gif
    else:

        stripped_filename = filename_abort_slash(args.file_name)

        bin_header1 = server_response
        bin_header2 = bin_header1.split('\n')
        print('\n'.join(bin_header2))

        file_to_save1 = open(stripped_filename, "wb")

        # getting the rest of the chunks from the server
        while True:

            file_to_save1.write(client_socket.recv(8192))

            # if all the chunks transferred then exit then finished
            # if not server_response_the_rest:
            if not client_socket.recv(8192):
                break

        file_to_save1.close()

# if the requested file does not exist (404)
else:

    print(server_response)


client_socket.close()

