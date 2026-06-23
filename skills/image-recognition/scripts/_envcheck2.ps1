$names = 'GPT_IMAGE_API_KEY','GPT_IMAGE_BASE_URL','OPENAI_API_KEY','OPENAI_BASE_URL'
foreach ($n in $names) {
    foreach ($scope in 'User','Machine','Process') {
        $v = [Environment]::GetEnvironmentVariable($n, $scope)
        if ($v) {
            if ($n -like '*KEY*') { Write-Output "$n[$scope] len=$($v.Length)" }
            else { Write-Output "$n[$scope] = $v" }
        }
    }
}
