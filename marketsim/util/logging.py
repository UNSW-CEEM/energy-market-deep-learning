from colored import fg, bg, attr, stylize
import sys

def tprint(msg, color=1):
    """
        like print, but won't get newlines confused with multiple threads
        also provides optional color code - can be string from colored library, or int
    """
    sys.stdout.write(stylize( msg + '\n', fg(color)))
    sys.stdout.flush()