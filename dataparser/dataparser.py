import os.path
from datetime import datetime
import sqlite3

# Zmienna typu Dictionary przechowująca informacje na temat każdego przystanku. Przystanki mają przydzielone linie, a
# linie mają przydzielone pojazdy.
# Dodawanie "_" przed nazwą zmiennej jest konwencją w pythonie. Oznaczać to ma, że dana zmienna/funkcja jest przechowywana w obrębie modułu.
_valid_stops = {
    5: {
        "lines": {
            102: {"vehicles": [201, 42, 53, 654, 75, 12]}
        }
    },
    10: {
        "lines": {
            110: {"vehicles": [753, 342, 84]},
            147: {"vehicles": [864, 532, 2, 5]}
        }
    },
    15: {
        "lines": {
            8: {"vehicles": [1002, 43, 6]},
            57: {"vehicles": [321, 56]}
        }
    },
    20: {
        "lines": {
            10: {"vehicles": [948]},
            57: {"vehicles": [321, 32]}
        }
    },
    25: {
        "lines": {
            22: {"vehicles": [1, 23, 6, 6532]},
            10: {"vehicles": [948]},
            57: {"vehicles": [321, 32]}
        }
    },
    30: {
        "lines": {
            142: {"vehicles": [225, 124, 532]},
            102: {"vehicles": [201, 42]}
        }
    },
    35: {
        "lines": {
            145: {"vehicles": [332]},
            147: {"vehicles": [864, 312, 764, 234]}
        }
    },
    40: {
        "lines": {
            147: {"vehicles": [864, 896, 42]},
            102: {"vehicles": [201, 42]}
        }
    },
    45: {
        "lines": {
            57: {"vehicles": [321, 764, 23, 89]},
            102: {"vehicles": [201, 42]}
        }
    }
}


def load_data_from_file(filename):
    # Sprawdzenie czy taki plik istnieje. Jeśli nie, to funkcja wyświtli komunikat i zwróci None
    if not os.path.exists(filename):
        print(f'"{filename}" does not exist')
        return None

    # Czytanie pliku linia po linii i zapisaywanie ich na liste
    list = []
    line_number = 0

    with open(filename) as file:
        for line in file:
            if len(line) == 0:
                continue  # Przyejdź do następnej iteracji, jeśli linia jest pusta

            if line_number > 0:  # Pomijanie pierwszej linii w pliku, która zawiera nazwy kolumn. Nie będą one dalej potrzebne
                list.append(line.strip())  # Strip usunie wszystkie whitespaces na początku i końcu linii, np. znak końca linii '\n'

            line_number += 1

    return list


def parse_data(data):
    # Listy, które będą przechowywać poprawne i niepoprawne dane
    items_ok = []
    items_nok = []

    # Pętla wykonuje się dla każdego elementu z listy
    for line in data:
        # Rozdzielenie danych
        split_line = line.split(";")

        # Sprawdzanie długości powstałej listy. Musi mieć ona 7 elementów
        if len(split_line) != 7:
            items_nok.append(line)  # Dodanie linii do listy niepoprawnych elementów
            continue  # Przejście do kolejnej iteracji pętli, czyli do kolejnej

        # Sprawdzanie czy wartości są liczbami
        if not split_line[0].isnumeric() or not split_line[1].isnumeric() or not split_line[2].isnumeric():
            items_nok.append(line)
            continue

        # Przypisanie wartości z każdej kolumny do osobnej zmiennej. Niektóre wartości muszą zostać zamienione z typu str na int.
        stop_number = int(split_line[0])
        line_number = int(split_line[1])
        vehicle_number = int(split_line[2])
        date = split_line[3]
        time = split_line[4]
        real_time = split_line[5]
        real_departure_time = split_line[6]

        # Sprawdzanie numeru przystanku
        if stop_number not in _valid_stops:
            items_nok.append(line)
            continue

        # Sprawdzanie numeru linii
        if line_number not in _valid_stops[stop_number]["lines"]:
            items_nok.append(line)
            continue

        # Sprawdzanie numeru pojazdu
        if vehicle_number not in _valid_stops[stop_number]["lines"][line_number]["vehicles"]:
            items_nok.append(line)
            continue

        # Sprawdzenie i próba naprawy separatora daty
        for separator in [".", ",", "*", "-", "/"]:
            date = date.replace(separator, ".")  # Sprawdzenie w pętli każdego separatora i jego podmiana
        try:
            date = datetime.strptime(date, "%d.%m.%Y")  # Funkcja strptime rzuci wyjątkiem ValueError w razie niepowodzenia
        except ValueError:
            items_nok.append(line)
            continue

        # Sprawdzenie i próba naprawy separatora godziny planowanego przyjazdu
        for separator in [".", "-", "'"]:
            time = time.replace(separator, ":")
        try:
            time = datetime.strptime(time, "%H:%M")
        except ValueError:
            items_nok.append(line)
            continue

        # Sprawdzenie i próba naprawy separatora godziny faktycznego przyjazdu
        for separator in [".", "-", "'"]:
            real_time = real_time.replace(separator, ":")
        try:
            real_time = datetime.strptime(real_time, "%H:%M")
        except ValueError:
            items_nok.append(line)
            continue

        # Sprawdzenie i próba naprawy separatora godziny faktycznego odjazdu
        for separator in [".", "-", "'"]:
            real_departure_time = real_departure_time.replace(separator, ":")
        try:
            real_departure_time = datetime.strptime(real_departure_time, "%H:%M")
        except ValueError:
            items_nok.append(line)
            continue

        # Zapisanie poprawnych danych w formie Dictionary
        items_ok.append({
            "stop_number": stop_number,
            "line_number": line_number,
            "vehicle_number": vehicle_number,
            "date": date,
            "time": time,
            "real_time": real_time,
            "real_departure_time": real_departure_time
        })

    return items_ok, items_nok  # Zwrócenie obu list


