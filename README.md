# evernote-latex #

Evernote-latex is a project that tries to make latex integration into Evernote simpler. While there is atleast one service I could find that does something similar, it requires handing over your entire evernote library to a 3rd party. 

What this does is convert any section enclosed in $$...$$ into a Latex rendered section (.png). An example is given below:

![](https://raw.github.com/Chrismarsh/evernote-latex/master/example.png)


## Installation ##
To use evernote-latex:

- pdflatex
- [Image Magick](http://www.imagemagick.org/script/binary-releases.php)
- Python 2.7 (only tested with 2.7)
- [Evernote SDK for Python](https://github.com/evernote/evernote-sdk-python)
- Evernote developer [API key](http://dev.evernote.com/documentation/cloud/) (OAuth currently not implimented)
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/#Download) 
- Perl
- [GhostScript](http://pages.cs.wisc.edu/~ghost/)


In `pyEverNote/` create a file `authToken.py` and add a variable declaration for `sandbox_devToken` that contains your developer sandbox API key. It should look like:
>`sadnbox_devToken = "S=s1:[...]3d"`

Then add a line for your consumerkey. This is required for storing the metadata to undo texification.
>`consumerKey=...`

The default settings are to use a sandbox environment. This is controlled by setting
>`EN = EverNote()`

to

>`EN = EverNote(isSandbox=False)`

If you do this, apply to have your API key enabled on the production servers. Then add  a variable declaration for `devToken` that contains your developer production API key.

There are hardcodes for the `perl` and `gs` directories -- **fix these before running**. This will be fixed in a next version.

## Usage ##
To use, mark sections of text in $$...$$ to be processed. Then add the tag 'tex' to the note. After processing, the 'tex' tag will be removed. Errors will be marked in red text with an explanation of the error (pdflatex output). To undo the texification, tag the note with 'tex.undo'. If a note is tagged with both 'tex' and 'tex.undo', the 'tex.undo' will take precedence. Texification will still be run, potentially undoing a 'tex.undo'.

To run, execute `python evernote-latex.py`.

## Troubleshooting ##
- pdfcrop.pl seems to have trouble finding gs on windows. Even when it's on the path, renaming gswin32c to gs seems to solve the search issues.

## Todo and caveats ##
- <del>Remove 'tex' tag after processing</del>
- Poll for changes or register for webhooks
- <del>Ability to undo texification</del>
- Images are resized for font 11pt.
- Images are a bit blury due to the resizing. 
- Evernote web seems to have trouble veritcally-aligning the images properly, but the desktop application does not.