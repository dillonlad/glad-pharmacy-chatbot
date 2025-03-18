class CognitoUser:
    """
    Holder class for authorizations.
    """
    
    def __init__(self, sub, db_handler):
        self.sub = sub
        self.db_handler = db_handler