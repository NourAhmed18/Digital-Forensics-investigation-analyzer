rule Digital_Forensics_Test_Rule
{
    meta:
        description = "Safe test rule for the Digital Forensics YARA engine"
        author = "Digital Forensics Team"
        severity = "low"

    strings:
        $marker = "DIGITAL_FORENSICS_TEST_MARKER"

    condition:
        $marker
}
