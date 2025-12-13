import csv
import re
import os

# Define file paths
PHYSICAL_INVENTORY_FILE = r'C:\Users\acern50\Documents\code\invent25\invent_fyzicka_2025.csv'
PREV_INVENTORY_FILE = r'C:\Users\acern50\Documents\code\invent25\Inventarizace-2025-12-IT-2024.csv'
ASSETS_FILE = r'C:\Users\acern50\Documents\code\invent25\SeznamProstredku_2025.csv'
OUTPUT_FILE = r'C:\Users\acern50\Documents\code\invent25\Inventory_Merged_2025.csv'

def normalize_inventory_number(inv_str):
    """
    Normalizes inventory number to a standard format (Type, Number).
    Type is 'UP' or 'Š' (normalized from S).
    Number is the 4-digit code.
    """
    if not inv_str or str(inv_str).lower() in ['nan', 'bez čísla', '']:
        return None

    # Handle cases like "Š4857" or "UP4782" (phys inv format)
    match_joined = re.match(r'([A-Za-zŠš]+)\s*(\d+.*)', str(inv_str).strip(), re.IGNORECASE)
    if match_joined:
        prefix = match_joined.group(1).upper()
        # Normalize S to Š for consistency with Physical Inventory if it's 'S'
        if prefix == 'S':
            prefix = 'Š'
        number = match_joined.group(2).strip()
        return (prefix, number)

    return None

def normalize_split_inv(type_col, number_col):
    """
    Normalizes inventory number from separate Type and Number columns.
    """
    if not type_col or not number_col:
        return None
    
    prefix = str(type_col).strip().upper()
    if prefix == 'S':
        prefix = 'Š'
    
    number = str(number_col).strip()
    return (prefix, number)

def load_physical_inventory(filepath):
    """
    Loads physical inventory and returns a dictionary of found items.
    Key: (Type, Number)
    Value: {Status: 'OK', Pavilon: ..., Room: ...}
    """
    found_items = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse Room (Místnost)
                # Format: 107 -> Pavilon 1, Room 07
                room_raw = row.get('Místnost', '').strip()
                pavilon = ''
                room_num = ''
                if len(room_raw) >= 3:
                     pavilon = room_raw[0]
                     room_num = room_raw[1:]
                elif len(room_raw) == 0:
                     pavilon = ''
                     room_num = '' # Handle cases like 'Kancelář' differently or keep as is? 
                                   # The prompt says: "první pozice = pavilon... 2 a 3 pozice = číslo místnosti"
                                   # Let's try to parse if numeric, else keep as is in room column?
                                   # Actually, for 'Kancelář', pavilon is undefined.
                     if room_raw.isdigit():
                         pass # Should be handled by len>=3 usually? Or 1 digit? 
                         # Assuming standard format is 3 digits.
                
                # If room_raw is not 3 digits, just store it in room_num for now
                if not (len(room_raw) == 3 and room_raw.isdigit()):
                     pavilon = '?'
                     room_num = room_raw
                
                inv_raw = row.get('Inventární číslo', '')
                normalized_inv = normalize_inventory_number(inv_raw)
                
                if normalized_inv:
                    found_items[normalized_inv] = {
                        'Stav': 'OK',
                        'Pavilon': pavilon,
                        'Místnost': room_num,
                        'FoundName': row.get('Název zařízení', '')
                    }
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    return found_items

def load_csv_data(filepath):
    data = []
    try:
        # Detect delimiter? Assuming comma based on previous 'view_file' output
        # But wait, the view_file of 2024 inventory showed:
        # 1: Stav,Změna,Pavilon,Místnost,"IČ",Inv. číslo,Název,Typ,Podtyp,SN,"VYRAD",Datum pořízení,
        # It looks like standard CSV.
        with open(filepath, 'r', encoding='utf-8') as f:
             # Check for potential BOM or encoding issues?
             # 'utf-8-sig' handles BOM if present
            reader = csv.DictReader(f)
            data = list(reader)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return data

