# run the modified bpytop program, capturing the input and output streams
# btop wants to learn the screen size and will send some command
# on stdout to trigger the shell to report it. I think.
import sys
import subprocess
import threading
import argparse

parser = argparse.ArgumentParser(description="run internal version of bpytop and vt100 to make pictures", allow_abbrev=False)
parser.add_argument("--freq", type=int, default=10, help = "seconds between overwrite replacements (default: %(default)s seconds)") # https://stackoverflow.com/questions/63862118/what-is-the-meaning-of-s-in-python
parser.add_argument("--rows", type=int, default=60, help = "number of rows on virtual screen (default: %(default)s rows)")
parser.add_argument("--cols", type=int, default=160, help = "number of columns on virtual screen (default: %(default)s columns)")
parser.add_argument('--type', choices=['png', 'gif', 'jpg'], default='png', help="output file's graphic format (specify the extension in --path) (default: %(default)s)")
parser.add_argument('--path', default='./delete_me_bpytop.png', help="path+name+ext for output, use --type to set the actual format (default: %(default)s)")
stdargs = parser.parse_args()


class ReadOut(threading.Thread):
    def __init__(self,generator,formatter):
        self.generator = generator
        self.formatter = formatter
        threading.Thread.__init__(self)
    def run(self):
        while True:
            c = self.generator.stdout.read(50000) # this chunk size will determine how often the html is recreated
            if c:
                # this displays great in vscode's terminal window:
                #sys.stdout.buffer.write(c)
                # this is how the html snippet is created: pipe the 20000 characters to the vt100...
                # it's FSM will update the virtual display. Then we'll need some way to trigger the 
                # html generator. 
                # Or maybe none of that...there might be a pattern in the bpytop output to signal
                # the end or begin of the next display (the time stamp updating, perhaps)
                self.formatter.stdin.write(c)


class ReadErr(threading.Thread):
    def __init__(self,generator):
        self.generator = generator
        threading.Thread.__init__(self)
    def run(self):
        while True:
            c = self.generator.stderr.read(1)
            assert False # if get this far, needs some thought
            if c:
                sys.stdout.buffer.write(c)

class WriteIn(threading.Thread):
    def __init__(self,generator):
        self.generator = generator
        threading.Thread.__init__(self)
    def run(self):
        while True:
            #print("writein",flush=True)
            c = next(sys.stdin) # getch.getch()
            assert False # if get this far, needs some thought
            #c = c.decode("utf-8")
            self.generator.stdin.write(c)
            pass

# start the modified bpytop to produce a stdout of ansi vt100 escape sequences
generator = subprocess.Popen(["python3","bpytop/bpytop.py",
                              "--rows",f"{stdargs.rows}",
                              "--cols",f"{stdargs.cols}",
                              "--freq",f"{stdargs.freq}",
                              ],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# start the vt100 parser to process the codes on stdin, using - (minus)  the geometry size must match the hardcoded size in bpytop
formatter = subprocess.Popen(["python3","vt100-parser/vt100.py",
                              f"--format={stdargs.type}",
                              f"--path={stdargs.path}",
                              "--freq",f"{stdargs.freq}",
                              f"--geometry={stdargs.cols}x{stdargs.rows}",
                              "--background=#000000",
                              "-"],stdin=subprocess.PIPE)



readout = ReadOut(generator,formatter)
readerr = ReadErr(generator)
writein = WriteIn(generator)

readout.start()
readerr.start()
writein.start()

readout.join()
readerr.join()
writein.join()
print(f"done")