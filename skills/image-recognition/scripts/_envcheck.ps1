$names = 'IMAGE_RECOGNITION_API_KEY','IMAGE_RECOGNITION_BASE_URL','IMAGE_RECOGNITION_MODEL'
foreach ($n in $names) {
    $v = [Environment]::GetEnvironmentVariable($n, 'User')
    if ($v) {
        if ($n -like '*KEY*') { Write-Output "$n len=$($v.Length)" }
        else { Write-Output "$n = $v" }
    } else {
        Write-Output "$n MISSING"
    }
}
