import json
from tqdm import *
from utils.logmanager import get_date, error, warn, success, info, user_input

def mergedata():
    lublin_eu = "././data/lublin_eu_data.json"
    zoom = "././data/zoom_events.json"
    output = "././data/final_data.json"

    lublin_plik = []
    zoom_plik = []
    final_plik = []

    with open(lublin_eu, "r") as f:
        lublin_plik = json.load(f)

    with open(zoom, "r") as f:
        zoom_plik = json.load(f)

    # Struktura: (piersze - lublin_eu drugie - zoom)
    # nazwa (nazwa, title)
    # data (data, time)
    # bilety (udzial, bilety)
    # godzina_rozpoczecia (godzina_rozpoczecia)
    # miejsce (miejsce, place)
    # link (link, link)
    # kategoria (kategoria, genre)

    count = 0
    info("Początek mergu Lublin.eu")
    for element in tqdm(
        lublin_plik,
        desc="Zapisywanie Lublin_Eu",
        unit="element",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        count+=1
        final_plik.append(
            {
                "nazwa": element["nazwa"],
                "data": element["data"],
                "bilety": element["udzial"],
                "godzina_rozpoczecia": element["godzina_rozpoczecia"],
                "miejsce": element["miejsce"],
                "link": element["link"],
                "kategoria": element["kategoria"],
                "source": "lublin.eu",
            }
        )
    success(f"Złączono {count} elementów")
    

    count = 0
    info("Początek mergu Zoom")
    for element in tqdm(
        zoom_plik,
        desc="Zapisywanie Zoom",
        unit="element",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        count+=1
        final_plik.append(
            {
                "nazwa": element["title"],
                "data": element["time"],
                "bilety": element["bilety"],
                "godzina_rozpoczecia": "Brak danych",
                "miejsce": element["place"],
                "link": element["link"],
                "kategoria": element["genre"],
                "source": "zoom.lublin.pl"
            }
        )

    success(f"Złączono {count} elementów")

    info("Zapisywanie pliku")
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(final_plik, f, indent=4, ensure_ascii=False)
        success(f"Zapisano plik i ma {len(final_plik)} elementów")
        if len(final_plik) != (lublin_plik.__len__() + zoom_plik.__len__()):
            error(f"Powinien mieć {lublin_plik.__len__() + zoom_plik.__len__()} elementów")

