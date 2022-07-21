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

FONTS = {}

def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]



#################################################################################################
# These two classes construct the text and element nodes. Text nodes do not actually contain any 
# children and the element class has an added attributes type. 
#####################################################################################################

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



##################################################################################################################
# The layout class controls the spacing of characters within the document. Cursor_x and y correspond with where 
# the next text characters are going to go. Recurse takes in nodes as input and outputs the text onto the screen.
#####################################################################################################################
class Layout:

    def __init__(self, tree):
        self.display_list = []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = []
        self.recurse(tree);

    ################################################################################################################
    # Layout object can use this function instead of tokens to iterate over the body of the document. These next
    # three methods are used together for this process. All opentag cases are covered in open_tag and same for close_tag
    # ################################################################################################################

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

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
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent


#########################################################################################################################
# The HTML parser class iterates through the document and creates a tree of element and text nodes. These nodes are
# tracked on a list called unfinish. Once tags are completed, these nodes are removed from the list. These nodes are passed
# on to the Layout function to be interpreted and displayed.
#########################################################################################################################
class HTMLParser:

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
    ]      

    ###################################################################################################################
    # This method iterates over the request body character by character. It will call add_tag when it comes across a tag object
    # and add_text when it comes across a text object. Once it is done iterating, it calls finish() to complete the 
    # unfinish list.
    ###################################################################################################################
    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_Tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c

        if not in_tag and text:
            self.add_text(text)
        return self.finish()


    ###################################################################################################################
    # this function will add the text as a child of it's parent node. IE the last node in the unfinish list. The reason
    # it is added as a child and not as a member of the unfinish list is because it does not require closing. Closing is 
    # required for tags and this way makes it easier to keep track of the tree.
    ####################################################################################################################
    def add_text(self, text):
        if text.isspace(): return     # ignore spaces.
        self.implicit_tags(None) 

        parent = self.unfinished[-1] 
        node = Text(text, parent)
        parent.children.append(node)


    ########################################################################################################################
    # add_tag has a couple different options. If it is as opening tag, it is simply added to the unfinish list with the node 
    # before it as a parent. If it's a close tag, it removes it's matching unfinished node and adds it as a child of it's parent.
    # edge case handlers are in place for the first tag of a document and the last tag. If there is a self-closing tag, we need to
    # just add it as a child because it is already closed. Check for attributes at the top
    #######################################################################################################################

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return       # Throw out comment tags and Doctype
        self.implicit_tags(tag)

        if tag.startswith("/"):
            if len(self.unfinished) == 1: return   
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)



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


    ##################################################################################################
    # This function breaks apart the tags from attributes on white space. The first string will be the tag
    # and everything that follows will be attributes. Attributes are split by "=" into key and value pairings.
    # Attributes are keys and values are values. 
    #######################################################################################################

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()       # tags are case sensitive
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:                        # Quotes need to be stripped out.
                key, value = attrpair.split("=", 1)
                attributes[key.lower()] = value        # attributes are case sensitive
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    ################################################################################################
    # finish turns the incomplete tree to a complete one by finishing any unfinished nodes.
    # If we have only one node left, it simply pops it and the unfinish list is emptied. 
    ###############################################################################################
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