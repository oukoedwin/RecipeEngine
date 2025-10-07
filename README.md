# SPECS
## Functionalities
- Pass in ingredients, time, cooking technologies available: get recipes that meet your criteria
- Increase your selection by adding new recipes
- Add photos of finished food
- Like recipes that you enjoyed
- Invite friends over
## Extensions
- Without exact ingredients, how can you customize (could use AI)
- Recommend recipes based on what your family and friends like, and occasional entirely new recipe (discovery)
- Add music you like listening to while cooking. Over time create a playlist (Communicates with APIs like Spotify, Apple Music etc)

## Other Ideas
- Vector Embeddings and Nearest Neighbor Search
- Similarity Comparison: Cosine, Jacard
- Caching most popular searches (extension)
    - Exact vs partial matches (e.g in terms of ingredients or cooking tech)
    - Filtering: could filter out recipes that require unavailable ingredients or cooking tech or time

## Simplifications
- Initially account for 20 ingredients, further ingredients may require more substantial change in schema
 
# Design
```plaintext
recipe_project/
├── manage.py
├── recipe_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/          # User management
│   ├── recipes/           # Recipe CRUD, search
│   ├── social/            # Invites, likes, friends
│   └── recommendations/   # Vector embeddings, ML
├── static/
├── templates/
└── requirements.txt
```

# Tasks Remaining
1. Finish setting up the database
2. Implement user authentication
3. Intermediate testing (difficult but find a way to do it)
3. User Interface design
4. Handling Images