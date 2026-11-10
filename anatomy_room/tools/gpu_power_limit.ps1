# GPU の電力の上限を下げる（2026-11-10、ユーザーの承認：書き出し中に PC が落ちる対策。画質は変わらない）。
# 管理者で実行する。上限は再起動で 220 W に戻るので、ログオン時に自動で設定するタスク「Reverse-GPU-PowerLimit」も作る。
# 元に戻す：nvidia-smi -pl 220 ／ schtasks /delete /tn Reverse-GPU-PowerLimit /f
param([int]$Watts = 180)
$smi = (Get-Command nvidia-smi -ErrorAction Stop).Source
& $smi -pl $Watts
schtasks /create /tn "Reverse-GPU-PowerLimit" /tr "`"$smi`" -pl $Watts" /sc ONLOGON /rl HIGHEST /f
& $smi --query-gpu=power.limit --format=csv | Out-File -Encoding utf8 "$env:TEMP\gpu_power_limit_result.txt"
schtasks /query /tn "Reverse-GPU-PowerLimit" | Out-File -Append -Encoding utf8 "$env:TEMP\gpu_power_limit_result.txt"
