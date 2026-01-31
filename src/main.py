import re


def is_palindrome(text: str) -> bool:
    # Ignorowanie wielkości liter i spacji
    cleaned = "".join(text.lower().split())
    return cleaned == cleaned[::-1]


def fibonacci(n: int) -> int:
    # fibonacci(0) = 0, fibonacci(1) = 1
    if n < 0:
        raise ValueError("n cannot be negative")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def count_vowels(text: str) -> int:
    # Zlicza a, e, i, o, u, y (wielkość liter bez znaczenia)
    # Uwzględnia polskie znaki, jeśli są potrzebne
    vowels = "aeiouyąęóćńłśźż"
    return sum(1 for char in text.lower() if char in vowels)


def calculate_discount(price: float, discount: float) -> float:
    # Wyjątek ValueError, jeśli discount poza zakresem 0-1
    if not (0 <= discount <= 1):
        raise ValueError("Discount must be between 0 and 1")
    return price * (1 - discount)


def flatten_list(nested_list: list) -> list:
    # Przyjmuje listę zagnieżdżoną i zwraca spłaszczoną
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


def word_frequencies(text: str) -> dict:
    # Ignorowanie wielkości liter i interpunkcji
    text = re.sub(r"[^\w\s]", "", text.lower())
    words = text.split()
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies


def is_prime(n: int) -> bool:
    # Jeśli n < 2
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
