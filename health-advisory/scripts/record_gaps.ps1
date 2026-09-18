#Requires -Version 7
<#
  One definition of "a gap in the record", dot-sourced by both record_view.ps1
  and due_report.ps1.

  It lives in one file because the two callers previously computed gaps
  independently and disagreed: the view named "allergies not recorded" while the
  review did not list it. A rule implemented twice drifts, and a review that
  under-reports a gap is a review that overstates the record.
#>

function Get-RecordGaps {
    param([Parameter(Mandatory)]$Person)

    $gaps = @()
    foreach ($section in @('conditions', 'medications', 'allergies')) {
        if ($null -eq $Person[$section]) { $gaps += "$section not recorded" }
    }
    if ($null -eq $Person['treatments_tried']) { $gaps += 'treatments_tried not recorded' }
    foreach ($condition in @($Person['conditions'])) {
        if (-not $condition) { continue }
        if ($condition['onset_unknown']) { $gaps += 'onset unknown' }
        if (-not $condition['severity'])  { $gaps += 'severity not graded' }
    }
    return @($gaps | Select-Object -Unique)
}
