Assignment #4.

server
------

To run the server, execute in a separate terminal window:

  python3 server.py

depending on the version, might need to use python instead of python3. Each server instance will output the host and port info for balancer to use.



balancer
--------

To run the server, execute in a separate terminal window:

  python3 balancer.py host:port host:port host:port and so on 

For example:

  python3 balancer.py localhost:11111 localhost:22222 localhost:333333 localhost:44444 localhost:555555

depending on the version, might need to use python instead of python3. I have decided for balancer to support 5 servers only.

TIMOUT TIME and the NAME of test.jpg file were defined as constants inside balancer.py file. Balancer will use test.jpg file for performance tests.

*** The command line argument has to be typed manually after all the servers are running in order for balancer to start executing. Also, based on how I have implemented the balancer, the balancer execution can be terminated through KeyboardInterrupt only when one of the servers shut down. So, if you want to KeyboardInterrupt the balancer.py, then KeyboardInterrupt one of the servers. ***



client 
------

Client will be executed last.

  python3 client.py http://host:port/file

depending on the version, might need to use python instead of python3. In the previous assignments I have made client to parse multiple directories, but for this assignment it will only parse the file. Therefore, thee command has to be same format as above. For example:

  python3 client.py http://localhost:12345/flower.jpg

*** Balancer will print out the host and port info for the client to use. ***





  