def main():
    print("Loading Physical Inventory...")
    physical_items = load_physical_inventory(PHYSICAL_INVENTORY_FILE)
    print(f"Loaded {len(physical_items)} items from physical inventory.")

    print("Loading 2024 Inventory...")
    inv_2024 = load_csv_data(PREV_INVENTORY_FILE)
    print(f"Loaded {len(inv_2024)} records from 2024 inventory.")

    print("Loading 2025 Assets...")
    assets_2025 = load_csv_data(ASSETS_FILE)
    print(f"Loaded {len(assets_2025)} records from 2025 assets.")

    # We need to prioritize 2024 inventory or Assets list?
    # The requirement says: "Výstupní soubor bude obsahovat všechny sloupce z vstupních souborů."
    # And "Soouhrnná tabulka bude obsahovat pro jedno zařízení jeden řádek záznamu."
    # It seems we should merge them. Secure matching by Inv Number.
    
    # Let's build the master list. 
    # Use a dictionary to merge by Inventory Key.
    master_inventory = {}

    # Helper to merge row into master
    def merge_into_master(row, source, type_key, num_key):
        inv_key = normalize_split_inv(row.get(type_key), row.get(num_key))
        if not inv_key:
             # Try to normalize from a single column if split fail or not present
             # But these files seem to have split columns "IČ" and "Inv. číslo"
             return

        if inv_key not in master_inventory:
            master_inventory[inv_key] = {}
        
        # Merge data. Prefix keys to avoid collisions if strictly necessary, 
        # but requirement says "merge into one file". 
        # If columns overlap, we might overwrite. 
        # Let's trust 2024 as base? Or 2025? 
        # Usually newer file (Assets 2025) might have partial data?
        # Let's just update the dict. 
        for k, v in row.items():
            if v and str(v).strip(): # Only update if value is present
                 master_inventory[inv_key][k] = v
        
        master_inventory[inv_key]['_source_' + source] = True

    # Process 2024 Inventory
    for row in inv_2024:
        merge_into_master(row, '2024', 'IČ', 'Inv. číslo')

    # Process 2025 Assets
    # In SeznamProstredku_2025.csv columns might differ.
    # Header: stav,Změna,Pavilon,Místnost,IČ1,IČ2,Inv. číslo,Název,Typ,Podtyp,SN,"VYRAD...
    # It has IČ1, IČ2? Let's check the file content again or assume IČ1 is the type.
    # Looking at file content: 
    # 3: ,,,,S,5087,S-5087,,PO Acer Chromebook...
    # Indices: Pavilon(2), Místnost(3), IČ1(4), IČ2(5), Inv. číslo(6)?
    # Wait, standard DictReader uses headers.
    # Header line: stav,Změna,Pavilon,Místnost,IČ1,IČ2,Inv. číslo,Název...
    # Row 3: ,,,,S,5087,S-5087,,PO Acer Chromebook...
    # empty, empty, empty, empty, 'S', '5087', 'S-5087', ...??
    # It seems 'IČ1' is type (S), 'IČ2' is number (5087), 'Inv. číslo' is combined (S-5087).
    # Or 'Inv. číslo' is the 5087?
    # Let's re-examine SeznamProstredku_2025.csv lines.
    # Line 3: ,,,,S,5087,S-5087,,PO Acer Chromebook,,,,17.09.2020,14 790.00
    # Header: stav,Změna,Pavilon,Místnost,IČ1,IČ2,Inv. číslo,Název,Typ,Podtyp,SN,"VYRAD\n",Datum pořízení,Cena
    # It seems:
    # IČ1 = S
    # IČ2 = 5087
    # Inv. číslo = S-5087
    # So we can use IČ1 and IČ2.
    
    for row in assets_2025:
        # Note: headers in assets_2025 might be slightly different case/spacing?
        # "IČ1" and "IČ2" seems correct from file view.
        merge_into_master(row, '2025', 'IČ1', 'IČ2')
        # Explicitly mark as from Seznam as requested
        inv_key = normalize_split_inv(row.get('IČ1'), row.get('IČ2'))
        if inv_key and inv_key in master_inventory:
             master_inventory[inv_key]['Seznam'] = 'TRUE'

    # Now verify against physical inventory
    matched_count = 0
    not_matched_count = 0 
    
    # Collect used physical items to see if any are new/unknown
    used_physical_keys = set()

    for inv_key, data in master_inventory.items():
        if inv_key in physical_items:
            phys_info = physical_items[inv_key]
            data['Stav'] = 'OK'
            # Update location from physical if found
            if phys_info['Pavilon'] != '?':
                data['Pavilon'] = phys_info['Pavilon']
            if phys_info['Místnost']:
                data['Místnost'] = phys_info['Místnost']
            matched_count += 1
            used_physical_keys.add(inv_key)
        else:
            # Not found physically
            # data['Stav'] = '' # Should we clear it? Or leave as is?
            # Requirement: "záznam, že zařízení bylo fyzicky nalezeno nastavením příznaku ve sloupci "Stav" na "OK""
            # implies we set OK if found. Else maybe leave it or set to something else?
            # Existing files have empty or other statuses. I'll just NOT set it to OK.
            pass

    print(f"Matched {matched_count} items with physical inventory.")
    
    # Create rows for Physical Items that were NOT in the master list (New items?)
    new_items_count = 0
    for phys_key, phys_info in physical_items.items():
        if phys_key not in used_physical_keys:
            # This item was found physically but not in 2024/2025 lists.
            # Add it to master? 
            # "Sloučit je do jednoho souboru tak aby každé zařízení bylo v inventáři na jednom řádku."
            # It implies ALL devices.
            new_row = {
                'Stav': 'OK',
                'Pavilon': phys_info['Pavilon'],
                'Místnost': phys_info['Místnost'],
                'Název': phys_info['FoundName'],
                'IČ': phys_key[0],
                'Inv. číslo': phys_key[1],
                'Poznámka': 'Nalezeno navíc při fyzické inventuře'
            }
            master_inventory[phys_key] = new_row
            new_items_count += 1
            
    print(f"Added {new_items_count} items found only in physical inventory.")

    # Write Output
    # Collect all column names
    all_columns = set()
    for row in master_inventory.values():
        all_columns.update(row.keys())
    
    # Sort columns preference: Stav, Pavilon, Místnost, IČ, Inv. číslo, Název, Seznam...
    sorted_columns = ['Stav', 'Pavilon', 'Místnost', 'IČ', 'Inv. číslo', 'Název', 'Seznam']
    rest_columns = sorted(list(all_columns - set(sorted_columns)))
    final_columns = sorted_columns + rest_columns
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=final_columns)
        writer.writeheader()
        for key in master_inventory: # Write in some order? Dict order is insertion order usually.
             writer.writerow(master_inventory[key])

    print(f"Successfully merged inventory to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
