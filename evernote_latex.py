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
import evernote.edam.error.ttypes as Errors
import HTMLParser
import bs4

perl_path=r'C:\cygwin\bin\perl'
im_path=r'C:\Program Files (x86)\ImageMagick-6.8.1-Q16\convert'
latex_path=r'pdflatex'

import subprocess
import re
import os

#Setup our evernote wrapper
EN = EverNote(isSandbox=False)

#find the tags to process
try:
    texify_undo = EN.filterNotesOnTag(['tex.undo'])
except:
    print('No tex.undo to do')
    

if texify_undo:
    #Do we have any notes to undo?
    for n in texify_undo.notes:
        print ('Reverting note ' + n.title+': ',end="")
        i=0
        content = EN.getNoteContent(n) #get the content
        rGUIDS = [] #resources guids to remove
        bs = bs4.BeautifulSoup(content,'xml') #use bs to pull out the en-media tags
        
        #loop over all the resources, some may not be ours
        for r in n.resources:
            #check if this is a texified resource
            res = EN.getResourceAppData(r.guid)
            try:
                data = res.fullMap[EN.consumerKey] #get our appdata
                eqn,hash = data.split('<;;;>') #get our eqn and hash from our saved meta data

                en_media = bs.find(hash=hash)
                if en_media: #place the tag with the eqn
                    en_media.replaceWith(eqn.replace('&','&amp;'))
                    rGUIDS.append(r.guid)
                    i=i+1
                 
                #for en_media in bs.findAll('en-media'):
                    #if hash in str(en_media):#is this our hash? replace it
                        #bs4 mixes up the attribute order, so we can hardcode the reorder as it's always like this (famous last words), then replace on 
                        #tmp_tag = '<en-media style="' + en_media['style'] +'" hash="' + en_media['hash'] +'" type="' + en_media['type'] + '"></en-media>' 
                        #content = content.replace(tmp_tag,eqn.replace('&','&amp;'))
            except:           
                pass #no dice, keep going
        
        n = EN.removeResourcesFromNote(n,rGUIDS)
        n.content = str(bs)#content
        n = EN.removeTagsFromNote(n,['tex.undo'])
        EN.updateNote(n)
        print(str(i)+'/'+str(i+len(n.resources))+' reverted.')

try:
    texify_notes = EN.filterNotesOnTag(['tex'])
except:
    print('No tex to do')

if texify_notes: #incase the tag has never been used
    for n in texify_notes.notes:
        print ('Texifying note: ' + n.title)
        
        eqn_hash ={}
        
        content = EN.getNoteContent(n)
        
        eqn_num=1
        
        
        eqns = re.findall(r"(?<!\\)\$\$.*?(?<!\\)\$\$",content,re.DOTALL) # regexp from http://stackoverflow.com/a/8485005/410074 may be worth changing to a parser 
        for eqn in eqns: 
            
            ##clean up the content. & gets turned into &amp;  
            eqn_cln = html_to_text(eqn)
            
            #this one seems to be a bit of an edge case, just get rid of it
            eqn_cln = eqn_cln.replace('&nbsp;',' ') # because we wanted to save the &amp above, we unfortunately preserve the nbsp that screws up latex. So remove it
            
            #all the rest o the html symbols, convert back to ascii
            h= HTMLParser.HTMLParser()
            eqn_cln = h.unescape(eqn_cln)

            print('\tEqn ' + str(eqn_num) + '/'+str(len(eqns)) + '...',end="")
            
            f = open(r'tex\base.tex','r')
            tex = f.read()
            f.close()
            
            #remove the extra $ on each end
            idx1 = eqn_cln.find('$')
            idx2 = eqn_cln.rfind('$')
            tex = tex.replace('$$',eqn_cln[idx1+1:idx2])
    
            fname = n.guid + '-' + str(eqn_num)
            
            f = open(fname+'.tex','w')
            f.write(tex)
            f.close()
            
            out = subprocess.Popen([latex_path, '-interaction','batchmode',fname],stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate() [0] 
    
    
            try:
                f = open(fname+'.log','r')
                log = f.read()
                f.close()
                
                if len(re.findall(r"\n!",log,re.DOTALL)) != 0: #look for lines that start with !
                    error = re.findall(r"\n!(.+?)\n(.+?)\n",log,re.DOTALL)
                    error= error[:][0][0]+error[:][0][1].replace('<recently read>','')
                    error = error.replace('<inserted text>','') #confuses the hell out of poor bs4
                    raise IOError(error)
                
                
                s = subprocess.Popen([perl_path,'pdfcrop.pl', '-hires',fname+'.pdf'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]                
                
                if not 'page written on' in s:
                    raise IOError(s)
                
                s = subprocess.Popen([im_path, '-density', '720','-resize','18%',\
                                      '-morphology', 'Thicken', 'ConvexHull',fname+'-crop.pdf',fname+'.png'], \
                                        stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0] 
     
                
                #will fail if the png is not found so don't have to explicitly test
                hash,md5 = EN.add_png_resource(n,fname+'.png')
                eqn_hash[md5]=eqn_cln+'<;;;>'+hash
                content = content.replace(eqn, '<en-media type="image/png" style="vertical-align: middle;" hash="'+hash+'"/>')
    
                print('success!')
            except IOError as e:
                content = content.replace(eqn,eqn + '<font color="red">[error:' + str(e) + ']</font>')
                print('error! ',end='')
                print(e)
                
                
            #try to clean up whatever we can, but ignore all errors
            try:
    
                os.remove(fname+'.tex')
                os.remove(fname+'.pdf')
                os.remove(fname+'-crop.pdf')
                os.remove(fname+'.log')
                os.remove(fname+'.aux')
                os.remove(fname+'.png')
            except:
                pass #don't care if the file isn't there
    
            eqn_num=eqn_num+1
            
        #off chance we've clobbered some HTML tags that started outside $$ and ended in our equation, try to fix it!
        content = str(bs4.BeautifulSoup(content,"xml"))
 
        #just in case, but should have been added by bs4 if missing
        if not "<?xml" in content:
            content = '<?xml version="1.0" encoding="UTF-8"?>' + content
            
        n.content = content
    
        EN.removeTagsFromNote(n,['tex'])
        try:
            EN.updateNote(n)
        except Errors.EDAMUserException as e:
            print('Unable to update note ' + n.title)
            print('\t' + str(e))
            exit(-1)
        
        #to add meta data, we need the note guid, which we only get after an update. so update, query the resources (we known the hashes)
        #and then update the meta data
        for h in eqn_hash:
            try:
                EN.setResourceAppDataByHash(n.guid,h,eqn_hash[h])
            except:
                print('Meta data failed for:')
                print(h)
                print(eqn_hash[h])
