import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types

import hashlib
import binascii

from authToken import *

class EverNote(object):
    def __init__(self,isSandbox=True):
        self.authToken = devToken
        
        #defaults to the sanbox to limit damage
        if isSandbox:
            # Initial development is performed on our sandbox server. To use the production
            # service, change "sandbox.evernote.com" to "www.evernote.com" and replace your
            # developer token above with a token from
            # https://www.evernote.com/api/DeveloperToken.action
            evernoteHost = "sandbox.evernote.com"
        else:
            evernoteHost = "evernote.com"
        
        self.isSandbox = isSandbox   
        userStoreUri = "https://" + evernoteHost + "/edam/user"            
            
        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        
        self.userStore = UserStore.Client(userStoreProtocol)
        
        versionOK = self.userStore.checkVersion("Evernote EDAMTest (Python)",
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
            raise "Tag not found"        
        notes = self.noteStore.findNotes(self.authToken,filter,offset,maxReturn)    
        return notes
    
    #Returns list of notes based on tag names
    def filterNotesOnTag(self,tag, offset=0,maxReturn = 100):
        filter = NoteStore.NoteFilter()
        filter.tagGuids = self.getTagGUID(tag)
        if filter.tagGuids  ==[]:
            raise "Tag not found"
        
        notes = self.noteStore.findNotes(self.authToken,filter,offset,maxReturn)     
        return notes    
    
    def getNoteContent(self,note):
        content = self.noteStore.getNoteContent(self.authToken,note.guid)
        return content
    
    def createNote(self,note):
        return self.noteStore.createNote(self.authToken,note)
        
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
            
            # Now, add the new Resource to the note's list of resources
            #note.resources = [resource]
            
            # To display the Resource as part of the note's content, include an <en-media>
            # tag in the note's ENML content. The en-media tag identifies the corresponding
            # Resource using the MD5 hash.
            hashHex = binascii.hexlify(hash)
            
            if note.resources == None:
                note.resources =[]
            note.resources.append(resource)
            return hashHex   
    def updateNote(self,note):
        self.noteStore.updateNote(self.authToken,note)
