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


import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types


import hashlib
import binascii

from . import authToken

class EverNote(object):
    def __init__(self,isSandbox=True):

        #defaults to the sanbox to limit damage
        if isSandbox:
            # Initial development is performed on our sandbox server. To use the production
            # service, change "sandbox.evernote.com" to "www.evernote.com" and replace your
            # developer token above with a token from
            # https://www.evernote.com/api/DeveloperToken.action
            evernoteHost = "sandbox.evernote.com"
            self.authToken = authToken.sandbox_devToken
        else:
            evernoteHost = "www.evernote.com"
            self.authToken = authToken.devToken
        self.consumerKey = authToken.consumerKey
        self.isSandbox = isSandbox   
        userStoreUri = "https://" + evernoteHost + "/edam/user"            
            
        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        
        self.userStore = UserStore.Client(userStoreProtocol)
        
        versionOK = self.userStore.checkVersion("everlatex",
                                           UserStoreConstants.EDAM_VERSION_MAJOR,
                                           UserStoreConstants.EDAM_VERSION_MINOR)
        
        
        if not versionOK:
            raise "API version mismatch"
        
        # Get the URL used to interact with the contents of the user's account
        # When your application authenticates using OAuth, the NoteStore URL will
        # be returned along with the auth token in the final OAuth request.
        # In that case, you don't need to make this call.
        noteStoreUrl = self.userStore.getNoteStoreUrl(self.authToken)
        
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        
        self.noteStore = NoteStore.Client(noteStoreProtocol)       
    
    def getTagGUID(self,tag):
        tags = self.noteStore.listTags(self.authToken)
        tagGUIDs = []
        for t in tags: # search in returned tags
            for myTag in tag: #search in filter tags
                if t.name == myTag:
                    tagGUIDs.append(t.guid)
        return tagGUIDs
    
    #Returns list of notes based on tag guids
    def filterNotesOnTagGUID(self,tagGUID, offset=0,maxReturn = 100):
        filter = NoteStore.NoteFilter()
        filter.tagGuids = tagGUID
        if filter.tagGuids  ==[]:
            return []
            #raise "Tag not found"        
        notes = self.noteStore.findNotes(self.authToken,filter,offset,maxReturn)    
        return notes
    
    #Returns list of notes based on tag names
    def filterNotesOnTag(self,tag, offset=0,maxReturn = 100):
        filter = NoteStore.NoteFilter()
        filter.tagGuids = self.getTagGUID(tag)
        if filter.tagGuids  ==[]:
            return []
            #raise IOError("Tag not found")
        
        notes = self.noteStore.findNotes(self.authToken,filter,offset,maxReturn)     
        return notes    
    
    def getNoteContent(self,note):
        content = self.noteStore.getNoteContent(self.authToken,note.guid)
        return content
    
    def createNote(self,note):
        return self.noteStore.createNote(self.authToken,note)

    def setResourceAppData(self, resourceGUID,  value):
        self.noteStore.setResourceApplicationDataEntry(self.authToken,resourceGUID,self.consumerKey,value)
        
    def setResourceAppDataByHash(self, noteGUID, hash, value):
        resource = self.noteStore.getResourceByHash(self.authToken,noteGUID,hash,False,False,False)
        self.setResourceAppData(resource.guid, value )
        
        
    def getResourceAppData(self,resourceGUID):
        data = self.noteStore.getResourceApplicationData(self.authToken,resourceGUID)
        return data
    
    #returns modified note
    def removeTagsFromNote(self,note,tags):
        guids = self.getTagGUID(tags)
        for guid in guids:
            note.tagGuids = [t for t in note.tagGuids if t != guid] #remove the tag
        return note
    
    def removeResourcesFromNote(self,note,resourceGUIDs):
        for r in note.resources:
            for g in resourceGUIDs:
                if r.guid == g:
                    try:
                        note.resources.remove(r)
                    except ValueError as e:
                        pass
        
        return note

    def add_png_resource(self,note,fname):
            # To include an attachment such as an image in a note, first create a Resource:\
            # for the attachment. At a minimum, the Resource contains the binary attachment
            # data, an MD5 hash of the binary data, and the attachment MIME type.
            # It can also include attributes such as filename and location.
            image = open(fname, 'rb').read()
            md5 = hashlib.md5()
            md5.update(image)
            hash = md5.digest()
            
            data = Types.Data()
            data.size = len(image)
            data.bodyHash = hash
            data.body = image
            
            resource = Types.Resource()
            resource.mime = 'image/png'
            resource.data = data

            hashHex = binascii.hexlify(hash)
            
            if note.resources == None:
                note.resources =[]
            note.resources.append(resource)
            return hashHex,md5.digest()
        
    def updateNote(self,note):
        self.noteStore.updateNote(self.authToken,note)
