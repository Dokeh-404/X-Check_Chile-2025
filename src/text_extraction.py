from extractor import extract_names
# Prueba con el PDF que ya sabemos que existe o descarga uno manualmente
nombres = extract_names("data/temp/test_unlocked.pdf")
print(f"Se extrajeron {len(nombres)} nombres.")
print(f"Primeros 5: {nombres[:5]}")