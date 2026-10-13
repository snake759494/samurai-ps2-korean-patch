# Boot test: run ISO, sample screen for ~66s, stop emulator. Stuck on loading screen (80,80,80) => HANG
param([string]$iso)
if (-not $iso) { $iso = Join-Path (Split-Path $PSScriptRoot -Parent) 'Samurai (Korean).iso' }
$e = Join-Path $PSScriptRoot 'emu.ps1'; $s = "$env:TEMP\boot_s.png"
powershell -ExecutionPolicy Bypass -File $e start $iso | Out-Null
Add-Type -AssemblyName System.Drawing
$log = @()
foreach ($i in 1..11) {
  Start-Sleep 6
  powershell -ExecutionPolicy Bypass -File $e shot $s | Out-Null
  if (Test-Path $s) { $b = [System.Drawing.Bitmap]::FromFile($s); $c = $b.GetPixel(470, 165); $b.Dispose(); $log += "$($c.R),$($c.G),$($c.B)" } else { $log += 'none' }
}
Stop-Process -Name pcsx2-qt -Force -ErrorAction SilentlyContinue
Remove-Item $s -ErrorAction SilentlyContinue
$tail = $log[-4..-1] | Select-Object -Unique
if ($tail.Count -eq 1 -and $tail[0] -eq '80,80,80') { "HANG  $($log -join ' ')" } else { "OK    $($log -join ' ')" }
