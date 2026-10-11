$ErrorActionPreference = 'Stop'
$workspace = 'D:\Github\BI 2026'
$tomdir = Join-Path $PSScriptRoot 'analysis/tools/tom/lib/netcoreapp3.0'
[System.Reflection.Assembly]::LoadFrom((Join-Path $tomdir 'Microsoft.AnalysisServices.Core.dll')) | Out-Null
[System.Reflection.Assembly]::LoadFrom((Join-Path $tomdir 'Microsoft.AnalysisServices.Tabular.dll')) | Out-Null
$projects = @(
    @{Folder='Workshop 8 Data Analysis Expressions (DAX)'; Name='Workshop8_DAX'; Tables=4; Relationships=3; Measures=9; CalculatedColumns=6},
    @{Folder='Workshop 9 Dashboard'; Name='Workshop9_Foreign_Tourists'; Tables=3; Relationships=2; Measures=3; CalculatedColumns=0}
)
foreach ($project in $projects) {
    $folder = Join-Path $workspace $project.Folder
    $definition = Join-Path $folder ('offline/'+$project.Name+'.SemanticModel/definition')
    $database = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($definition)
    $measureCount = @($database.Model.Tables | ForEach-Object {$_.Measures}).Count
    $calcCount = @($database.Model.Tables | ForEach-Object {$_.Columns} | Where-Object {$_.GetType().Name -eq 'CalculatedColumn'}).Count
    if ($database.Model.Tables.Count -ne $project.Tables -or $database.Model.Relationships.Count -ne $project.Relationships -or $measureCount -ne $project.Measures -or $calcCount -ne $project.CalculatedColumns) {throw 'Model cardinality mismatch'}
    foreach ($relationship in $database.Model.Relationships) {
        if ($relationship.FromCardinality -ne 'Many' -or $relationship.ToCardinality -ne 'One' -or $relationship.CrossFilteringBehavior -ne 'OneDirection' -or -not $relationship.IsActive) {throw 'Invalid relationship'}
    }
    foreach ($table in $database.Model.Tables) {
        if ($table.Partitions.Count -ne 1 -or $table.Partitions[0].Mode -ne 'Import') {throw 'Import partition mismatch'}
    }
    $output = @{result='passed'; validator='Microsoft.AnalysisServices.Tabular.TmdlSerializer 19.84.1'; tables=$database.Model.Tables.Count; relationships=$database.Model.Relationships.Count; measures=$measureCount; calculatedColumns=$calcCount; checks=@('TMDL deserialize','Active many-to-one single-direction relationships','One Import M partition per table'); limitation='DAX evaluation, M refresh, rendering, and slicer interactions require Power BI Desktop'; checkedAt=(Get-Date).ToString('o')}
    $output | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $folder 'analysis/tmdl_validation.json') -Encoding utf8
    Write-Output ($project.Name+': passed TMDL structural validation')
}
