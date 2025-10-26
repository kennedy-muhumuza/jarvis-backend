import random


def random_string():
    random_list = [
       
        "Oops, seems I lost track of what you just said. Please rephrase",
        "Oh! It appears you spoke something I don't understand yet. Do you mind rephrasing",
        "Do you mind trying to rephrase that? It seems am yet to learn about that",
        "Sorry dear, I think I missed that. But am on my way to doing much better than this.",
        "I'm terribly sorry dear, I didn't quite catch that. But dont worry, I will soon be much better than this.",
        "Am sorry dear, can't answer that yet, but am looking forward to perfection. I promise!",
        
    ]

    list_count = len(random_list)
    random_item = random.randrange(list_count)

    return random_list[random_item]

