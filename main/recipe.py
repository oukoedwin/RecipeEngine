import pandas as pd

class Recipe:
    def __init__(self, person, ingredients, time, cooking_technologies):
        self.id = None
        self.ingredients = ingredients
        self.time = time
        self.cooking_technologies = cooking_technologies
        self.picture_path = ""
        self.likes = 0
        self.shares = 0
        self.creator = person
        self.vector = np.array([0] * len(criteria))
        # TODO: add to database
        # self.id = self.add_to_database()

    def add_to_database(self):
        # return id
        pass

    def add_picture(self, picture_path):
        self.picture = picture_path
        # TODO: update db

    def add_like(self):
        self.likes += 1

    def add_share(self):
        self.shares += 1

    def get_ingredients(self):
        return self.ingredients

    def get_time(self):
        return self.time

    def get_cooking_technologies(self):
        return self.cooking_technologies

    def get_picture_path(self):
        return self.picture_path

    def get_likes(self):
        return self.likes

    def get_shares(self):
        return self.shares

    def update_vector(self):


    def edit_recipe(self, person, ingredients=None, time=None, cooking_technologies=None, picture_path=None):
        if person != self.creator:
            return
        if ingredients is not None:
            self.ingredients = ingredients
        if time is not None:
            self.time = time
        if cooking_technologies is not None:
            self.cooking_technologies = cooking_technologies
        if picture_path is not None:
            self.picture_path = picture_path
        
        # TODO: edit in the database
    