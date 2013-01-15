# evernote-latex #

Evernote-latex is a project that tries to make latex integration into Evernote simpler. While there is atleast one service I could find that does something similar, it requires handing over your entire evernote library to a 3rd party. 

What this does is convert any section enclosed in a  $$...$$ section into a Latex rendered section (.png). An example is given below:

![](https://raw.github.com/Chrismarsh/evernote-latex/master/example.png)


## Installation ##
To use evernote-latex:

- pdflatex
- [Image Magick](http://www.imagemagick.org/script/binary-releases.php)
- Python 2.7 (only tested with 2.7)
- [Evernote SDK for Python](https://github.com/evernote/evernote-sdk-python)
- Evernote developer [API key](http://dev.evernote.com/documentation/cloud/) (OAuth currently not implimented)


In `pyEverNote/` create a file `authToken.py` and add a variable declaration for `devToken` that contains your developer API key. It should look like:
>`devToken = "S=s1:[...]3d"`

The default settings are to use a sandbox environment. This is controlled by setting
>`EN = EverNote()`

to

>`EN = EverNote(sandbox=False)`

If you do this, apply to have your API key enabled on the production servers.

## Usage ##
To use, mark any note with the tag 'tex'. It will then be processed
Then run ` python evernote-latex.py`

## Todo and caveats ##
- Remove 'tex' tag after processing
- Poll for changes or register for webhooks
- Ability to undo texification
- Images are resized for font 11pt.
- Images are a bit blury due to the resizing. 