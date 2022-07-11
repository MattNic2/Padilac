import socket
import ssl
import tkinter
import tkinter.font
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

# Has to do with the font on the screen.
weight = "normal"
style = "roman"


# This method returns a list of tokens, a token is either a text object or a tag object
def parse(self):
    text = ""
    in_tag = False
    # iterates through the entire webpage (c is character)
    for c in self.body:
        if c == "<":
            # When we come across an opening tag, in_tag evaluates to true, 
            # If there is anything in text string, append it to the text object, then clear text
            in_Tag = True
            if text: self.add_text(text)
            text = ""
        elif c == ">":
            # When we come across a close tag, switch in_tag to false. This will store the contents of 
            # the tag in the tag object
            in_tag = False
            self.add_tag(text)
            text = ""
        else:
            text += c
    # If its just regular text, return it to the text object
    if not in_tag and text:
        self.add_text(text)
    return self.finish()

FONTS = {}

def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


# These two objects make it so we could differentiate between text and tag objects 
# when parsing through the document
# Text is being read as a node.
class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "Text('{}')".format(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "Tag('{}')".format(self.tag)





# This object controls the spacing of characters within the document.
# Cursor_x and y point to where the next text is going to go.
# It takes in tokens as an arg (text or tag) and loops over them
class Layout:

    def __init__(self, tokens):
        self.tokens = tokens
        self.display_list = []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    # Weight and style variables must change when we see tags with different types.
    # isinstance checks to see if there is a given tag within the text
    def token(self, tok):
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

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
    def clos_tag(self, tag):
        if tag == "i":
            self.style = "roman"

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close(tree.tag)


    def text(self, tok):
        font = get_font(self.size, self.weight, self.style)
        # 1.) Measure the width of the text and store it in w
        # 2.) cursor_x is where we draw the text, so we check if cursor_x + w is past the width of the page
        # 3.) 
        for word in tok.text.split():
            w = font.measure(word)
            if self.cursor_x + w > WIDTH - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            # This adds the spaces between words, it was taken out by .split()
            self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return
        #breakpoint("initial_y", self.cursor_y, self.line);
        metrics = [font.metrics() for x, word, font in self.line]
        #breakpoint("metrics", metrics)
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
       # breakpoint("max_ascent", max_ascent);
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
            #breakpoint("aligned", self.display_list);
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        #breakpoint("max_descent", max_descent);
        self.cursor_y = baseline + 1.25 * max_descent
        #breakpoint("final_y", self.cursor_y);

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]


class HTMLParser:

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] \
                 and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and \
                 tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)

        if tag.startswith("/"):
            if tag.startswith("!"): return
            if len(self.unfinished) == 1: return
            self.implicit_tags(tag)
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent)
            self.unfinished.append(node)

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                attributes[key.lower()] = value
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    
    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()


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
        self.display_list = []

    # Gets the text from request, takes out the tags using lex, then gets the display_list from layout and 
    # calls draw to use the display list to draw it on the canvas.
    def load(self, url):
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    # The draw function loops through the display list and draws each character.
    def draw(self):
        # We want to delete the previous text on the screen once we start scrolling
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + font.metrics("linespace") < self.scroll: continue
            # creates text based on where we are coordinate wise with the scroll
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor="nw")

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

if __name__ == "__main__":
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()