import uuid


def generate_persons(count: int = 100):
    person = [
        {
            'id': 'b45bd7bc-2e16-46d5-b125-983d356768c0',
            'full_name': "Ben",
        },
        {
            'id': 'caf76c67-c0fe-477e-8766-3ab3ff2574b0',
            'full_name': "Howard",
        },
    ]
    person.extend(
        [
            {
                'id': str(uuid.uuid4()),
                'full_name': "David",
            }
            for _ in range(count)
        ]
    )
    return person
