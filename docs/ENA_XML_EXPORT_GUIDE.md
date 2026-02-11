# ENA XML Export Implementation Guide

## Overview
This document describes the implementation of ENA (European Nucleotide Archive) XML export functionality for FieldSample data following the ERC000024 (GSC MIxS water/sediment) checklist schema.

## What Was Implemented

### 1. Custom Renderer: `ENAXMLRenderer`
**File**: `wet_lab/renderers.py`

The renderer generates a **ZIP file** containing two separate XML files required by ENA:

#### Files Generated:
1. **submission.xml** - Contains the submission metadata
   - SUBMISSION_SET with VALIDATE action
   - Used to validate metadata before actual submission

2. **sample.xml** - Contains all sample metadata
   - SAMPLE_SET with individual SAMPLE elements
   - Follows ERC000024 checklist requirements
   - Includes mandatory and optional fields

#### Key Features:
- **Media Type**: `application/zip`
- **Format**: `zip`
- **Charset**: `utf-8`

### 2. Export Integration

#### Modified Files:
- `utility/serializers.py` - Added custom format support in `CharSerializerExportMixin`
- `wet_lab/views.py` - Configured `MixsWaterFilterView` and `MixsSedimentFilterView`

#### Configuration:
```python
export_formats = list(settings.EXPORT_FORMATS) + ['ena_xml']
renderer_classes = {
    'ena_xml': ENAXMLRenderer,
}
```

## How to Use

### 1. Access the Export Views

#### For Water Samples (MIxS Water):
- Navigate to the MIxS Water view
- Apply any filters you need
- Click "Export" and select **"ena_xml"** format

#### For Sediment Samples (MIxS Sediment):
- Navigate to the MIxS Sediment view
- Apply any filters you need
- Click "Export" and select **"ena_xml"** format

### 2. Download the ZIP File
- The export will download as: `MIxSwater_v5_YYYY-MM-DD_HH-MM-SS.zip` (or sediment equivalent)
- Contains both `submission.xml` and `sample.xml`

### 3. Extract and Review
```bash
unzip MIxSwater_v5_2024-01-15_10-30-00.zip
# This creates:
# - submission.xml
# - sample.xml
```

### 4. Validate with ENA
Before submitting to ENA, you should:
1. Review both XML files
2. Validate using ENA's validation tools
3. Check that all mandatory fields are populated
4. Verify coordinates and dates are correct

## XML Structure

### submission.xml Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<SUBMISSION_SET>
  <SUBMISSION>
    <ACTIONS>
      <ACTION>
        <VALIDATE/>
      </ACTION>
    </ACTIONS>
  </SUBMISSION>
</SUBMISSION_SET>
```

### sample.xml Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<SAMPLE_SET>
  <SAMPLE alias="sample_alias">
    <TITLE>Project Name - Barcode</TITLE>
    <SAMPLE_NAME>
      <TAXON_ID>256318</TAXON_ID>
      <SCIENTIFIC_NAME>metagenome</SCIENTIFIC_NAME>
    </SAMPLE_NAME>
    <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>project name</TAG>
        <VALUE>Project Name</VALUE>
      </SAMPLE_ATTRIBUTE>
      <!-- More attributes... -->
      <SAMPLE_ATTRIBUTE>
        <TAG>ENA-CHECKLIST</TAG>
        <VALUE>ERC000024</VALUE>
      </SAMPLE_ATTRIBUTE>
    </SAMPLE_ATTRIBUTES>
  </SAMPLE>
  <!-- More samples... -->
</SAMPLE_SET>
```

## Field Mappings

