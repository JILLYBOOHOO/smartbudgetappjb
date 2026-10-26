param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$types=@(
 'Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime',
 'Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime',
 'Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType=WindowsRuntime',
 'Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime',
 'Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime',
 'Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime',
 'Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime',
 'Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType=WindowsRuntime'
)
foreach($name in $types){[void][Type]::GetType($name)}
$script:asTask=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1
$script:asAction=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'} | Select-Object -First 1
function Wait-Operation($operation,[Type]$resultType){
 $task=$script:asTask.MakeGenericMethod($resultType).Invoke($null,@($operation))
 $task.Wait()
 return $task.Result
}
function Wait-Action($operation){$task=$script:asAction.Invoke($null,@($operation));$task.Wait()}
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if($null -eq $engine){throw 'No Windows OCR language is installed. Install English OCR in Windows language settings.'}
[void][Type]::GetType('Windows.Storage.Streams.DataWriter, Windows.Storage.Streams, ContentType=WindowsRuntime')
$inputStream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
$writer=New-Object Windows.Storage.Streams.DataWriter($inputStream)
$writer.WriteBytes([IO.File]::ReadAllBytes($InputPath))
[void](Wait-Operation ($writer.StoreAsync()) ([uint32]))
$writer.DetachStream() | Out-Null
$writer.Dispose()
$inputStream.Seek(0)
$pdf=Wait-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromStreamAsync($inputStream)) ([Windows.Data.Pdf.PdfDocument])
if($pdf.PageCount -gt 20){throw 'Scanned PDFs must contain at most 20 pages. Split the statement into smaller files.'}
$pages=New-Object System.Collections.Generic.List[string]
for($i=0;$i -lt $pdf.PageCount;$i++){
 $page=$pdf.GetPage($i)
 $stream=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
 try{
  $options=New-Object Windows.Data.Pdf.PdfPageRenderOptions
  $scale=[Math]::Min(3,[Math]::Min(2400,[Windows.Media.Ocr.OcrEngine]::MaxImageDimension)/[Math]::Max($page.Size.Width,$page.Size.Height))
  $options.DestinationWidth=[uint32]($page.Size.Width*$scale)
  $options.DestinationHeight=[uint32]($page.Size.Height*$scale)
  Wait-Action ($page.RenderToStreamAsync($stream,$options))
  $stream.Seek(0)
  $decoder=Wait-Operation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap=Wait-Operation ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  try{
   $result=Wait-Operation ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
   # Group words by vertical position so statement columns stay on their row.
   $words=@(foreach($line in $result.Lines){foreach($word in $line.Words){[pscustomobject]@{Text=$word.Text;X=$word.BoundingRect.X;Y=($word.BoundingRect.Y+$word.BoundingRect.Height/2);Height=$word.BoundingRect.Height}}})
   if($words.Count){
    $heights=@($words.Height | Sort-Object)
    $tolerance=[Math]::Max(3,$heights[[int]($heights.Count/2)]*0.65)
    $rows=New-Object System.Collections.Generic.List[object]
    $row=New-Object System.Collections.Generic.List[object]
    $anchor=-10000
    foreach($word in ($words | Sort-Object Y,X)){
     if($row.Count -and [Math]::Abs($word.Y-$anchor) -gt $tolerance){$rows.Add(@($row.ToArray()));$row.Clear()}
     if(-not $row.Count){$anchor=$word.Y}
     $row.Add($word)
    }
    if($row.Count){$rows.Add(@($row.ToArray()))}
    $lines=@(foreach($rowWords in $rows){(($rowWords | Sort-Object X | ForEach-Object {$_.Text}) -join ' ')})
    $pages.Add(($lines -join "`n"))
   }
  }finally{$bitmap.Dispose()}
 }finally{$stream.Dispose();$page.Dispose()}
}
[IO.File]::WriteAllText($OutputPath,($pages -join "`n`n"),(New-Object Text.UTF8Encoding($false)))

$inputStream.Dispose()
