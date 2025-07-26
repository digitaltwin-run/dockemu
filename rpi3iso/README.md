# Raspberry Pi OS Images

Umieść tutaj obrazy Raspberry Pi OS (pliki .img lub .iso) do uruchomienia w wirtualizacji QEMU.

## Wspierane formaty:
- `.img` - Obrazy Raspberry Pi OS (zalecane)
- `.iso` - Obrazy ISO (jeśli dostępne)

## Pobieranie obrazów:
1. Pobierz oficjalny obraz z: https://www.raspberrypi.org/downloads/raspberry-pi-os/
2. Wypakuj plik .zip
3. Umieść plik .img w tym folderze

## Przykład nazewnictwa:
- `raspios-lite-arm64-latest.img`
- `raspios-desktop-arm64-latest.img`

## Automatyczne wykrywanie:
Kontener automatycznie wykryje pierwszy dostępny obraz w kolejności:
1. Pliki .img
2. Pliki .iso

## Uwagi:
- Pierwszy boot może potrwać dłużej (inicjalizacja systemu)
- Obraz zostanie rozszerzony automatycznie do 8GB
- SSH będzie włączone automatycznie na porcie 2222
- VNC będzie dostępne na porcie 5901


```bash    
xz -d *.xz
```