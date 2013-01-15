#Copyright (C) 2013  Chris Marsh

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http:www.gnu.org/licenses/>.

from __future__ import print_function
#light wrapper around some of the used evernote functions
from pyEverNote.EverNote import *
from pyEverNote.MLStripper import *
import bs4
#import evernote.edam.type.ttypes as Types

import subprocess
import re
import os


EN = EverNote()
notes = EN.filterNotesOnTag(['tex'])

debugGUID = EN.getTagGUID('tex-debug')

print('Found ' + str(len(notes.notes)) + ' notes')

for n in notes.notes:
    print ('Note: ' + n.title)
    if debugGUID in n.tagGuids:
        debug = True
    
    content = EN.getNoteContent(n)
    
    eqn_num=1
    
    
    eqns = re.findall(r"(?<!\\)\$\$.*?(?<!\\)\$\$",content,re.DOTALL) # regexp from http://stackoverflow.com/a/8485005/410074 may be worth changing to a parser 
    for eqn in eqns: 
        
        ##clean up the content. & gets turned into &amp;  
        
        #eqn_cln = eqn_cln.replace('<br clear="none"/>','')
        #eqn_cln = eqn_cln.replace('<p>','')
        #eqn_cln = eqn_cln.replace('</p>','')
        eqn_cln = html_to_text(eqn)
        eqn_cln = eqn_cln.replace('&amp;','&')
        print('\tEqn ' + str(eqn_num) + '/'+str(len(eqns)) + '...',end="")
        
        f = open(r'tex\base.tex','r')
        tex = f.read()
        f.close()
        tex = tex.replace('$$',eqn_cln[1:-1])

        fname = n.guid + '-' + str(eqn_num)
        
        f = open(fname+'.tex','w')
        f.write(tex)
        f.close()
        
        out = subprocess.Popen(['pdflatex', '-interaction','batchmode',fname],stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate() [0] 


        try:
            f = open(fname+'.log','r')
            log = f.read()
            f.close()
            
            if len(re.findall(r"\n!",log,re.DOTALL)) != 0: #look for lines that start with !
                error = re.findall(r"\n!(.+?)\n(.+?)\n",log,re.DOTALL)
                error= error[:][0][0]+error[:][0][1].replace('<recently read>','')
                raise IOError(error)
            
            s = subprocess.Popen([r'convert', '-density', '720','-resize','18%','-morphology', 'Thicken', 'ConvexHull',fname+'.pdf',fname+'.png'], \
                                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]             

            #s = subprocess.Popen([r'C:\Program Files (x86)\ImageMagick-6.8.1-Q16\convert', '-density', '600',fname+'.pdf','-resize', '20%',fname+'.png'], \
                          #stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]             
            
            #will fail if the png is not found so don't have to explicitly test
            hash = EN.add_png_resource(n,fname+'.png')
            content = content.replace(eqn, '<en-media type="image/png" border="0" vspace="0" hash="'+hash+'" align="absmiddle"/>')
            print('success!')
        except IOError as e:
            content = content.replace(eqn,eqn + '<font color="red">[error:' + str(e) + ']</font>')
            print('error! ',end='')
            print(e)
            
            
        #try to clean up whatever we can, but ignore all errors
        try:
            os.remove(fname+'.tex')
            os.remove(fname+'.pdf')
            os.remove(fname+'.log')
            os.remove(fname+'.aux')
            os.remove(fname+'.png')
        except:
            pass #don't care if the file isn't there
        
        #if debug:
                #debug_note = Types.Note()
                #debug_note.title = 'debug-log-'+n.title
                #de
                 
        eqn_num=eqn_num+1
    #off chance we've clobbered some HTML tags that started outside $$ and ended in our equation, try to fix it!
    
    content = str(bs4.BeautifulSoup(content))
    
    #remove the body and html that bs4 helpfully added back
    content = content.replace('<body>','')
    content = content.replace('</body>','')
    content = content.replace('<html>','')
    content = content.replace('</html>','')
    if not "<?xml" in content:
        content = '<?xml version="1.0" encoding="UTF-8"?>' + content
    n.content = content
    EN.updateNote(n)
