param([string]$Source = 'E:\supervision-sentry\src\SupervisionProtocol.cs')
Add-Type -Path $Source
$empty = [SentryHardener.SupervisionProtocol]::ParseVerdict('')
if ($empty.Status -ne 'unverifiable') { throw "empty verdict status mismatch" }
$fp1 = [SentryHardener.SupervisionProtocol]::Fingerprint('frame-1','answer')
$fp2 = [SentryHardener.SupervisionProtocol]::Fingerprint('frame-1','answer')
if ($fp1 -ne $fp2 -or $fp1.Length -ne 64) { throw "fingerprint mismatch" }
