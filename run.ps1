param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$ErrorActionPreference='Stop'
$ref=Get-ChildItem "$PSHOME\ref\*.dll" | ForEach-Object FullName
Add-Type -Path (Get-ChildItem 'E:\supervision-sentry\src\*.cs').FullName -ReferencedAssemblies $ref
$task=[SentryHardener.Program]::Main($Args)
exit $task.GetAwaiter().GetResult()
