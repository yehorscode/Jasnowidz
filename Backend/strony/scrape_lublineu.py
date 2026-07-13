import requests
from bs4 import BeautifulSoup
import json
from utils.logmanager import error, success, info, warn, user_input
from tqdm import *
from colorama import Fore, Back, Style

from utils.headers import headers


def scrape_lublineu():
    url = "https://lublin.eu/kultura/wydarzenia/"
    base_url = "https://lublin.eu"

    info(f"Rozpoczęto diagnostykę strony: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error(f"Błąd podczas pobierania strony {url}: {response.status_code}")
        return None
    else:
        success("Strona działa")

    robots_url = f"{base_url}/robots.txt"

    info(f"Pobieram robots.txt z {robots_url}")

    robots_response = requests.get(robots_url, headers=headers)

    if robots_response.status_code == 200:
        warn("Strona posiada robots.txt, ale nie jesteś robotem? Prawda?")
        success(f"Zapisano robots.txt do pliku")
        with open("./robots/lublin_eu_robots.txt", "w") as f:
            f.write(robots_response.text)
    else:
        error(f"Błąd podczas pobierania robots.txt: {robots_response.status_code}")

    success("Diagnostyka zakończona!")

    # Początek scrapowania strony lublina
    # Potrzebne dane:
    # Nazwa, Data, Godzina Rozpoczęcia, Miejsce, Udział (Platny, Darmowy, Zapisy), Kategoria, Link bezpośredni
    # Wydarzenia Cykliczne lublin.eu:
    # Nazwa

    info(f"Rozpoczęto scrapowanie strony: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find_all("div", class_="event")

    data = []

    info("Rozpoczęcie szukania wydarzeń...")

    for event in tqdm(
        event_elements,
        desc="Szukanie...",
        unit="wydarzenie",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        # Pobieranie tytułu i linku
        title_element = event.find("div", class_="event-title").find("a")
        event_title = (
            title_element.get("title", "").strip() if title_element else "Brak tytułu"
        )
        event_url = (
            title_element.get("href", "").strip() if title_element else "Brak linku"
        )

        # Pobieranie daty i godziny
        date_elements = event.find("div", class_="event-date-time").find_all(
            "span", class_="event-date"
        )
        time_element = event.find("span", class_="event-time")

        event_dates = (
            [date.text.strip() for date in date_elements]
            if date_elements
            else ["Brak daty"]
        )
        event_time = time_element.text.strip() if time_element else "Brak godziny"

        # Wykonanie dodatkowego requestu do linku bezpośredniego
        full_event_url = f"https://lublin.eu{event_url}"
        event_response = requests.get(full_event_url, headers=headers)
        if event_response.status_code != 200:
            warn(f"Nie udało się pobrać szczegółów wydarzenia: {full_event_url}")
            continue

        event_soup = BeautifulSoup(event_response.content, "html.parser")

        # Pobieranie danych z elementów HTML
        labels = event_soup.find_all("span", class_="label")

        for label in labels:
            if label.text.strip() == "Data rozpoczęcia":
                date_element = label.find_next_sibling("span")
                event_date = date_element.text.strip() if date_element else "Brak danych"
            elif label.text.strip() == "Godzina rozpoczęcia":
                time_element = label.find_next_sibling("span")
                event_time = time_element.text.strip() if time_element else "Brak danych"
            elif label.text.strip() == "Miejsce":
                place_element = label.find_next_sibling("span")
                event_place = place_element.text.strip() if place_element else "Brak danych"
            elif label.text.strip() == "Organizator":
                organizer_element = label.find_next_sibling("span")
                event_organizer = organizer_element.text.strip() if organizer_element else "Brak danych"
            elif label.text.strip() == "Udział":
                participation_element = label.find_next_sibling("span")
                event_participation = participation_element.text.strip() if participation_element else "Brak danych"
            elif label.text.strip() == "Kategoria":
                category_element = label.find_next_sibling("span")
                event_category = category_element.text.strip() if category_element else "Brak danych"

        # Tworzenie słownika dla wydarzenia
        event_data = {
            "nazwa": event_title,
            "data": " - ".join(event_dates),  # Łączenie dat w przypadku zakresu
            "godzina_rozpoczecia": event_time,
            "miejsce": event_place if 'event_place' in locals() else "Brak danych",
            "organizator": event_organizer if 'event_organizator' in locals() else "Brak danych",
            "udzial": event_participation if 'event_participation' in locals() else "Brak danych",
            "kategoria": event_category if 'event_category' in locals() else "Brak danych",
            "link": full_event_url
        }

        data.append(event_data)

    # Wyświetlanie wyników
    info(f"Znaleziono {len(data)} wydarzeń.")
    with open("./data/lublin_eu_data.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Szukanie wydarzeń zakończono!")

    # Scrapowanie wydarzeń cyklicznych
    info("Rozpoczęto scrapowanie wydarzeń cyklicznych...")

    cykliczne_section = soup.find("div", class_="events-groups-list")

    if not cykliczne_section:
        warn("Nie znaleziono sekcji 'Wydarzenia cykliczne'")
    else:
        event_groups = cykliczne_section.find_all("div", class_="event-group")
        cykliczne_data = []

        for event in tqdm(
            event_groups,
            desc="Szukanie...",
            unit="wydarzenie",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            link_element = event.find("a")
            if link_element:
                event_title = link_element.get("title", "").strip()
                event_url = link_element.get("href", "").strip()

                # Tworzenie słownika dla wydarzenia cyklicznego
                event_data = {
                    "nazwa": event_title,
                    "link_bezposredni": f"https://lublin.eu{event_url}",  # Pełny link
                }
                cykliczne_data.append(event_data)

        # Zapisanie danych do pliku JSON
        with open("./data/lublin_eu_cykliczne.json", "w") as f:
            json.dump(cykliczne_data, f, ensure_ascii=False, indent=4)

        success(
            f"Zapisano {len(cykliczne_data)} wydarzeń cyklicznych do pliku './data/lublin_eu_cykliczne.json'"
        )
    print()
    success(f"Scrapowanie {base_url} zakończono!")