### Mandatory Fields (ERC000024)
| Database Field | ENA Tag | Notes |
|----------------|---------|-------|
| `project_name` | project name | Project identifier |
| `collection_date` | collection date | ISO 8601 format |
| `geographic_location_latitude` | geographic location (latitude) | Decimal degrees |
| `geographic_location_longitude` | geographic location (longitude) | Decimal degrees |
| `geographic_location_country` | geographic location (country and/or sea) | Country name |
| `env_broad_scale` | broad-scale environmental context | Biome context |
| `env_local_scale` | local environmental context | Local features |
| `env_medium` | environmental medium | Sample medium |

### Optional Fields
| Database Field | ENA Tag |
|----------------|---------|
| `geo_loc_name` | geographic location (region and locality) |
| `depth` | depth |
| `sample_type` | sample type |
| `sampling_method` | sampling method |
| `samp_collect_device` | sample collection device |
| `samp_mat_process` | sample material processing |
| `samp_size` | amount or size of sample collected |
| `nucl_acid_ext` | nucleic acid extraction |
| `temperature` | temperature |
| `ph` | pH |
| `turbidity` | turbidity |
| `conductivity` | conductivity |
| `dissolved_oxygen` | dissolved oxygen |

## Submission Process to ENA

1. **Prepare Files**
   - Extract `submission.xml` and `sample.xml` from the ZIP
   - Review both files for completeness

2. **Validate (RECOMMENDED)**
   - Use the VALIDATE action (already included in submission.xml)
   - Submit to ENA test environment first
   - Check for any validation errors

3. **Submit to Production**
   - Once validation passes, change action to HOLD or ADD
   - Submit to ENA production environment
   - Follow ENA's submission guidelines

4. **Hold Action (Optional)**
   - If you want to hold samples until publication date
   - Add HOLD action with `HoldUntilDate` attribute
   - Example: `<HOLD HoldUntilDate="2025-01-01"/>`

## Technical Details

### Serializers Used
- **MixsWaterSerializer** - For water samples (`sample_type_code='fs'`)
- **MixsSedimentSerializer** - For sediment samples (`sample_type_code='ex'`)

### Data Sources
- **FieldSample** - Base sample data
- **FieldSurvey** - Survey information, project links
- **FilterSample** - Water sample specific data
- **SubCoreSample** - Sediment sample specific data
- **SampleBarcode** - Barcode information
- **EnvMeasure** - Environmental measurements (temperature, pH, etc.)

### Query Optimization
Both views use:
- `select_related()` for foreign keys
- `prefetch_related()` for many-to-many relationships
- Efficient single-query data retrieval

## Troubleshooting

### Export Button Not Working
- Check browser console for JavaScript errors
- Verify user has required permissions:
  - `field_survey.view_fieldsample`
  - `wet_lab.view_fastqfile`

### Missing Data in Export
- Check that filters are not too restrictive
- Verify related data exists (FieldSurvey, SampleBarcode, etc.)
- Check serializer field mappings

### Invalid XML
- Validate XML structure using online validators
- Check for special characters in data (should be escaped automatically)
- Verify all mandatory fields have values

### ENA Validation Errors
- Review ENA's error messages carefully
- Check field format requirements (dates, coordinates, etc.)
- Ensure controlled vocabulary terms are used correctly

## Future Enhancements

### Possible Improvements:
1. **Configurable Actions** - Allow users to choose VALIDATE, HOLD, or ADD action
2. **Hold Date Selection** - UI to set hold date for embargoed samples
3. **Project Details** - Add PROJECT_SET generation if needed
4. **Batch Submission** - Support for multiple submission sets
5. **ENA API Integration** - Direct submission to ENA via API
6. **Validation Feedback** - Pre-submission validation within application

## References

- **ENA Submission Guidelines**: https://ena-docs.readthedocs.io/
- **ERC000024 Checklist**: GSC MIxS water checklist
- **XML Schema**: ENA SRA XML schema documentation
- **Webin-CLI**: ENA's command-line submission tool

## Support

For issues or questions:
1. Check this documentation first
2. Review ENA's official documentation
3. Test in ENA's test environment before production
4. Contact system administrator for application-specific issues
