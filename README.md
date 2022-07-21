# Padilac
This is a basic internet browser. In case you're wondering, the name, "Padillac" is a nickname for a surfboard. You would use this browser to surf the web bu-dum-tss. 
The goal of this project is to create a bare bones internet browser to understand how browsers work under the hood. 

## Supported URI schemes:
 - HTTP
 - HTTPS
 - local files
 - data
 - source code

This browser's requests support compression, redirects, caching, and a couple other features.

 ## Graphics
The graphics library that is used is python's tkinter. Display options include: 

 - Line breaks
 - Mouse wheel scrolling
 - Emojis
 - Resizing
 - Zooming
 
This browser uses a parser to convert HTML tokens into a tree. Tag elements and attributes are recognized and parsed. There are also 
limited fixes for malformed documents. A recursive algorithm is used to lay out an HTML tree for error handling.
