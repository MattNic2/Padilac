import socket
import ssl


"""
    This program basically acts as a telnet connection to a website.
        - Parse a URL into a scheme, host, port and path.
        - Connect to that host using the sockets and ssl libraries
        - Send an HTTP request to that host, including a Host header
        - Split the HTTP response into a status line, headers, and a body
        - Print the text (and not the tags) in the body
"""

# This function checks to see if it is a valid URL, it then connects to the correct socket, and formats what we see on the other end
def request(url):

    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], \
        "Unknown scheme {}".format(scheme)

    if ("/" in url):
      host, path = url.split("/", 1)
      path = "/" + path
    else:
      host = url
      path = '/'
    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    # this command creates a socket
    s = socket.socket(

        # We have to establish our socket's, address family. 
        family=socket.AF_INET,

        # Our socket has a type, and this type allows us to send arbitrary amounts of data.
        type=socket.SOCK_STREAM,

        # This tells us the protocol by which our sockets will be communicating over.
        proto=socket.IPPROTO_TCP,
    )
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    # First we must give the other server some information. We want the path and HTTP version. Always 
    # finish with two newlines to make sure the server knows it's the end of our request
    s.send(("GET {} HTTP/1.1\r\n".format(path) + "Host: {}\r\n".format(host) + 
        "Connection: close\r\n" + "User-Agent: Padillac\r\n\r\n").encode("utf8"))

    # Here we want to create a file from the results of the response
    response = s.makefile("r", encoding="utf8", newline="\r\n")
        
    # The status line is first in the makefile and contains status code
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    # Headers come after the status line. 
    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    s.close()

    return headers, body


# This code checks to see if the code is within a pair of angle brackets or not
def show(body):
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url):
    headers, body = request(url)
    show(body)

if __name__ == "__main__":
    import sys
    load(sys.argv[1])
