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

# This method adds the contents of a webpage to the string variable, text
# If it's inside of an angle bracket, then dont return it, otherwise add it to text
# returns any text not within a bracket.
def lex(body):
    text = ""
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            text += c
      #  breakpoint("lex", text)
    return text

# This method controls the spacing of characters within the document.
# Cursor_x and y point to where the next text is going to go.
# Returns a display list with each character along with it's position. 
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    # This for loop essentially wraps the the text once we get to the edge of the screen.
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
       # breakpoint("layout", display_list)
    return display_list


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
        self.display_list = layout(text)
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