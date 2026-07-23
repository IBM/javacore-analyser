#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
import shutil
from multiprocessing.dummy import Pool  # Keep for HTML generation compatibility
from pathlib import Path

import importlib_resources
from lxml import etree
from lxml.etree import XMLSyntaxError
from tqdm import tqdm

from javacore_analyser.file_resolver import FileResolver
from javacore_analyser.plugin_coordinator import PluginCoordinator
from javacore_analyser.properties import Properties


def _create_xml_xsl_for_collection(tmp_dir, templates_dir, xml_xsl_filename, collection, output_file_prefix):
    """Create per-element XML and XSL files in *tmp_dir* from a template in *templates_dir*.

    Args:
        tmp_dir (str): Destination directory (will be created).
        templates_dir (str): Directory containing the template files.
        xml_xsl_filename (str): Base filename (without extension) of the template files.
        collection: Iterable of elements that expose ``get_id()`` and ``is_interesting()``.
        output_file_prefix (str): Prefix prepended to each output filename.
    """
    logging.info("Creating xmls and xsls in " + tmp_dir)
    os.mkdir(tmp_dir)
    extensions = [".xsl", ".xml"]
    for extension in tqdm(extensions, desc="Creating xml/xsl files", unit=" file"):
        file_full_path = os.path.normpath(os.path.join(templates_dir, xml_xsl_filename + extension))
        if not file_full_path.startswith(templates_dir):
            raise Exception("Security exception: Uncontrolled data used in path expression")
        file_content: str = Path(file_full_path).read_text()
        for element in collection:
            element_id = element.get_id()
            filename = output_file_prefix + "_" + str(element_id) + extension
            if filename.startswith("_"):
                filename = filename[1:]
            if element.is_interesting() or not Properties.get_instance().skip_boring():
                file = os.path.join(tmp_dir, filename)
                logging.debug("Writing file " + file)
                f = open(file, "w")
                f.write(file_content.format(id=element_id))
                f.close()
            else:
                logging.debug("Skipping boring file: " + filename)


