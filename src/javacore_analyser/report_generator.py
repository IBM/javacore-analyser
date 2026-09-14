#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
import shutil
import tempfile
from datetime import datetime
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import IO, Optional, cast
from xml.dom.minidom import Document, Element, parseString

import importlib_resources
from lxml import etree
from lxml.etree import XMLSyntaxError
from tqdm import tqdm

from javacore_analyser.constants import DATE_FORMAT
from javacore_analyser.properties import Properties


class FileResolver(etree.Resolver):
    """
    Custom URI resolver for XSLT processing to handle xsl:include directives.

    This resolver enables lxml's XSLT processor to locate and include external XSL files
    referenced via <xsl:include> elements in the main XSLT stylesheet. It handles file://
    URIs by converting them to file system paths that lxml can access.

    The resolver is necessary because report.xsl has been modularized into separate section
    files (header.xsl, footer.xsl, etc.) to support a plugin architecture. Without this
    resolver, lxml would fail to locate the included files.

    See: https://lxml.de/resolvers.html for lxml resolver documentation
    """

    def __init__(self, temp_path=None):
        super().__init__()
        self.temp_path = temp_path

    def resolve(self, url, id, context):
        """
        Resolve a URI to a file system path.

        Args:
            url (str): The URI to resolve (may include file:// prefix)
            id (str): The document identifier (unused)
            context: The resolution context from lxml

        Returns:
            The resolved file content if the file exists, None otherwise
        """
        if url.startswith('file://'):
            url = url[7:]  # Remove 'file://' prefix
        if os.path.exists(url):
            return self.resolve_filename(url, context)
        return self.resolve_filename(self.temp_path + os.sep + url, context)


def _create_xml_xsl_for_collection(tmp_dir, templates_dir, xml_xsl_filename, collection, output_file_prefix):
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


