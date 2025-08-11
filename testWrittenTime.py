from word2number import w2n

# Function to convert written time phrases to formatted time string
def convert_written_time(phrase):
    phrase = phrase.lower().strip()
    phrase = phrase.replace("in the morning", "am").replace("in the evening", "pm").replace("at ", "")
    words = phrase.split()
    try:
        if len(words) == 2 and words[1] in ("am", "pm"):
            hour = w2n.word_to_num(words[0])
            return f"{hour}:00 {words[1]}"
        elif len(words) == 3 and words[2] in ("am", "pm"):
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(words[1])
            return f"{hour}:{minute:02d} {words[2]}"
        elif len(words) == 2:
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(words[1])
            return f"{hour}:{minute:02d}"
        elif len(words) == 1:
            hour = w2n.word_to_num(words[0])
            return f"{hour}:00"
        print(f"[DEBUG] Trying to convert: {phrase}")
    except:
        return None
    return None

# Test cases
test_phrases = [
    "five am",
    "seven thirty am",
    "nine in the evening",
    "twelve fifteen pm",
    "three 45",
    "ten",
    "at six pm",
    "eight in the morning",
    "twenty five sixty",   # invalid
    "hello world",         # invalid
]

# Run tests
print("Testing `convert_written_time` function:\n")
for phrase in test_phrases:
    result = convert_written_time(phrase)
    print(f"Input: '{phrase}' → Output: {result}")
