from socket import *
from array import *
import os
import sys
import struct
import time
import select
from statistics import *
import binascii


ICMP_ECHO_REQUEST = 8

def checksum(string):
	csum = 0
	countTo = (len(string) // 2) * 2
	count = 0
	while count < countTo:
		thisVal = (string[count+1]) * 256 + (string[count])
		csum += thisVal
		csum &= 0xffffffff
		count += 2

	if countTo < len(string):
		csum += (string[len(string) - 1])
		csum &= 0xffffffff

	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
	rtt = []
	timeLeft = timeout
	while 1:
	    startedSelect = time.time()
	    whatReady = select.select([mySocket], [], [], timeLeft)
	    howLongInSelect = (time.time() - startedSelect)
	    if whatReady[0] == []: # Timeout
	        return "Request timed out."
	    timeReceived = time.time()
	    recPacket, addr = mySocket.recvfrom(1024)
	    icmpHeader = recPacket[20:28]
	    icmpType, code, myChecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
	    if ID == packetID:
	        bytesInDouble = struct.calcsize("d")
	        timeLeft = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
	        rtt = (timeReceived - timeLeft) * 1000
	        return rtt
	        timeLeft = timeLeft - howLongInSelect

def sendOnePing(mySocket, destAddr, ID):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	myChecksum = 0
	# Make a dummy header with a 0 checksum# struct -- Interpret strings as packed binary data
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
	# Calculate the checksum on the data and the dummy header.
	myChecksum = checksum(header + data)

	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		# Convert 16-bit integers from host to network byte order
		myChecksum = htons(myChecksum) & 0xffff
	else:
		myChecksum = htons(myChecksum)
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data
	mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
	icmp = getprotobyname("icmp")
	# SOCK_RAW is a powerful socket type. For more details: http://sock-raw.org/papers/sock_raw
	mySocket = socket(AF_INET, SOCK_RAW, icmp)
	myID = os.getpid() & 0xFFFF	# Return the current process
	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	mySocket.close()
	return delay


def ping(host, timeout=1):
	dest = gethostbyname(host)
	print ("Pinging " + dest + " using Python:")
	print ("")
	delay_float = array ('f')
	# Send ping requests to a server separated by approximately one second
	for i in range(0,4):
		delay = doOnePing(dest, timeout)
		delay_float.append(delay)
		print(delay)
		time.sleep(1)
	packet_min = min(delay_float)
	packet_max = max(delay_float)
	packet_avg = (sum(delay_float))/(len(delay_float))
	stdev_var = stdev(delay_float)
	vars = packet_min, packet_avg, packet_max, stdev_var
	print(vars)
	return vars

if __name__ == '__main__':
	ping("google.co.il")