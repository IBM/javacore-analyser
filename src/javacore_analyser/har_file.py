#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from haralyzer import HarParser


class HarFile:
    """
    Represents a HAR (HTTP Archive) file and provides methods to parse and convert it to XML format.
    
    HAR files contain recorded HTTP transactions including requests, responses, headers, cookies,
    and timing information. This class uses the haralyzer library to parse HAR files and extracts
    HTTP call data for analysis and reporting.
    
    Attributes:
        path (str): The file path to the HAR file
        har (HarParser): The parsed HAR file object from haralyzer library
    """

    def __init__(self, path):
        """
        Initialize a HarFile object by parsing the HAR file at the given path.
        
        Args:
            path (str): The file path to the HAR file to parse

        """
        self.path = path
        with open(path, 'r', encoding='utf-8') as file:
            self.har = HarParser(json.load(file, strict=False))

    def get_xml(self, doc):
        """
        Convert the HAR file data to an XML representation.
        
        Creates an XML element containing all HTTP calls from the HAR file, including
        metadata such as filename, hostname, and browser information.
        
        Args:
            doc (xml.dom.minidom.Document): The XML document to create elements in
            
        Returns:
            xml.dom.minidom.Element: An XML element representing the HAR file with all HTTP calls
        """
        har_file_node = doc.createElement("har_file")
        har_file_node.setAttribute("filename", os.path.basename(self.path))
        
        # Handle cases where HAR file has no valid pages or missing browser info (issue #271)
        try:
            hostname = str(self.har.hostname)
        except (IndexError, AttributeError, KeyError):
            hostname = "unknown"
        har_file_node.setAttribute("hostname", hostname)
        
        try:
            browser = str(self.har.browser)
        except (IndexError, AttributeError, KeyError):
            browser = "unknown"
        har_file_node.setAttribute("browser", browser)
        for page in self.har.pages:
            for entry in page.entries:
                http_call = HttpCall(entry)
                har_file_node.appendChild(http_call.get_xml(doc))
        return har_file_node


