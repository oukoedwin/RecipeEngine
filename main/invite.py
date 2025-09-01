import datetime


class Invite:
    def __init__(self, sender, recipient, recipe, invite_date, invite_time):
        self.sender = sender
        self.recipient = recipient
        self.recipe = recipe
        self.invite_date = invite_date
        self.invite_time = invite_time
        self.status = PENDING
        self.creation_time = datetime.now()