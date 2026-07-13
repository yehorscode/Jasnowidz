import requests
from bs4 import BeautifulSoup
import json
from utils.logmanager import error, success, info, warn, user_input
from tqdm import *
from colorama import Fore, Back, Style

from utils.headers import headers


def scrape_zoom_cykliczne():
    url = "https://zoom.lublin.pl/w-trakcie/"
    base_url = "https://zoom.lublin.pl"

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
        with open("./robots/zoom_robots.txt", "w") as f:
            f.write(robots_response.text)
    else:
        error(f"Błąd podczas pobierania robots.txt: {robots_response.status_code}")

    success("Diagnostyka zakończona!")

    # Potrzebne dane
    # nazwa, adres, daty, link, gatunek

    info(f"Rozpoczęto scrapowanie strony: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find("div", class_="archive-events__items").find_all(
        "div", class_="event-card-wrapper"
    )

    info(f"Znaleziono {len(event_elements)} elementów wydarzeń.")

    data = []

    info("Rozpoczenie szukania wydarzeń...")

    for event in tqdm(
        event_elements,
        desc="Szukanie...",
        unit="wydarzenie",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        title_element = event.find("h3", class_="event-card__title")
        link_element = event.find("a", class_="event-card__image-link")
        place_element = event.find("div", class_="event-card__place")
        time_element = event.find("div", class_="event-card__dates").find("span")
        genre_element = event.find("div", class_="event-card__data-right").find("span")

        title = title_element.text.strip() if title_element else None
        link = link_element["href"] if link_element else None
        if place_element:
            place = (
                place_element.find("span").text.strip()
                if place_element.find("span")
                else None
            )
        else:
            place = None
        time = time_element.text.strip() if time_element else None
        genre = genre_element.text.strip() if genre_element else None

        link = link_element["href"] if link_element else None

        event_data = {
            "title": title,
            "link": link,
            "place": place,
            "time": time,
            "genre": genre,
            "bilety": None,  # Dodaj to pole
        }

        if link:
            # Wykonaj dodatkowy request do linku
            link_response = requests.get(link, headers=headers)
            if link_response.status_code == 200:
                # Scrapuj potrzebne dane z linku
                link_soup = BeautifulSoup(link_response.content, "html.parser")
                bilety_element = link_soup.find("p", text="Bilety:")
                if bilety_element:
                    bilety_text = bilety_element.find_next("p").text.strip()
                    event_data["bilety"] = bilety_text
            else:
                error(f"Błąd podczas pobierania linku: {link_response.status_code}")

        data.append(event_data)


    if len(data) == 0:
        error(f"Nie znaleziono żadnych wydarzeń")
    else:
        success(f"Znaleziono {len(data)} wydarzeń")

    info("Zakończono szukanie wydarzeń.")

    with open("./data/zoom_events_cykliczne.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Zapisano dane wydarzeń do plików JSON.")
