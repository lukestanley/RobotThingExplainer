import csv
import string

def extract_allowed_words(csv_path, category='A1'):
    allowed_words = set()
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Category'] == category:
                allowed_words.add(row['Word'].lower())  # Normalise to lowercase
    return sorted(allowed_words)

def find_invalid_words(text, valid_words, extra_words=[]):
    words = text.lower().split()
    invalid_words = set()

    # Create a translation table to remove punctuation
    translator = str.maketrans('', '', string.punctuation)

    def singularise(word):
        """Convert simple plural forms or conjugations to singular."""
        if word.endswith('es') and len(word) > 2:
            base_word = word[:-2]
            if base_word in valid_words or base_word in extra_words:
                return base_word
        if word.endswith('s') and len(word) > 1:
            base_word = word[:-1]
            if base_word in valid_words or base_word in extra_words:
                return base_word
        return word

    # Create a copy of the valid words list and add extra words
    combined_words = set(valid_words).union(extra_words)

    for word in words:
        cleaned_word = word.translate(translator)  # Remove punctuation
        singular_word = singularise(cleaned_word)  # Convert to singular form
        if singular_word not in combined_words:
            invalid_words.add(cleaned_word)

    return list(invalid_words)


allowed_words_list = extract_allowed_words('oxford_britishish_3000_full_words_types_categories.csv')
