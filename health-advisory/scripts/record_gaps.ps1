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
    if (-not $Person['relationship']) { $gaps += 'relationship not recorded' }
    # Every section that can be "not recorded". An empty list means "asked and
    # there are none"; null means nobody asked. Writing [] for an unasked section
    # asserts something untrue, which is how both records were first written.
    foreach ($section in @('conditions', 'medications', 'allergies', 'family_history', 'measurements', 'lifestyle', 'events')) {
        if ($null -eq $Person[$section]) { $gaps += "$section not recorded" }
    }
    if ($null -eq $Person['treatments_tried']) { $gaps += 'treatments_tried not recorded' }
    foreach ($condition in @($Person['conditions'])) {
        if (-not $condition) { continue }
        if ($condition['onset_unknown']) { $gaps += 'onset unknown' }
        if (-not $condition['severity'])  { $gaps += 'severity not graded' }
    }
    # An event with no sourced interval cannot be scheduled against anything.
    foreach ($event in @($Person['events'])) {
        if (-not $event) { continue }
        if (-not $event['interval_months']) { $gaps += 'a screening event has no sourced interval' }
    }
    # The leading comma matters. A bare `return @(...)` writes the array to the
    # pipeline, and a one-element array unwraps to a scalar while an empty one
    # arrives as $null - so `$gaps.Count` throws under StrictMode on exactly the
    # person with no gaps at all. The comma emits the array as one object.
    return ,@($gaps | Select-Object -Unique)
}
