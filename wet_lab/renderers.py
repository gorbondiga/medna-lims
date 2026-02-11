"""
Custom renderers for exporting data in various formats including ENA XML
"""
from rest_framework import renderers
from django.utils.xmlutils import SimplerXMLGenerator
from io import StringIO, BytesIO
import datetime
import zipfile


class ENAXMLRenderer(renderers.BaseRenderer):
    """
    Renderer for ENA (European Nucleotide Archive) XML submission format
    Generates a ZIP file containing both submission.xml and sample.xml
    Following ERC000024 (GSC MIxS water) checklist schema
    """
    media_type = 'application/zip'
    format = 'zip'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into ENA XML files and package them in a ZIP
        Returns a ZIP file containing submission.xml and sample.xml
        """
        if data is None:
            return b''

        # Handle both single object and list of objects
        if isinstance(data, list):
            samples = data
        elif isinstance(data, dict) and 'results' in data:
            samples = data['results']
        else:
            samples = [data]
        
        # Generate submission.xml content
        submission_xml = self._generate_submission_xml()
        
        # Generate sample.xml content
        sample_xml = self._generate_sample_xml(samples)
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add submission.xml
            zip_file.writestr('submission.xml', submission_xml)
            # Add sample.xml
            zip_file.writestr('sample.xml', sample_xml)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _generate_submission_xml(self):
        """Generate the submission.xml file content"""
        stream = StringIO()
        xml = SimplerXMLGenerator(stream, self.charset)
        xml.startDocument()
        
        xml.startElement('SUBMISSION_SET', {})
        xml.startElement('SUBMISSION', {})
        xml.startElement('ACTIONS', {})
        
        # ADD action
        xml.startElement('ACTION', {})
        xml.startElement('ADD', {})
        xml.endElement('ADD')
        xml.endElement('ACTION')
        
        xml.endElement('ACTIONS')
        xml.endElement('SUBMISSION')
        xml.endElement('SUBMISSION_SET')
        
        xml.endDocument()
        return stream.getvalue()
    
    def _generate_sample_xml(self, samples):
        """Generate the sample.xml file content"""
        stream = StringIO()
        xml = SimplerXMLGenerator(stream, self.charset)
        xml.startDocument()
        
        # Render SAMPLE_SET
        xml.startElement('SAMPLE_SET', {})
        for sample_data in samples:
            self._render_sample(xml, sample_data)
        xml.endElement('SAMPLE_SET')
        
        xml.endDocument()
        return stream.getvalue()
    
    def _render_sample(self, xml, sample_data):
        """Render a single sample following ENA format"""
        # Start SAMPLE with alias
        sample_alias = sample_data.get('sample_id', 'SAMPLE')
        xml.startElement('SAMPLE', {'alias': sample_alias})
        
        # TITLE
        xml.startElement('TITLE', {})
        title = f"{sample_data.get('project_name', 'eDNA')} - {sample_data.get('barcode', sample_alias)}"
        xml.characters(title)
        xml.endElement('TITLE')
        
        # SAMPLE_NAME
        xml.startElement('SAMPLE_NAME', {})
        xml.startElement('TAXON_ID', {})
        xml.characters('256318')  # Default: metagenome taxon ID
        xml.endElement('TAXON_ID')
        xml.startElement('SCIENTIFIC_NAME', {})
        xml.characters('metagenome')
        xml.endElement('SCIENTIFIC_NAME')
        xml.endElement('SAMPLE_NAME')
        
        # SAMPLE_ATTRIBUTES
        xml.startElement('SAMPLE_ATTRIBUTES', {})
        
        # Map fields to ENA attributes with their units (ENA-specific unit format)
        attribute_mapping = [
            ('project_name', 'project name', True, None),
            ('collection_date', 'collection date', True, None),
            ('geographic_location_latitude', 'geographic location (latitude)', True, 'DD'),
            ('geographic_location_longitude', 'geographic location (longitude)', True, 'DD'),
            ('geographic_location_country', 'geographic location (country and/or sea)', True, None),
            ('geo_loc_name', 'geographic location (region and locality)', False, None),
            ('env_broad_scale', 'broad-scale environmental context', True, None),
            ('env_local_scale', 'local environmental context', True, None),
            ('env_medium', 'environmental medium', True, None),
            ('depth', 'depth', False, 'm'),
            ('sample_type', 'sample type', False, None),
            ('sampling_method', 'sampling method', False, None),
            ('samp_collect_device', 'sample collection device', False, None),
            ('samp_mat_process', 'sample material processing', False, None),
            ('samp_size', 'amount or size of sample collected', False, None),
            ('nucl_acid_ext', 'nucleic acid extraction', False, None),
            ('temperature', 'temperature', False, 'ºC'),  # ENA requires º not °
            ('ph', 'pH', False, None),
            ('turbidity', 'turbidity', False, 'FNU'),
            ('conductivity', 'conductivity', False, 'S/m'),
            ('dissolved_oxygen', 'dissolved oxygen', False, 'µmol/kg'),  # ENA requires µmol/kg not mg/L
        ]
        
        for field_name, ena_name, mandatory, unit in attribute_mapping:
            value = sample_data.get(field_name)
            if value or mandatory:
                self._render_attribute(xml, ena_name, value or 'not provided', unit)
        
        # Add ENA checklist reference
        self._render_attribute(xml, 'ENA-CHECKLIST', 'ERC000024')
        
        xml.endElement('SAMPLE_ATTRIBUTES')
        xml.endElement('SAMPLE')
    
    def _render_attribute(self, xml, tag, value, unit=None):
        """Render a single SAMPLE_ATTRIBUTE with optional unit"""
        xml.startElement('SAMPLE_ATTRIBUTE', {})
        xml.startElement('TAG', {})
        xml.characters(str(tag))
        xml.endElement('TAG')
        xml.startElement('VALUE', {})
        xml.characters(str(value))
        xml.endElement('VALUE')
        if unit:
            xml.startElement('UNITS', {})
            xml.characters(str(unit))
            xml.endElement('UNITS')
        xml.endElement('SAMPLE_ATTRIBUTE')
