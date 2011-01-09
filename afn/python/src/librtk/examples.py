
import librtk

__doc__ = """\
This module contains a number of RTK example applications. All of them are
provided as functions that should be used as the connect function passed to
an RTK connection or server instance.
"""

def hello_world(connection):
    """
    A program that shows a window titled "Hello" containing a label whose text
    is "Hello, world! How are you?".
    """
    w = connection.Window(title="Hello")
    w.close_request.listen(connection.close)
    l = connection.Label(w, text="Hello, world! How are you?")

def multi_hello(connection):
    """
    A program that shows five labels stacked one on top of the other.
    """
    w = connection.Window(title="Hello")
    w.close_request.listen(connection.close)
    box = connection.VBox(w)
    for i in range(1,6):
        connection.Label(box, text="Hello number " + str(i))

def count(connection):
    """
    A program that shows a label with a number and a button. Every time the
    button is clicked, the number on the label increments. Multiple clients
    do not share the same number count; see shared_count for an example where
    multiple clients do.
    """
    value = [0] # Store as an array so that it's mutable from closures
    window = connection.Window(title="The Counter")
    window.close_request.listen(connection.close)
    box = connection.VBox(window)
    label = connection.Label(box, text=str(value[0]))
    button = connection.Button(box, text="Click to increment the counter.")
    def clicked():
        value[0] += 1
        label.text = str(value[0])
    button.clicked.listen(clicked)

def shared_count(connection):
    """
    Identical to count, but the counter is shared among clients so that
    clicking the button in one client causes all others to see the new value.
    
    This example is not perfect; it has some race conditions because it doesn't
    use locks where it should. I may fix this at some point, but this is
    intended to be a proof-of-concept, not a perfect application.
    """
    from utils import PrintExceptions
    global shared_count_state
    global shared_count_labels
    try:
        shared_count_state
    except NameError:
        shared_count_state = 0
    try:
        shared_count_labels
    except NameError:
        shared_count_labels = []
    window = connection.Window(title="The Shared Counter")
    window.close_request.listen(connection.close)
    box = connection.VBox(window)
    label = connection.Label(box, text=str(shared_count_state))
    button = connection.Button(box, text="Click to increment the counter "
            "across all clients.")
    def clicked():
        global shared_count_state
        shared_count_state += 1
        for s_label in shared_count_labels[:]:
            with PrintExceptions():
                s_label.text = str(shared_count_state)
    button.clicked.listen(clicked)
    shared_count_labels.append(label)
    def closed():
        shared_count_labels.remove(label)
    connection.add_close_function(closed)
    






def serve_example(port, name, localhost_only=True):
    """
    Starts a server serving the example with the specified name. The server,
    which is an instance of ThreadedServer, will be started and returned.
    Nothing else needs to be done to start using the example (except that you
    need to open a viewer and actually connect to the example, of course).
    
    If localhost_only is True (the default), the example will be served only
    on the loopback interface. If it's false, the example will be served on
    all interfaces.
    """
    server = librtk.ThreadedServer("127.0.0.1" if localhost_only else "", 
            port, globals()[name])
    server.start()
    return server

def main():
    """
    Calls serve_example, taking the port and name from the first two
    command-line arguments. This is intended for use with afn-python/run.
    """
    import sys
    if len(sys.argv) <= 2:
        print "You need to specify a port and an example name."
        return
    server = serve_example(int(sys.argv[1]), sys.argv[2])
    from time import sleep
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print "Interrupted, shutting down"
    finally:
        server.shutdown()
        sys.exit()











