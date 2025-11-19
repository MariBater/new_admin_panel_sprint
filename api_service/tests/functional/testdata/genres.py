import uuid


def generate_genres(count: int = 10):
    genres = [
        {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90', 'name': 'Action', 'description': 'Action movies description'},
        {'id': 'fb111f22-121e-44a7-b78f-b19191810fb0', 'name': 'Sci-Fi', 'description': 'Sci-Fi movies description'},
        {'id': str(uuid.uuid4()), 'name': 'Comedy', 'description': 'Funny movies'},
        {'id': str(uuid.uuid4()), 'name': 'Drama', 'description': 'Dramatic movies'},
        {'id': str(uuid.uuid4()), 'name': 'Horror', 'description': 'Scary movies'},
    ]
    # In case more genres are needed for tests than defined
    genres.extend([{'id': str(uuid.uuid4()), 'name': f'Genre {i}', 'description': f'Description {i}'} for i in range(len(genres), count)])
    return genres[:count]