class HttpCall:
    INVALID_UTF_CHARACTERS = tuple(chr(code_point) for code_point in range(0x20)
                                   if code_point not in (0x09, 0x0A, 0x0D))

    """
    Represents a single HTTP call extracted from a HAR file entry.
    
    This class extracts and stores detailed information about an HTTP request/response pair,
    including method, status, timing, headers, cookies, and content (for text-based data).
    
    Attributes:
        call: The HAR entry object from haralyzer
        url (str): The URL of the HTTP call
        method (str): The HTTP method (GET, POST, etc.)
        status (str): The HTTP status code
        start_time (str): The start time of the request
        duration (str): Total duration of the request in milliseconds
        timings (str): Detailed timing information
        size (str): Response body size in bytes
        success (str): Whether the request was successful (not 4xx or 5xx)
        request_headers (str): Formatted request headers
        request_cookies (str): Formatted request cookies
        request_content (str): Request body content (if text-based)
        response_headers (str): Formatted response headers
        response_cookies (str): Formatted response cookies
        response_content (str): Response body content (if text-based)
    """

    def __init__(self, call):
        """
        Initialize an HttpCall object from a HAR entry.
        
        Args:
            call: A HAR entry object from haralyzer containing request/response data
        """
        self.call = call
        self.url = call.url
        self.method = str(call.request.method) if hasattr(call.request, 'method') else 'GET'
        self.status = str(call.status)
        self.start_time = str(call.startTime)
        self.duration = str(self.get_total_time())
        self.timings = str(call.timings)
        self.size = str(call.response.bodySize)
        self.success = str(self._calculate_success())
        
        # Request data
        self.request_headers = self.get_headers(call.request.headers) if hasattr(call.request, 'headers') else ''
        self.request_cookies = self.get_cookies(call.request.cookies) if hasattr(call.request, 'cookies') else ''
        self.request_content = self.get_request_content(call.request)
        
        # Response data
        self.response_headers = self.get_headers(call.response.headers) if hasattr(call.response, 'headers') else ''
        self.response_cookies = self.get_cookies(call.response.cookies) if hasattr(call.response, 'cookies') else ''
        self.response_content = self.get_response_content(call.response)
    
    def get_total_time(self):
        """
        Calculate the total time taken for the HTTP call.
        
        Sums all positive timing values from the HAR entry's timings object.
        
        Returns:
            int: Total time in milliseconds
        """
        total = 0
        if len(self.call.timings) > 0:
            for key in self.call.timings.keys():
                time = int(self.call.timings[key])
                if time > 0:
                    total += time
        return total

    def _calculate_success(self):
        """
        Determine if the HTTP call was successful based on status code.
        
        Returns:
            bool: False if status code starts with 4 or 5, True otherwise
        """
        if self.status.startswith('4') or self.status.startswith('5'):
            return False
        return True

    def get_headers(self, headers):
        """Convert headers list to formatted string"""
        if not headers:
            return ''
        header_lines = []
        for header in headers:
            if isinstance(header, dict) and 'name' in header and 'value' in header:
                header_name = HttpCall.__sanitize_xml_attribute_value(str(header['name']))
                header_value = HttpCall.__sanitize_xml_attribute_value(str(header['value']))
                header_lines.append(f"{header_name}: {header_value}")
        return '\n'.join(header_lines)

    def get_cookies(self, cookies):
        """Convert cookies list to formatted string"""
        if not cookies:
            return ''
        cookie_lines = []
        for cookie in cookies:
            if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                cookie_name = HttpCall.__sanitize_xml_attribute_value(str(cookie['name']))
                cookie_value = HttpCall.__sanitize_xml_attribute_value(str(cookie['value']))
                cookie_lines.append(f"{cookie_name}={cookie_value}")
        return '\n'.join(cookie_lines)

    def get_request_content(self, request):
        """Extract request content if it's text"""
        # Access raw_entry directly since haralyzer doesn't expose postData properly
        if not hasattr(request, 'raw_entry'):
            return ''
        
        raw_entry = request.raw_entry
        if 'postData' not in raw_entry:
            return ''
        
        post_data = raw_entry['postData']
        if not post_data:
            return ''
        
        # Check if it's text content
        mime_type = post_data.get('mimeType', '')
        if mime_type and self.is_text_mime_type(mime_type):
            text = post_data.get('text', '')
            return HttpCall.__sanitize_xml_attribute_value(str(text)) if text else ''
        
        return ''

    def get_response_content(self, response):
        """Extract response content if it's text"""
        # Access raw_entry directly since haralyzer doesn't expose content properly
        if not hasattr(response, 'raw_entry'):
            return ''
        
        raw_entry = response.raw_entry
        if 'content' not in raw_entry:
            return ''
        
        content = raw_entry['content']
        if not content:
            return ''
        
        # Check if it's text content
        mime_type = content.get('mimeType', '')
        if mime_type and self.is_text_mime_type(mime_type):
            text = content.get('text', '')
            return HttpCall.__sanitize_xml_attribute_value(str(text)) if text else ''
        
        return ''

    def is_text_mime_type(self, mime_type):
        """Check if MIME type represents text content"""
        text_types = [
            'text/', 'application/json', 'application/xml', 'application/javascript',
            'application/x-www-form-urlencoded', 'application/xhtml+xml'
        ]
        return any(mime_type.startswith(t) for t in text_types)

    @staticmethod
    def __sanitize_xml_attribute_value(value):
        """Remove characters that are invalid in XML attribute values."""
        sanitized_value = value
        for invalid_character in HttpCall.INVALID_UTF_CHARACTERS:
            sanitized_value = sanitized_value.replace(invalid_character, '')
        return sanitized_value

    def get_xml(self, doc):
        """
        Convert the HTTP call data to an XML representation.
        
        Creates an XML element with all HTTP call attributes including URL, method,
        status, timing, headers, cookies, and content.
        
        Args:
            doc (xml.dom.minidom.Document): The XML document to create elements in
            
        Returns:
            xml.dom.minidom.Element: An XML element representing the HTTP call
        """
        http_call_node = doc.createElement("http_call")
        http_call_node.setAttribute("url", HttpCall.__sanitize_xml_attribute_value(self.url))
        http_call_node.setAttribute("method", HttpCall.__sanitize_xml_attribute_value(self.method))
        http_call_node.setAttribute("status", HttpCall.__sanitize_xml_attribute_value(self.status))
        http_call_node.setAttribute("start_time", HttpCall.__sanitize_xml_attribute_value(self.start_time))
        http_call_node.setAttribute("duration", HttpCall.__sanitize_xml_attribute_value(self.duration))
        http_call_node.setAttribute("timings", HttpCall.__sanitize_xml_attribute_value(self.timings))
        http_call_node.setAttribute("size", HttpCall.__sanitize_xml_attribute_value(self.size))
        http_call_node.setAttribute("success", HttpCall.__sanitize_xml_attribute_value(self.success))
        http_call_node.setAttribute("request_headers", self.request_headers)
        http_call_node.setAttribute("request_cookies", self.request_cookies)
        http_call_node.setAttribute("request_content", self.request_content)
        http_call_node.setAttribute("response_headers", self.response_headers)
        http_call_node.setAttribute("response_cookies", self.response_cookies)
        http_call_node.setAttribute("response_content", self.response_content)
        return http_call_node
