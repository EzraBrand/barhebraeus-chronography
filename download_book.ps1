# Download the whole scan of Bedjan's Chronicon Syriacum (1890), University of Toronto copy on archive.org:
# one zip of 620 JPEG 2000 page images, about 416 MB. Resumable: run it again after a break and curl goes on.
# Run in PowerShell:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\ezrab\Ezra Brandt\Claude\barhebraeus-chronography\download_book.ps1"
$dir = "C:\Users\ezrab\Ezra Brandt\Claude\barhebraeus-chronography\data\raw"
$zip = Join-Path $dir "ketabademadatbez00barhuoft_jp2.zip"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
# curl.exe (not the PowerShell alias "curl"): -L follows redirects, -C - resumes a partial file
curl.exe -L -C - --retry 5 -o $zip "https://archive.org/download/ketabademadatbez00barhuoft/ketabademadatbez00barhuoft_jp2.zip"
Write-Host "Unpacking..."
Expand-Archive -Path $zip -DestinationPath (Join-Path $dir "jp2") -Force
$n = (Get-ChildItem -Recurse -Filter *.jp2 (Join-Path $dir "jp2")).Count
Write-Host "Done: $n page images in $dir\jp2"
