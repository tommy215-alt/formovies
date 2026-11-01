# YouTube の予約投稿を、Windows のタスク スケジューラで自動で動かす（2026-11-01、ユーザーの承認）。
#   登録：  powershell -ExecutionPolicy Bypass -File anatomy_room\tools\yt_task.ps1
#   削除：  powershell -ExecutionPolicy Bypass -File anatomy_room\tools\yt_task.ps1 -Remove
# ログオン時と 3 時間ごとに `node anatomy_room\tools\yt_upload.js next` を動かす。PC が切れていて動かなかった分は、起動したときに実行する（StartWhenAvailable）。
# Chrome の画面を使うので、ユーザーがログオンしているときだけ動く。出力は anatomy_room\publish\log\task.log。
param([switch]$Remove)
$Name = "Reverse-YouTube-Upload"   # 予約投稿（名前は英数字：日本語は環境によって文字化けする）
if ($Remove) { Unregister-ScheduledTask -TaskName $Name -Confirm:$false; "削除しました：$Name"; return }
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Node = (Get-Command node).Source
$Cmd = "[Console]::OutputEncoding = [Text.Encoding]::UTF8; Set-Location '$Repo'; & '$Node' anatomy_room\tools\yt_upload.js next 2>&1 | Out-File -Append -Encoding utf8 anatomy_room\publish\log\task.log"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$Cmd`"" -WorkingDirectory $Repo
$T1 = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$T2 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6) -RepetitionInterval (New-TimeSpan -Hours 3)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $Name -Action $Action -Trigger @($T1, $T2) -Settings $Settings -Principal $Principal -Description "anatomy_room/publish/queue.json の未投稿の回を YouTube に予約投稿する（formovies）" -Force | Out-Null
"登録しました：$Name（ログオン時と 3 時間ごと。次回：$((Get-ScheduledTask -TaskName $Name | Get-ScheduledTaskInfo).NextRunTime)）"