class ReportGenerator:
    """Generates HTML report files from a :class:`~javacore_analyser.javacore_set.JavacoreSet`."""

    def __init__(self, javacore_set, output_dir: str):
        """
        Args:
            javacore_set: The :class:`~javacore_analyser.javacore_set.JavacoreSet` instance whose data will be
                rendered into the report.
            output_dir: Path to the directory where the report will be written.
        """
        self.javacore_set = javacore_set
        self.output_dir = output_dir
        self.report_xml_file: Optional[str] = None
        self._doc: Optional[Document] = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def generate_report_files(self):
        """Generate report files in HTML format. All output is written to *self.output_dir*."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_name = temp_dir.name
        logging.info("Created temp dir: " + temp_dir_name)
        self._create_report_xml(temp_dir_name + "/report.xml")
        self._generate_placeholder_htmls(os.path.join(self.output_dir, "threads"), self.javacore_set.threads, "thread")
        self._generate_placeholder_htmls(os.path.join(self.output_dir, "javacores"), self.javacore_set.javacores, "")
        self._create_index_html(temp_dir_name)
        self._generate_htmls_for_threads(temp_dir_name)
        self._generate_htmls_for_javacores(temp_dir_name)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_placeholder_htmls(self, directory, collection, file_prefix):
        placeholder_file = os.path.join(self.output_dir, "data", "html", "processing_data.html")
        logging.info(f"Generating placeholder htmls in {directory}")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.mkdir(directory)
        for element in tqdm(collection, desc="Generating placeholder htmls", unit=" file"):
            if element.is_interesting() or not Properties.get_instance().skip_boring():
                filename = file_prefix + "_" + element.get_id() + ".html"
                if filename.startswith("_"):
                    filename = filename[1:]
                shutil.copy2(placeholder_file, os.path.join(directory, filename))
        logging.info("Finished generating placeholder htmls")

    def _generate_htmls_for_threads(self, temp_dir_name: str):
        _create_xml_xsl_for_collection(
            os.path.join(temp_dir_name, "threads"),
            os.path.join(self.output_dir, "data", "xml", "threads"),
            "thread",
            self.javacore_set.threads,
            "thread",
        )
        self._generate_htmls_from_xmls_xsls(
            os.path.join(temp_dir_name, "threads"),
            os.path.join(self.output_dir, "threads"),
        )

    def _generate_htmls_for_javacores(self, temp_dir_name: str):
        _create_xml_xsl_for_collection(
            os.path.join(temp_dir_name, "javacores"),
            os.path.join(self.output_dir, "data", "xml", "javacores"),
            "javacore",
            self.javacore_set.javacores,
            "",
        )
        self._generate_htmls_from_xmls_xsls(
            os.path.join(temp_dir_name, "javacores"),
            os.path.join(self.output_dir, "javacores"),
        )

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def _create_report_xml(self, output_file: str):
        """
        Generate an XML report containing information about the JavacoreSet data.

        Parameters:
        - output_file (str): The path and filename of the output XML file.
        """
        javacore_set = self.javacore_set

        logging.info("Generating report xml")

        self._doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
        <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')
        doc: Document = cast(Document, self._doc)
        doc_node: Element = cast(Element, doc.documentElement)

        # Add data types information
        data_types_node = cast(Element, doc.createElement("data_types"))
        doc_node.appendChild(data_types_node)
        for data_type in javacore_set.data_types:
            type_node = cast(Element, doc.createElement("type"))
            type_node.appendChild(doc.createTextNode(data_type))
            data_types_node.appendChild(type_node)

        javacore_count_node = cast(Element, doc.createElement("javacore_count"))
        javacore_count_node.appendChild(doc.createTextNode(str(len(javacore_set.javacores))))
        doc_node.appendChild(javacore_count_node)
        report_info_node = cast(Element, doc.createElement("report_info"))
        doc_node.appendChild(report_info_node)
        generation_time_node = cast(Element, doc.createElement("generation_time"))
        report_info_node.appendChild(generation_time_node)
        generation_time_node.appendChild(doc.createTextNode(str(datetime.now().strftime(DATE_FORMAT))))
        doc_node.setAttribute("use_ml", str(javacore_set.use_ml))

        # Only include javacore-specific data if javacores are present
        if 'javacores' in javacore_set.data_types and len(javacore_set.javacores) > 0:
            generation_javacores_node = doc.createElement("javacores_generation_time")
            report_info_node.appendChild(generation_javacores_node)
            generation_javacores_node_starting_time = doc.createElement("starting_time")
            generation_javacores_node.appendChild(generation_javacores_node_starting_time)
            generation_javacores_node_starting_time.appendChild(
                doc.createTextNode(str(javacore_set.javacores[0].datetime.strftime(DATE_FORMAT))))
            generation_javacores_node_end_time = doc.createElement("end_time")
            generation_javacores_node.appendChild(generation_javacores_node_end_time)
            generation_javacores_node_end_time.appendChild(
                doc.createTextNode(str(javacore_set.javacores[-1].datetime.strftime(DATE_FORMAT))))

            javacore_list_node = doc.createElement("javacore_list")
            report_info_node.appendChild(javacore_list_node)
            for jc in javacore_set.javacores:
                javacore_node = doc.createElement("javacore")
                javacore_list_node.appendChild(javacore_node)
                javacore_file_node = doc.createElement("javacore_file_name")
                javacore_node.appendChild(javacore_file_node)
                javacore_file_node.appendChild(doc.createTextNode(jc.basefilename()))
                javacore_file_time_stamp_node = doc.createElement("javacore_file_time_stamp")
                javacore_node.appendChild(javacore_file_time_stamp_node)
                javacore_file_time_stamp_node.appendChild(doc.createTextNode(str(jc.datetime.strftime(DATE_FORMAT))))
                javacore_total_cpu_node = doc.createElement("javacore_cpu_percentage")
                javacore_node.appendChild(javacore_total_cpu_node)
                javacore_total_cpu_node.appendChild(doc.createTextNode(str(jc.get_cpu_percentage())))
                javacore_load_node = doc.createElement("javacore_load")
                javacore_node.appendChild(javacore_load_node)
                javacore_load_node.appendChild(doc.createTextNode(str(jc.get_load())))
                if jc.current_thread:
                    current_thread_node = doc.createElement("javacore_current_thread")
                    current_thread_node.appendChild(doc.createTextNode(jc.current_thread.name))
                    if jc.current_thread.thread:
                        current_thread_node.setAttribute("thread_hash", jc.current_thread.thread.get_hash())
                    javacore_node.appendChild(current_thread_node)
                # When ML classification is enabled, count how many thread snapshots in this javacore received each
                # classification label. The counts are stored as <classification_entry value="…" count="…"/> children
                # so the thread-classification-over-time chart can read them per javacore.
                if javacore_set.use_ml:
                    classification_counts: dict[str, int] = {}
                    for snapshot in jc.snapshots:
                        label = snapshot.get_classification()
                        if label:
                            classification_counts[label] = classification_counts.get(label, 0) + 1
                    jc_classifications_node = doc.createElement("javacore_classifications")
                    javacore_node.appendChild(jc_classifications_node)
                    for label, count in classification_counts.items():
                        entry_node = doc.createElement("classification_entry")
                        entry_node.setAttribute("value", label)
                        entry_node.setAttribute("count", str(count))
                        jc_classifications_node.appendChild(entry_node)

        verbose_gc_list_node = doc.createElement("verbose_gc_list")
        report_info_node.appendChild(verbose_gc_list_node)
        total_collects_in_time_limits = 0
        for vgc in javacore_set.gc_parser.get_files():
            verbose_gc_node = doc.createElement("verbose_gc")
            verbose_gc_list_node.appendChild(verbose_gc_node)
            verbose_gc_file_name_node = doc.createElement("verbose_gc_file_name")
            verbose_gc_node.appendChild(verbose_gc_file_name_node)
            verbose_gc_file_name_node.appendChild(doc.createTextNode(vgc.get_file_name()))
            verbose_gc_collects_node = doc.createElement("verbose_gc_collects")
            verbose_gc_node.appendChild(verbose_gc_collects_node)
            verbose_gc_collects_node.appendChild(doc.createTextNode(str(vgc.get_number_of_collects())))
            total_collects_in_time_limits += vgc.get_number_of_collects()
            verbose_gc_total_collects_node = doc.createElement("verbose_gc_total_collects")
            verbose_gc_node.appendChild(verbose_gc_total_collects_node)
            verbose_gc_total_collects_node.appendChild(doc.createTextNode(str(vgc.get_total_number_of_collects())))
        verbose_gc_list_node.setAttribute("total_collects_in_time_limits", str(total_collects_in_time_limits))

        if len(javacore_set.har_files) > 0:
            har_files_node = cast(Element, doc.createElement("har_files"))
            doc_node.appendChild(har_files_node)
            for har in javacore_set.har_files:
                har_files_node.appendChild(har.get_xml(doc))

        # Include system info if javacores or verbosegc are present and jvm_info is available
        system_info_node: Optional[Element]
        if ('javacores' in javacore_set.data_types or 'verbosegc' in javacore_set.data_types) \
                and javacore_set.jvm_info is not None:
            system_info_node = cast(Element, doc.createElement("system_info"))
            doc_node.appendChild(system_info_node)
        else:
            system_info_node = None

        tips_node = doc.createElement("tips")
        report_info_node.appendChild(tips_node)
        for tip in javacore_set.tips:
            tip_node = doc.createElement("tip")
            tips_node.appendChild(tip_node)
            tip_node.appendChild(doc.createTextNode(tip))
        tips_node.setAttribute("ai_tips", javacore_set.ai_tips)

        if system_info_node is not None and javacore_set.jvm_info is not None:
            system_info_node.appendChild(javacore_set.jvm_info.to_xml(doc))

        # Only add javacore-dependent data if javacores are present
        if 'javacores' in javacore_set.data_types:
            doc_node.appendChild(self._get_blockers_xml(doc))
            doc_node.appendChild(javacore_set.threads.get_xml(doc))
            doc_node.appendChild(javacore_set.stacks.get_xml(doc))

        doc_node.appendChild(javacore_set.gc_parser.get_xml(doc))

        # Add plugin data to XML if plugins were processed
        if javacore_set.plugin_data:
            try:
                logging.info("Adding plugin data to report XML")
                plugins_node = cast(Element, doc.createElement("plugins"))
                doc_node.appendChild(plugins_node)
                for plugin_name, plugin_info in javacore_set.plugin_data.items():
                    try:
                        plugin = plugin_info['plugin']
                        data = plugin_info['data']
                        logging.debug(f"Generating XML for plugin: {plugin.get_display_name()}")
                        plugin_xml = plugin.generate_xml(doc, data)
                        plugins_node.appendChild(plugin_xml)
                        logging.debug(f"Successfully added XML for plugin: {plugin.get_display_name()}")
                    except Exception as e:
                        logging.error(f"Error generating XML for plugin {plugin_name}: {e}")
                logging.info(f"Successfully added {len(javacore_set.plugin_data)} plugin(s) to report XML")
            except Exception as e:
                logging.error(f"Error adding plugin data to XML: {e}")

        doc.appendChild(doc_node)  # type: ignore[type-var]

        with open(output_file, 'w', encoding='utf-8') as stream:
            doc.writexml(stream, indent="  ", addindent="  ", newl='\n', encoding="utf-8")
        doc.unlink()
        self.report_xml_file = output_file

        logging.info("Finished generating report xml")

    def _get_blockers_xml(self, doc: Document) -> Element:
        blockers_node = doc.createElement("blockers")
        count = 0
        for blocked in self.javacore_set.blocked_snapshots:
            blocker_node = doc.createElement("blocker")
            blocker_id_node = doc.createElement("blocker_id")
            blocker_node.appendChild(blocker_id_node)
            blocker_id_node.appendChild(doc.createTextNode(str(blocked.get(0).blocker.thread.id)))
            blockers_node.appendChild(blocker_node)
            blocker_name_node = doc.createElement("blocker_name")
            blocker_node.appendChild(blocker_name_node)
            blocker_name_node.appendChild(doc.createTextNode(blocked.get(0).blocker.name))
            blocker_hash_node = doc.createElement("blocker_hash")
            blocker_node.appendChild(blocker_hash_node)
            blocker_hash_node.appendChild(doc.createTextNode(blocked.get(0).blocker.get_thread_hash()))
            blocker_size_node = doc.createElement("blocker_size")
            blocker_node.appendChild(blocker_size_node)
            blocked_size = len(blocked.get_threads_set())
            blocker_size_node.appendChild(doc.createTextNode(str(blocked_size)))
            if count > 9:
                break
            count += 1
        return blockers_node

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def get_javacore_set_in_xml(self) -> str:
        """Returns the contents of the XML report file as a string."""
        file: Optional[IO[str]] = None
        try:
            file = open(self.report_xml_file, "r")  # type: ignore[arg-type]
            return file.read()
        finally:
            if file is not None:
                file.close()

    def generate_plugin_section_header(self, section_id: str, section_title: str, description: str) -> str:
        """
        Generate standardized HTML header for plugin sections.

        Args:
            section_id: Unique identifier for the section (used in HTML IDs and JavaScript)
            section_title: Human-readable title displayed in the section header
            description: HTML content describing what the section shows

        Returns:
            HTML string containing the section header and documentation wrapper
        """
        from html import escape
        escaped_title = escape(section_title)
        return (
            f'<h3><a id="toggle_{section_id}" href="javascript:expand_it({section_id},toggle_{section_id})"'
            f' class="expandit">{escaped_title}</a></h3>\n'
            f'<div id="{section_id}" style="display:none;">\n'
            f'    <a id="toggle{section_id}doc"'
            f' href="javascript:expand_it({section_id}doc,toggle{section_id}doc)" class="expandit">\n'
            f'        What does this section tell me?</a>\n'
            f'    <div id="{section_id}doc" style="display:none;">\n'
            f'        {description}\n'
            f'    </div>\n\n'
        )

    def _generate_plugins_xsl(self, temp_dir: str) -> Optional[str]:
        """
        Generate plugins.xsl file dynamically from loaded plugin HTML content.

        :param temp_dir: Temporary directory where XSL files are stored
        :return: Path to generated plugins.xsl file, or None if generation fails
        """
        plugin_data = self.javacore_set.plugin_data
        plugins_xsl_path = os.path.join(temp_dir, "plugins.xsl")

        try:
            plugins_xsl_content = '''<?xml version="1.0" encoding="UTF-8"?>

<!--
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# This file is auto-generated during report creation.
# It contains XSL templates for all loaded plugins.
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template name="plugins">
'''
            if plugin_data:
                logging.info("Generating plugins.xsl with plugin HTML content")
                for plugin_name, plugin_info in plugin_data.items():
                    try:
                        plugin = plugin_info['plugin']
                        data = plugin_info.get('data', {})
                        html_content = plugin.generate_html(data)
                        if html_content:
                            section_id = plugin_name.replace('_', '')
                            section_header = self.generate_plugin_section_header(
                                section_id=section_id,
                                section_title=plugin.get_display_name(),
                                description=plugin.get_description(),
                            )
                            full_html = section_header + html_content + '\n</div>\n'
                            plugins_xsl_content += f'''
        <!-- Plugin: {plugin.get_display_name()} -->
        <xsl:text disable-output-escaping="yes"><![CDATA[
{full_html}
        ]]></xsl:text>

'''
                            logging.info(f"Added HTML content for plugin: {plugin.get_display_name()}")
                        else:
                            logging.debug(f"Plugin {plugin.get_display_name()} returned no HTML content")
                    except Exception as e:
                        logging.error(f"Error generating HTML for plugin {plugin_name}: {e}")
                        logging.exception(e)
                        plugins_xsl_content += f'''
        <!-- Plugin: {plugin_name} - Error generating HTML -->
        <xsl:text disable-output-escaping="yes"><![CDATA[
        <div class="error_row" style="padding: 10px; margin: 10px 0;">
            <strong>Error in plugin {plugin_name}:</strong> {str(e).replace('<', '&lt;').replace('>', '&gt;')}
        </div>
        ]]></xsl:text>

'''
            else:
                plugins_xsl_content += "        <!-- No plugins loaded -->\n"

            plugins_xsl_content += '''    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
'''
            with open(plugins_xsl_path, 'w', encoding='utf-8') as f:
                f.write(plugins_xsl_content)
            logging.info(f"Generated plugins.xsl at {plugins_xsl_path}")
            return plugins_xsl_path

        except Exception as e:
            logging.error(f"Error generating plugins.xsl: {e}")
            try:
                with open(plugins_xsl_path, 'w', encoding='utf-8') as f:
                    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template name="plugins">
        <!-- Error generating plugin templates -->
    </xsl:template>
</xsl:stylesheet>
''')
                return plugins_xsl_path
            except Exception:
                return None

    def _create_index_html(self, temp_dir_name: str):
        index_xml = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "index.xml"))
        shutil.copy2(index_xml, temp_dir_name)

        report_xsl = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "report.xsl"))
        shutil.copy2(report_xsl, temp_dir_name)

        sections_dir = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "sections"))
        sections_dest = os.path.join(temp_dir_name, "sections")
        logging.debug(f"Sections source dir: {sections_dir}")
        logging.debug(f"Sections dest dir: {sections_dest}")
        logging.debug(f"Sections dir exists: {os.path.exists(sections_dir)}")
        if os.path.exists(sections_dir):
            shutil.copytree(sections_dir, sections_dest)
            logging.info(f"Copied sections directory to {sections_dest}")
            if os.path.exists(sections_dest):
                logging.info(f"Section files copied: {os.listdir(sections_dest)}")
        else:
            logging.warning(f"Sections directory not found at {sections_dir}")

        self._generate_plugins_xsl(temp_dir_name)

        report_xsl_path = os.path.join(temp_dir_name, "report.xsl")
        report_xsl_uri = "file://" + os.path.abspath(report_xsl_path)
        logging.info(f"Report XSL path: {report_xsl_path}")
        logging.info(f"Report XSL URI: {report_xsl_uri}")

        xslt_parser = etree.XMLParser()
        xslt_parser.resolvers.add(FileResolver(temp_path=temp_dir_name))
        xslt_doc = etree.parse(report_xsl_path, xslt_parser)
        xslt_doc.docinfo.URL = report_xsl_uri
        logging.debug(f"XSLT doc base URL set to: {xslt_doc.docinfo.URL}")
        xslt_transformer = etree.XSLT(xslt_doc)

        source_parser = etree.XMLParser(resolve_entities=True)
        source_doc = etree.parse(temp_dir_name + "/index.xml", source_parser)
        output_doc = xslt_transformer(source_doc)

        output_html_file = self.output_dir + "/index.html"
        logging.info("Generating file " + output_html_file)
        output_doc.write(output_html_file, pretty_print=True)

    def _generate_htmls_from_xmls_xsls(self, data_input_dir: str, output_dir: str):
        logging.info(f"Starting generating htmls from data from {data_input_dir}")

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        shutil.copy2(self.report_xml_file, data_input_dir)

        threads_no = self._get_number_of_parallel_threads()
        logging.info(f"Using {threads_no} threads to generate html files")

        list_files = [f for f in os.listdir(data_input_dir) if f.endswith(".xsl")]
        logging.info(f"Generating {len(list_files)} html files from {data_input_dir}")

        params = [(f, data_input_dir, output_dir) for f in list_files]
        with Pool(threads_no) as p:
            for _ in tqdm(
                p.imap_unordered(ReportGenerator._generate_html_from_xml_xsl_files, params),
                total=len(params),
                desc="Generating html files",
                unit=' file',
            ):
                pass

        logging.info(f"Generated html files in {output_dir}")

    def _get_number_of_parallel_threads(self) -> int:
        return max(1, (os.cpu_count() or 2) - 1)

    # Must remain @staticmethod: passed as a picklable callable to multiprocessing.Pool.imap_unordered.
    # Instance methods cannot be pickled by Python's multiprocessing module.
    @staticmethod
    def _generate_html_from_xml_xsl_files(args):
        collection_file, collection_input_dir, output_dir = args

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
            msg = ("Error parsing file {}. File content: {}. report.xml generated: {}"
                   .format(xml_file, file_content, is_report_xml_generated))
            logging.error(msg)
            raise XMLSyntaxError(msg) from e

        output_doc = xslt_transformer(source_doc)
        logging.debug("Generating file " + html_file)
        output_doc.write(html_file, pretty_print=True)
