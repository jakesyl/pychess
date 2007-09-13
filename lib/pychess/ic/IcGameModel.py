
from pychess.Utils.GameModel import GameModel
from pychess.Utils.const import *

class IcGameModel (GameModel):
    
    def __init__ (self, boardmanager, offermanager, gameno, timemodel):
        GameModel.__init__(self, timemodel)
        self.boardmanager = boardmanager
        self.offermanager = offermanager
        self.gameno = gameno
        
        boardmanager.connect("clockUpdatedMs", self.onClockUpdatedMs)
        boardmanager.connect("boardRecieved", self.onBoardRecieved)
        boardmanager.connect("gameEnded", self.onGameEnded)
        boardmanager.connect("gamePaused", self.onGamePaused)
        
        offermanager.connect("onActionError", self.onActionError)
        
        self.inControl = True
    
    def onClockUpdatedMs (self, boardmanager, gameno, msecs, color):
        if gameno == self.gameno:
            self.timemodel.updatePlayer (color, msecs/1000.)
    
    def onBoardRecieved (self, boardmanager, gameno, ply, fen, wsecs, bsecs):
        print "recieved board", gameno, self.gameno, ply, self.ply
        if gameno == self.gameno:
            print "SYNC CLOCK", wsecs, bsecs
            self.timemodel.syncClock (wsecs, bsecs)
            if ply < self.ply:
                print "TAKEBACK", self.ply, ply
                self.undoMoves(self.ply-ply)
    
    def onGameEnded (self, boardmanager, gameno, status, reason):
        if gameno == self.gameno:
            self.end (status, reason)
    
    def setPlayers (self, players):
        if [player.__type__ for player in players] == [REMOTE, REMOTE]:
            self.inControl = False
        GameModel.setPlayers (self, players)
    
    def onGamePaused (self, boardmanager, gameno, paused):
        if paused:
            self.pause()
        else: self.resume()
    
    ############################################################################
    # Offer management                                                         #
    ############################################################################
    
    def offerRecieved (self, player, offer):
        if player == self.players[WHITE]:
            opPlayer = self.players[BLACK]
        else: opPlayer = self.players[WHITE]
        
        if offer.offerType == HURRY_REQUEST:
            return
        
        # This is only sent by ServerPlayers when observing
        elif offer.offerType == TAKEBACK_FORCE:
            self.undoMoves(self.ply - offer.param)
        
        elif offer.offerType in (RESIGNATION, FLAG_CALL):
            self.offermanager.offer(offer, self.ply)
        
        elif offer.offerType in OFFERS:
            if offer not in self.offerMap:
                self.offerMap[offer] = player
                opPlayer.offer(offer)
            # If the offer was an update to an old one, like a new takebackvalue
            # we want to remove the old one from offerMap
            for of in self.offerMap.keys():
                if offer.offerType == of.offerType and offer != of:
                    del self.offerMap[of]
    
    def acceptRecieved (self, player, offer):
        if player.__type__ == LOCAL:
            if offer not in self.offerMap or self.offerMap[offer] == player:
                player.offerError(offer, ACTION_ERROR_NONE_TO_ACCEPT)
            else:
                self.offermanager.accept(offer.offerType)
                del self.offerMap[offer]
        
        # We don't handle any ServerPlayer calls here, as the fics server will
        # know automatically if he/she accepts an offer, and will simply send
        # us the result.
    
    def checkStatus (self):
        status, reason = getStatus(self.boards[-1])
        # On FICS we don't want to autodraw on insufficient material
        if reason == DRAW_INSUFFICIENT:
            return True
        return GameModel.checkStatus(self)
    
    def onActionError (self, offermanager, offer, error):
        self.emit("action_error", offer, error)