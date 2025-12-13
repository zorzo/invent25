# Spárovat, respektive sloučit data z CSV souborů

## CSV soubory:
- invent_fyzicka_2025.csv
- Inventarizace-2025-12-IT-2024.csv
- SeznamProstredku_2025.csv

- Tabulky obsahují informace o zařízeních v inventáři.
- Sloučit je do jednoho souboru tak aby každé zařízení bylo v inventáři na jednom řádku.
 
## Realizace spárování:
- Souhrnná tabulka bude obsahovat pro jedno zařízení jeden řádek záznamu.
- Záznamy v tabulkách se budou párovat pomocí inventárního čísla.
- Formát inventárního čísla je:
  - UP nebo Š
  - 4 čísla
  - Např. UP-1234 nebo Š-1234
- Čislo místnosti má formát:
  - první pozice = pavilon (1 nebo 2 nebo 3) 
  - 2 a 3 pozice = číslo místnosti
- souhrnná tabulka bude obsahovat záznam, že zařízení bylo fyzicky nalezeno nastavením příznaku ve sloupci "Stav" na "OK"

## Struktura tabulek je podrboně popsána v souboru:- struktura_csv_souboru.md

- Výstupní formát je CSV soubor.
- Výstupní soubor bude obsahovat všechny sloupce z vstupních souborů.