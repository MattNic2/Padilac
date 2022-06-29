import socket
import ssl
import tkinter
from browser import request

"""
This program uses the graphical toolkit named tkinter to open webpages in a GUI
Optional Features:
    - Line Breaks
    - Mouse Wheel
    - Emoji
    - Resizing 
    - Zoom

"""




# Variables that describe the dimensions of the canvas
# Hstep and Vstep corresponds to the spacing between the characters on a screen.
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

weight = "normal"
style = "roman"


def text(self, tok):
    font = get_font(self.size, self.weight, self.style)
    for word in tok.text.split():
        w = font.measure(word)
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")


def flush(self):
    if not self.line: return
    breakpoint("initial_y", self.cursor_y, self.line);
    metrics = [font.metrics() for x, word, font in self.line]
    breakpoint("metrics", metrics)
    max_ascent = max([metric["ascent"] for metric in metrics])
    baseline = self.cursor_y + 1.25 * max_ascent
    breakpoint("max_ascent", max_ascent);
    for x, word, font in self.line:
        y = baseline - font.metrics("ascent")
        self.display_list.append((x, y, word, font))
        breakpoint("aligned", self.display_list);
    self.cursor_x = HSTEP
    self.line = []
    max_descent = max([metric["descent"] for metric in metrics])
    breakpoint("max_descent", max_descent);
    self.cursor_y = baseline + 1.25 * max_descent
    breakpoint("final_y", self.cursor_y);


# This method adds the contents of a webpage to the string variable, text
# If it's inside of an angle bracket, then dont return it, otherwise add it to text
# returns any text not within a bracket.
def lex(body):
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_Tag = True
            if text: out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
      #  breakpoint("lex", text)
    return out

FONTS = {}

def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


# This method controls the spacing of characters within the document.
# Cursor_x and y point to where the next text is going to go.
# Returns a display list with each character along with it's position. 
def layout(tokens):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    # This for loop essentially wraps the the text once we get to the edge of the screen.
    for tok in tokens:
        if isinstance(tok, Text):
            for word in tok.text.split():
                display_list.append((cursor_x, cursor_y, c))
                cursor_x += HSTEP
                if cursor_x >= WIDTH - HSTEP:
                    cursor_y += VSTEP
                    cursor_x = HSTEP
            # breakpoint("layout", display_list)
    return display_list




class Test:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "Text('{}')".format(self.text)

class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "Tag('{}')".format(self.tag)


class Layout:
    def __init__(self, tokens):
        self.tokens = tokens
        self.display_list = []

        self.cursor_x = HSTEP
        self.cursour_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, token):
        if isinstance(tok, Text):
            self.text(tok)
        elif tok.tag == "i":
            style = "italic"
        elif tok.tag == "/i":
            style = "roman"
        elif tok.tag == "b":
            weight = "bold"
        elif tok.tag == "/b":
            weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4



# This object organizes the window, canvas, and other things
# Everything that needs access to the canvas will be stored here.
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )

        self.canvas.pack()

        self.scroll = 0
        # binds the down arrow to the scrolldown function (essentially an event handler.)
        self.window.bind("<Down>", self.scrolldown)

    # Gets the text from request, takes out the tags using lex, then gets the display_list from layout and 
    # calls draw to use the display list to draw it on the canvas.
    def load(self, url):
        headers, body = request(url)
        text = lex(body)
        self.display_list = Layout(tokens).display_list
        self.draw()

    # The draw function loops through the display list and draws each character.
    def draw(self):
        # We want to delete the previous text on the screen once we start scrolling
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            # breakpoint("draw")
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            # creates text based on where we are coordinate wise with the scroll
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

if __name__ == "__main__":
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()