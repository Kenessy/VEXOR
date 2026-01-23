for (=0;  -lt 40; ++) {
   = Get-Content -Path G:\AI\mirror\VRAXION\logs\current\tournament_phase6.log -Tail 5
   =  | Select-String -Pattern ' ctrl\(' | Select-Object -Last 1
  if () {
     = [regex]::Match(.Line, 'step\s+(\d+)')
    if (.Success -and [int].Groups[1].Value -ge 10) { .Line; break }
  }
  Start-Sleep -Seconds 1
}