def calc_delay_and_layover_time(data):
    for item in data:
        delay = item["real_time"] - item["time"]  # Odejmowanie dwóch obiektów typu Datetime. Wynikiem jest różnica czyli opóźnienie (lub zbyt wczesny przyjazd)
        item["delay"] = int(delay.total_seconds())  # Zapisanie opóźnienia w sekundach jako int. total_seconds zwraca float

        layover = item["real_departure_time"] - item["real_time"]  # Obliczanie czasu przebywania na przystanku
        item["layover"] = int(layover.total_seconds())  # Zapisanie czasu w sekundach jako int. total_seconds zwraca float

        # Funkcja nic nie zwraca. Operuje na liście podanej w argumencie i bezpośrednio na niej wprowadza zmiany


def save_to_csv(filename, data):
    file = open(filename, "w")  # Otwarcie pliku do zapisu

    # Zapisanie nazw kolumn
    file.write("Numer przystanku;Numer linii;Numer pojazdu;Data;Godzina planowana;Godzina faktycznego przyjazdu;Godzina faktycznego  odjazdu\n")

    for item in data:
        file.write(item + '\n')

    file.close()  # Zamknięcie pliku


def save_to_sqlite(filename, data):
    conn = sqlite3.connect(filename)  # Otwarcie pliku z bazą danych
    cur = conn.cursor()  # Kursor potrzebny do wysyłanai zapytańdo bazy

    # Usunięcie tabeli, jeśli wcześniej taka istniała.
    # Można usunąć tąlinie, jeśli chcemy dopisywać dane do istniejącej tabeli
    cur.execute("drop table if exists public_transport_data")

    # Stworzenie tabeli, jeśli nie istnieje
    cur.execute("CREATE TABLE if not exists public_transport_data "
                "(stop_number INTEGER, line_number INTEGER, vehicle_number INTEGER, date TEXT, time TEXT,"
                "real_time TEXT, real_departure_time TEXT, delay TEXT, layover TEXT);")

    for item in data:
        # Konwersja typu Datetime na string w podanym formacie
        date = item["date"].strftime("%d.%m.%Y")
        time = item["time"].strftime("%H:%M")
        real_time = item["real_time"].strftime("%H:%M")
        real_departure_time = item["real_departure_time"].strftime("%H:%M")

        # Konwersja z sekund na format "00:00"
        delay = _seconds_to_time(item["delay"])
        layover = _seconds_to_time(item["layover"])

        # Dodawanie danych do bazy danych
        cur.execute(f"INSERT INTO public_transport_data VALUES({item['stop_number']}, {item['line_number']}, "
                    f"{item['vehicle_number']}, '{date}', '{time}', '{real_time}', '{real_departure_time}', "
                    f"'{delay}', '{layover}');")

    # Zapisanie zmian i zamknięcie bazy
    conn.commit()
    conn.close()


def _seconds_to_time(seconds):
    # Funkcja zamienia sekundy na czas w formacie 00:00

    # Zapisanie inforamcji o ujemnej ilości sekund i odwrócenie znaku. Ułatwi to późniejsze obliczenia
    negative = False
    if seconds < 0:
        negative = True
        seconds *= -1

    # '//' to dzielenie, gdzie wynikiem będzie liczba całkowita z obciętą częścią dziesiętną
    # np 10 // 3 = 3
    m = seconds // 60
    s = seconds - (m * 60)

    # Dodanie "-", jeśli autobus przyjechał zbyt wcześnie
    result = ""

    if negative:
        result += "-"

    # Dodanie '0' na początku liczby, jeśli jest mniejsza od 10. Bez tego czas wyglądałby "0:0" zamiast "00:00"

    if m < 10:
        result += "0"
    result += str(m) + ":"

    if s < 10:
        result += "0"
    result += str(s)

    return result
