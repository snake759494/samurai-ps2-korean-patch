# Background PCSX2 driver: no focus stealing.
# Usage: emubg.ps1 start <iso> | key <VKhex>[,ms] | snap <outpng> | stop | wins
param([string]$cmd, [string]$arg)
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\Jay\AppData\Local\Temp\claude\D--ps2-------1\fd645b6c-286a-420c-bee1-9bae473839a0\scratchpad\pcsx2p'
$pcsx2 = Join-Path $root 'pcsx2-qt.exe'
$pidf = Join-Path $root 'my.pid'
Add-Type @"
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class B {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint c, uint t);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  public static List<IntPtr> Children(IntPtr p) { var r = new List<IntPtr>(); EnumChildWindows(p, (h, l) => { r.Add(h); return true; }, IntPtr.Zero); return r; }
  public static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
}
"@
function Get-Emu { if (-not (Test-Path $pidf)) { return $null }; $id = [int](Get-Content $pidf); Get-Process -Id $id -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $pcsx2 -and $_.MainWindowHandle -ne 0 } }
function Send-Key([int]$vk, [int]$ms) {
  $p = Get-Emu; if (-not $p) { throw 'no pcsx2 window' }
  $sc = [B]::MapVirtualKey($vk, 0)
  $ext = if ($vk -ge 0x21 -and $vk -le 0x2E) { 1 } else { 0 }
  $down = [IntPtr](1 -bor ($sc -shl 16) -bor ($ext -shl 24))
  $up = [IntPtr]([int64]1 -bor ($sc -shl 16) -bor ($ext -shl 24) -bor (3L -shl 30))
  $targets = @($p.MainWindowHandle) + [B]::Children($p.MainWindowHandle)
  foreach ($h in $targets) { [B]::PostMessage($h, 0x100, [IntPtr]$vk, $down) | Out-Null }
  Start-Sleep -Milliseconds $ms
  foreach ($h in $targets) { [B]::PostMessage($h, 0x101, [IntPtr]$vk, $up) | Out-Null }
}
switch ($cmd) {
  'start' { $p = Start-Process -FilePath $pcsx2 -ArgumentList @('-batch', '-nogui', "`"$arg`"") -WindowStyle Minimized -PassThru; Set-Content $pidf $p.Id; "started $($p.Id)" }
  'key' { $parts = $arg.Split(','); $ms = if ($parts.Length -gt 1) { [int]$parts[1] } else { 120 }; Send-Key ([Convert]::ToInt32($parts[0], 16)) $ms; "key $arg" }
  'snap' {
    $dir = Join-Path $root 'snaps'; New-Item -ItemType Directory -Force $dir | Out-Null
    $before = (Get-ChildItem $dir -Filter 'Samurai*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
    Send-Key 0x7B 80
    for ($i = 0; $i -lt 30; $i++) { Start-Sleep -Milliseconds 200; $n = (Get-ChildItem $dir -Filter 'Samurai*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; if ($n -ne $before) { for ($k = 0; $k -lt 20; $k++) { Start-Sleep -Milliseconds 300; try { Copy-Item $n $arg -Force -ErrorAction Stop; Remove-Item $n -ErrorAction SilentlyContinue; "snap $arg"; return } catch {} }; 'snap locked'; return } }
    'snap failed'
  }
  'park' { $p = Get-Emu; $h = $p.MainWindowHandle; [B]::ShowWindow($h, 4) | Out-Null; Start-Sleep -Milliseconds 500; [B]::ShowWindow($h, 8) | Out-Null; [B]::SetWindowPos($h, [IntPtr]1, -3000, 0, 820, 640, 0x50) | Out-Null; Start-Sleep -Milliseconds 500; [B]::SetWindowPos($h, [IntPtr]1, -3000, 0, 816, 636, 0x50) | Out-Null; 'parked' }
  'wins' { $p = Get-Emu; ([B]::Children($p.MainWindowHandle) | ForEach-Object { "$_ $([B]::Cls($_))" }) }
  'stop' { $p = Get-Emu; if ($p) { Stop-Process -Id $p.Id -Force }; 'stopped' }
}