class HtmlReportGenerator:
    """Generates HTML reports from XML data and XSL stylesheets.

    Handles:
    - XSLT transformations for the main index.html
    - Parallel generation of per-thread and per-javacore HTML pages
    - Copying static resources
    - Plugin-specific XSL and HTML generation
    """

    @staticmethod
    def generate_placeholder_htmls(placeholder_file, directory, collection, file_prefix):
        """Create placeholder HTML files (later replaced by full generated files).

        Args:
            placeholder_file (str): Source placeholder file to copy.
            directory (str): Destination directory (recreated if it already exists).
            collection: Iterable of elements exposing ``get_id()`` and ``is_interesting()``.
            file_prefix (str): Prefix for each output filename.
        """
        logging.info(f"Generating placeholder htmls in {directory}")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.mkdir(directory)

        for element in tqdm(collection, desc="Generating placeholder htmls", unit=" file"):
            if element.is_interesting() or not Properties.get_instance().skip_boring():
                filename = file_prefix + "_" + element.get_id() + ".html"
                if filename.startswith("_"):
                    filename = filename[1:]
                file_path = os.path.join(directory, filename)
                shutil.copy2(placeholder_file, file_path)
        logging.info("Finished generating placeholder htmls")

    @staticmethod
    def create_index_html(input_dir, output_dir, plugin_data=None):
        """Generate the main index.html for the report.

        Copies index.xml, report.xsl, and section XSL files into *input_dir*, generates
        plugins.xsl, then transforms the XML to produce index.html in *output_dir*.

        Args:
            input_dir (str): Temporary directory used for intermediate files.
            output_dir (str): Directory where index.html will be written.
            plugin_data (dict, optional): Plugin data used to generate plugins.xsl.
        """
        # Copy index.xml and report.xsl to temp dir
        index_xml = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "index.xml"))
        shutil.copy2(index_xml, input_dir)

        report_xsl = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "report.xsl"))
        shutil.copy2(report_xsl, input_dir)

        # Copy sections directory containing modular XSL files
        sections_dir = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "sections"))
        sections_dest = os.path.join(input_dir, "sections")
        logging.debug(f"Sections source dir: {sections_dir}")
        logging.debug(f"Sections dest dir: {sections_dest}")
        logging.debug(f"Sections dir exists: {os.path.exists(sections_dir)}")
        if os.path.exists(sections_dir):
            shutil.copytree(sections_dir, sections_dest)
            logging.info(f"Copied sections directory to {sections_dest}")
            if os.path.exists(sections_dest):
                section_files = os.listdir(sections_dest)
                logging.info(f"Section files copied: {section_files}")
        else:
            logging.warning(f"Sections directory not found at {sections_dir}")

        # Generate plugins.xsl file dynamically
        PluginCoordinator.generate_plugins_xsl(input_dir, plugin_data)

        # Prepare XSLT file path and URI for processing
        report_xsl_path = os.path.join(input_dir, "report.xsl")
        report_xsl_uri = "file://" + os.path.abspath(report_xsl_path)
        logging.info(f"Report XSL path: {report_xsl_path}")
        logging.info(f"Report XSL URI: {report_xsl_uri}")

        # Create XML parser with custom FileResolver to handle xsl:include directives
        xslt_parser = etree.XMLParser()
        xslt_parser.resolvers.add(FileResolver(temp_path=input_dir))

        xslt_doc = etree.parse(report_xsl_path, xslt_parser)
        xslt_doc.docinfo.URL = report_xsl_uri
        logging.debug(f"XSLT doc base URL set to: {xslt_doc.docinfo.URL}")
        xslt_transformer = etree.XSLT(xslt_doc)

        source_parser = etree.XMLParser(resolve_entities=True)
        source_doc = etree.parse(input_dir + "/index.xml", source_parser)
        output_doc = xslt_transformer(source_doc)

        output_html_file = output_dir + "/index.html"
        logging.info("Generating file " + output_html_file)
        output_doc.write(output_html_file, pretty_print=True)

    @staticmethod
    def generate_htmls_from_xmls_xsls(report_xml_file, data_input_dir, output_dir):
        """Generate HTML files from pairs of XML+XSL files in *data_input_dir*.

        Uses a process pool for parallel conversion.

        Args:
            report_xml_file (str): Path to the central report.xml (copied into *data_input_dir*).
            data_input_dir (str): Directory containing per-element .xml and .xsl file pairs.
            output_dir (str): Directory where generated .html files will be placed.
        """
        logging.info(f"Starting generating htmls from data from {data_input_dir}")

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        shutil.copy2(report_xml_file, data_input_dir)

        threads_no = HtmlReportGenerator.get_number_of_parallel_threads()
        logging.info(f"Using {threads_no} threads to generate html files")

        list_files = os.listdir(data_input_dir)
        progress_bar = tqdm(desc="Generating html files", unit=' file')

        generate_html_params = [
            (file, data_input_dir, output_dir, progress_bar) for file in list_files
        ]

        with Pool(threads_no) as p:
            p.map(HtmlReportGenerator.generate_html_from_xml_xsl_files, generate_html_params)

        progress_bar.close()
        logging.info(f"Generated html files in {output_dir}")

    @staticmethod
    def get_number_of_parallel_threads():
        """Return the number of parallel threads to use for HTML generation.

        Leaves one CPU free for other tasks.
        """
        return max(1, os.cpu_count() - 1)

    @staticmethod
    def generate_html_from_xml_xsl_files(args):
        """Transform one XML+XSL pair into an HTML file.

        Args:
            args (tuple): (collection_file, collection_input_dir, output_dir, progress_bar)
                - collection_file: Filename within *collection_input_dir* (XSL files only).
                - collection_input_dir: Directory containing the XML/XSL pair.
                - output_dir: Destination directory for the HTML file.
                - progress_bar: tqdm progress bar to update after each file.
        """
        collection_file, collection_input_dir, output_dir, progress_bar = args

        if not collection_file.endswith(".xsl"):
            return

        xsl_file = collection_input_dir + "/" + collection_file
        xml_file = xsl_file.replace(".xsl", ".xml")
        html_file = (output_dir + "/" + collection_file).replace("xsl", "html")
        xslt_doc = etree.parse(xsl_file)
        xslt_transformer = etree.XSLT(xslt_doc)

        try:
            parser = etree.XMLParser(resolve_entities=True)
            source_doc = etree.parse(xml_file, parser)
            logging.debug("Successfully parsed file {}".format(xml_file))
        except XMLSyntaxError as e:
            file_content = Path(xml_file).read_text()
            is_report_xml_generated = os.path.isfile(collection_input_dir + "/" + "report.xml")
            msg = (
                "Error parsing file {}. File content: {}. report.xml generated: {}"
                .format(xml_file, file_content, is_report_xml_generated)
            )
            logging.error(msg)
            raise XMLSyntaxError(msg) from e

        output_doc = xslt_transformer(source_doc)
        logging.debug("Generating file " + html_file)
        output_doc.write(html_file, pretty_print=True)
        progress_bar.update(1)

    @staticmethod
    def create_xml_xsl_for_collection(tmp_dir, xml_xsls_prefix_path, collection, output_file_prefix):
        """Create per-element XML and XSL files in *tmp_dir*.

        Unlike the module-level ``_create_xml_xsl_for_collection``, this variant accepts a
        full path prefix (without extension) instead of a separate directory + filename.

        Args:
            tmp_dir (str): Destination directory (will be created).
            xml_xsls_prefix_path (str): Full path prefix (without extension) of the templates.
            collection: Iterable of elements exposing ``get_id()``.
            output_file_prefix (str): Prefix prepended to each output filename.
        """
        logging.info("Creating xmls and xsls in " + tmp_dir)
        os.mkdir(tmp_dir)
        extensions = [".xsl", ".xml"]
        for extension in extensions:
            file_content = Path(xml_xsls_prefix_path + extension).read_text()
            for element in tqdm(collection, desc="Creating xml/xsl files", unit=" file"):
                element_id = element.get_id()
                filename = output_file_prefix + "_" + str(element_id) + extension
                if filename.startswith("_"):
                    filename = filename[1:]
                file = os.path.join(tmp_dir, filename)
                logging.debug("Writing file " + file)
                f = open(file, "w")
                f.write(file_content.format(id=element_id))
                f.close()
