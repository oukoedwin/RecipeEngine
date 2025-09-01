import pandas as pd
from enum import Enum

class InviteStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class Person:
    def __init__(self, name):
        self.my_recipes = []
        self.name = name
        self.cooking_technologies = []
        self.liked_recipes = []
        self.friends = []
        self.pending_invites_received = [] # only keep <=10 for now
        self.pending_invites_sent = [] # only keep <= 10 for now

    def add_cooking_technology(self, cooking_technology):
        self.cooking_technologies.append(cooking_technology)

    def like_recipe(self, recipe):
        self.liked_recipes.append(recipe)

    def share_recipe(self, recipe):
        self.shared_recipes.append(recipe)

    def create_recipe(self, ingredients, time, cooking_technologies):
        recipe = Recipe(self, len(self.my_recipes), ingredients, time, cooking_technologies)
        self.my_recipes.append(recipe)
        return recipe

    def edit_recipe(self, recipe, ingredients=None, time=None, cooking_technologies=None, picture_path=None):
        recipe.edit_recipe(self, ingredients, time, cooking_technologies, picture_path)

    def search_recipes(self, ingredients, time, cooking_technologies):
        pass

    def get_my_recipes(self):
        return self.my_recipes

    def accept_invite(self, invite):
        invite.status = ACCEPTED
        
    def decline_invite(self, invite):
        invite.status = DECLINED

    def update_sent_invites(self):
        pass

    def update_received_invites(self):
        pass # delete old invites

    def add_invite(self, invite):
        self.pending_invites_received.append(invite)

    def invite_friend(self, friend, recipe, date, time):
        invite = Invite(self, friend, recipe, date, time)
        self.pending_invites_sent.append(invite)
        friend.add_invite(invite)

    def reply_to_invite(self, invite, status):
        if status == "accept":
            invite.status = ACCEPTED
        elif status == "decline":
            invite.status = DECLINED



        


