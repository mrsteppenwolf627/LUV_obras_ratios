#!/usr/bin/env python
# Generar presupuestos de prueba con estructura valida para importacion

import json
import hashlib
import random
import os

# Definir areas y descripcion reales de los BC3
areas = {
    'Demolicion': [
        'Derribo pared divisoria', 'Derribo falso techo', 'Retirada pavimento',
        'Derribo estructura', 'Arranque carpinteria', 'Arranque instalaciones'
    ],
    'Estructura': [
        'Pilares metalicos', 'Vigas metalicas', 'Forjado hormigon', 'Apuntalamiento',
        'Andamiaje temporal', 'Reparacion grietas'
    ],
    'Carpinteria': [
        'Ventanas aluminio', 'Puertas interiores', 'Puertas exteriores',
        'Armarios', 'Carpinteria madera', 'Cercos'
    ],
    'Fontaneria': [
        'Tuberias PVC', 'Tuberias cobre', 'Griferia bano', 'Griferia cocina',
        'Inodoro', 'Lavabo', 'Ducha', 'Fregadero'
    ],
    'Electricidad': [
        'Cableado electrico', 'Enchufes', 'Interruptores', 'Iluminacion LED',
        'Panel electrico', 'Toma tierra'
    ],
    'Pintura': [
        'Pintura interior mate', 'Pintura interior plastica', 'Pintura exterior',
        'Imprimacion', 'Acabados especiales', 'Lacados'
    ],
}

# Generar 5 presupuestos de prueba
presupuestos = []

for presupuesto_id in range(1, 6):
    lineas = []
    numero = 1

    # Por cada area, agregar 2-4 items
    for area, items_area in areas.items():
        for item in random.sample(items_area, min(3, len(items_area))):
            cantidad = round(random.uniform(5, 100), 1)
            precio = round(random.uniform(50, 500), 2)

            lineas.append({
                "numero": numero,
                "capitulo": f"{presupuesto_id:02d}",
                "descripcion": f"{item} ({area})",
                "cantidad": cantidad,
                "unidad": "m2" if area in ["Demolicion", "Carpinteria", "Pintura"] else ("u" if area in ["Carpinteria", "Fontaneria"] else "ml"),
                "precio_unitario": precio
            })
            numero += 1

    # Crear JSON para importacion
    filename = f"test_presupuesto_{presupuesto_id:02d}.json"
    file_hash = hashlib.sha256(filename.encode()).hexdigest()

    presupuesto_json = {
        "filename": filename,
        "file_hash": file_hash,
        "building_type": "residencial",
        "lineas": lineas
    }

    presupuestos.append(presupuesto_json)
    print(f"Presupuesto {presupuesto_id}: {len(lineas)} lineas")

# Guardar archivos JSON para importacion manual
os.makedirs("data/imports", exist_ok=True)

for presupuesto in presupuestos:
    filename = presupuesto["filename"].replace(".json", "_import.json")
    filepath = os.path.join("data/imports", filename)

    with open(filepath, "w") as f:
        json.dump(presupuesto, f, ensure_ascii=False, indent=2)

    print(f"Guardado: {filepath}")

print(f"\nTotal presupuestos de prueba: {len(presupuestos)}")
print(f"Total lineas: {sum(len(p['lineas']) for p in presupuestos)}")
