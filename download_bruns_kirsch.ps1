# Download the Syriac volume of the Bruns-Kirsch edition (Leipzig 1789) of Barhebraeus' Chronicon Syriacum, for a
# cross-check of Bedjan's OCR: archive.org item ChroniconSyriacum, "Chronicon_Syriacum 2" (Serto type; pages numbered
# from the back), one zip of JPEG 2000 images, about 583 MB. Resumable: run again after a break.
# Run in PowerShell:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\ezrab\Ezra Brandt\Claude\barhebraeus-chronography\download_bruns_kirsch.ps1"
$dir = "C:\Users\ezrab\Ezra Brandt\Claude\barhebraeus-chronography\data\bruns_kirsch"
$zip = Join-Path $dir "Chronicon_Syriacum_2_jp2.zip"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
curl.exe -L -C - --retry 5 -o $zip "https://archive.org/download/ChroniconSyriacum/Chronicon_Syriacum%202_jp2.zip"
Write-Host "Unpacking..."
Expand-Archive -Path $zip -DestinationPath (Join-Path $dir "jp2") -Force
$n = (Get-ChildItem -Recurse -Filter *.jp2 (Join-Path $dir "jp2")).Count
Write-Host "Done: $n page images in $dir\jp2"
