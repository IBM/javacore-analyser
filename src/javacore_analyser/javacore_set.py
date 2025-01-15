#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import fnmatch
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from multiprocessing.dummy import Pool
from pathlib import Path
from xml.dom.minidom import parseString

import importlib_resources
from lxml import etree
from lxml.etree import XMLSyntaxError
from tqdm import tqdm

from javacore_analyser import tips
from javacore_analyser.code_snapshot_collection import CodeSnapshotCollection
from javacore_analyser.constants import *
from javacore_analyser.har_file import HarFile
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.snapshot_collection import SnapshotCollection
from javacore_analyser.snapshot_collection_collection import SnapshotCollectionCollection
from javacore_analyser.verbose_gc import VerboseGcParser


def _create_xml_xsl_for_collection(tmp_dir, templates_dir, xml_xsl_filename, collection, output_file_prefix):
    logging.info("Creating xmls and xsls in " + tmp_dir)
    os.mkdir(tmp_dir)
    extensions = [".xsl", ".xml"]
    for extension in tqdm(extensions, desc="Creating xml/xsl files", unit=" file"):
        file_full_path = os.path.normpath(os.path.join(templates_dir, xml_xsl_filename + extension))
        if not file_full_path.startswith(templates_dir):
            raise Exception("Security exception: Uncontrolled data used in path expression")
        file_content = Path(file_full_path).read_text()
        for element in collection:
            element_id = element.get_id()
            filename = output_file_prefix + "_" + str(element_id) + extension
            if filename.startswith("_"):
                filename = filename[1:]
            file = os.path.join(tmp_dir, filename)
            logging.debug("Writing file " + file)
            f = open(file, "w")
            f.write(file_content.format(id=element_id))
            f.close()


class JavacoreSet:
    """represents a single javacore collection
    consisting of one or more javacore files"""

    def __init__(self, path):
        self.path = path  # path of the folder where the javacores are located
        # start of static information
        self.number_of_cpus = None  # number of cpus the VM is using
        self.xmx = ""
        self.xms = ""
        self.xmn = ""
        self.gc_policy = ""
        self.compressed_refs = False
        self.verbose_gc = False
        self.os_level = ""
        self.architecture = ""
        self.java_version = ""
        self.user_args = []
        # end of static information
        self.files = []
        self.javacores = []
        self.excluded_javacores = []
        self.verbose_gc_files = []
        self.threads = SnapshotCollectionCollection(Thread)
        self.stacks = SnapshotCollectionCollection(CodeSnapshotCollection)
        self.report_xml_file = None

        self.doc = None

        '''
        List where each element is SnapshotCollection containing all threads blocked by given thread. 
        You can check the blocking thread by looking at snapshotCollection.get(0).get_blocker()
        '''
        # TODO this list is redundant with the data stored in Thread Snapshot. Should be removed in the future.
        self.blocked_snapshots = []
        self.tips = []
        self.gc_parser = VerboseGcParser()
        self.har_files = []

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    @staticmethod
    def process_javacores(input_path):
        """
        Processes Java core data and generates tips based on the analysis.

        Args:
            input_path (str): The path to the directory containing the Javacore data.

        Returns:
            JavacoreSet: A JavacoreSet object containing the analysis results.
        """
        jset = JavacoreSet.create(input_path)
        jset.print_java_settings()
        jset.populate_snapshot_collections()
        jset.sort_snapshots()
        # jset.find_top_blockers()
        jset.print_blockers()
        jset.print_thread_states()
        jset.generate_tips()
        return jset

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def generate_report_files(self, output_dir):
        """
        Generate report files in HTML format.

        Parameters:
        - output_dir (str): The directory where the generated report files will be saved.

        Returns:
        - None
        """
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_name = temp_dir.name
        logging.info("Created temp dir: " + temp_dir_name)
        self.__create_report_xml(temp_dir_name + "/report.xml")
        placeholder_filename = os.path.join(output_dir, "data", "html", "processing_data.html")
        self.__generate_placeholder_htmls(placeholder_filename,
                                          os.path.join(output_dir, "threads"),
                                          self.threads, "thread")
        self.__generate_placeholder_htmls(placeholder_filename,
                                          os.path.join(output_dir, "javacores"),
                                          self.javacores, "")
        self.__create_index_html(temp_dir_name, output_dir)
        self.__generate_htmls_for_threads(output_dir, temp_dir_name)
        self.__generate_htmls_for_javacores(output_dir, temp_dir_name)

    @staticmethod
    def __generate_placeholder_htmls(placeholder_file, directory, collection, file_prefix):
        logging.info(f"Generating placeholder htmls in {directory}")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.mkdir(directory)

        for element in tqdm(collection, desc="Generating placeholder htmls", unit=" files"):
            filename = file_prefix + "_" + element.get_id() + ".html"
            if filename.startswith("_"):
                filename = filename[1:]
            file_path = os.path.join(directory, filename)
            shutil.copy2(placeholder_file, file_path)
        logging.info("Finished generating placeholder htmls")

    def __generate_htmls_for_threads(self, output_dir, temp_dir_name):
        _create_xml_xsl_for_collection(os.path.join(temp_dir_name, "threads"),
                                       os.path.join(output_dir, "data", "xml", "threads"), "thread",
                                       self.threads,
                                       "thread")
        self.generate_htmls_from_xmls_xsls(self.report_xml_file,
                                           os.path.join(temp_dir_name, "threads"),
                                           os.path.join(output_dir, "threads"))

    def __generate_htmls_for_javacores(self, output_dir, temp_dir_name):
        _create_xml_xsl_for_collection(os.path.join(temp_dir_name, "javacores"),
                                       os.path.join(output_dir, "data", "xml", "javacores"), "javacore",
                                       self.javacores,
                                       "")
        self.generate_htmls_from_xmls_xsls(self.report_xml_file,
                                           os.path.join(temp_dir_name, "javacores"),
                                           os.path.join(output_dir, "javacores"))

    def populate_snapshot_collections(self):
        for javacore in self.javacores:
            javacore.print_javacore()
            for s in tqdm(javacore.snapshots, desc="Populating snapshot collection", unit=" javacore"):
                self.threads.add_snapshot(s)
                self.stacks.add_snapshot(s)

    def print_java_settings(self):
        logging.debug("number of CPUs: {}".format(self.number_of_cpus))
        logging.debug("Xmx: {}".format(self.xmx))
        logging.debug("Xms: {}".format(self.xms))
        logging.debug("Xmn: {}".format(self.xmn))
        logging.debug("Verbose GC: {}".format(self.verbose_gc))
        logging.debug("GC policy: {}".format(self.gc_policy))
        logging.debug("Compressed refs: {}".format(self.compressed_refs))
        logging.debug("Architecture: {}".format(self.architecture))
        logging.debug("Java version: {}".format(self.java_version))
        logging.debug("OS Level: {}".format(self.os_level))

    @staticmethod
    def create(path):
        jset = JavacoreSet(path)
        jset.populate_files_list()
        if len(jset.files) < 1:
            raise RuntimeError("No javacores found. You need at least one javacore. Exiting with error 13")
        first_javacore = jset.get_one_javacore()
        jset.parse_common_data(first_javacore)
        jset.parse_javacores()
        jset.parse_verbose_gc_files()
        jset.sort_snapshots()
        jset.__generate_blocked_snapshots_list()
        return jset

    def get_one_javacore(self):
        """ finds one javacore file from the collection
        the objective is to get VM information like number of CPUs etc
        it is assumed all the javacores come from one collection, so this information will be the same
        in all the javacores, wo we just open whichever one we happen to find first.
        """
        return self.files[0]

    def populate_files_list(self):
        """
        This methods populates self.files structure and sets self.path.
        """
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            for file in filenames:
                if fnmatch.fnmatch(file, '*javacore*.txt'):
                    file_size = os.path.getsize(os.path.join(dirpath, file))
                    if file_size > MIN_JAVACORE_SIZE:
                        self.files.append(file)
                        self.path = dirpath
                        logging.info("Javacore file found: " + file)
                    else:
                        logging.info(f"Excluding javacore file {file} with size {file_size} bytes")
                        self.excluded_javacores.append({"file": file,
                                                        "reason": tips.ExcludedJavacoresTip.SMALL_SIZE_JAVACORES.format(
                                                            file, file_size)})
                if fnmatch.fnmatch(file, '*verbosegc*.txt*'):
                    self.gc_parser.add_file(dirpath + os.sep + file)
                    logging.info("VerboseGC file found: " + file)
                if fnmatch.fnmatch(file, "*.har"):
                    self.har_files.append(HarFile(dirpath + os.sep + file))
                    logging.info("HAR file found: " + file)

        # sorting files by name.
        # Unless the user changed the javacore file name format, this is equivalent to sorting by date
        self.files.sort()

    def parse_common_data(self, filename):
        """ extracts information that is common to all the javacores, like the number of CPUs """
        filename = os.path.join(self.path, filename)
        curr_line = ""
        i = 0
        file = None
        try:
            file = open(filename, 'r')
            for line in file:
                i += 1
                if line.startswith(CPU_NUMBER_TAG):  # for example: 3XHNUMCPUS       How Many       : 16
                    self.number_of_cpus = line.split()[-1]
                    continue
                elif line.startswith(USER_ARGS):
                    self.parse_user_args(line)
                    continue
                elif line.startswith(OS_LEVEL):
                    self.os_level = line[line.rfind(":") + 1:].strip()
                    continue
                elif line.startswith(ARCHITECTURE):
                    self.architecture = line[line.rfind(":") + 1:].strip()
                    continue
                elif line.startswith(JAVA_VERSION):
                    self.java_version = line[len(JAVA_VERSION) + 1:].strip()
                    continue
        except Exception as ex:
            logging.exception(ex)
            logging.error(f'Error during processing file: {file.name} \n'
                          f'line number: {i} \n'
                          f'line: {curr_line}\n'
                          f'Check the exception below what happened')
        finally:
            file.close()

    def parse_javacores(self):
        """ creates a Javacore object for each javacore...txt file in the given path """
        for filename in tqdm(self.files, "Parsing javacore files", unit=" file"):
            filename = os.path.join(self.path, filename)
            javacore = Javacore()
            javacore.create(filename, self)
            self.javacores.append(javacore)
        self.javacores.sort(key=lambda x: x.timestamp)

    def parse_verbose_gc_files(self):
        start = self.javacores[0].datetime
        stop = self.javacores[-1].datetime
        self.gc_parser.parse_files(start, stop)

    # def find_thread(self, thread_id):
    #     """ Checks if thread_name already existing in this javacore set """
    #     for thread in self.threads:
    #         if thread.get_id() == thread_id:
    #             return thread
    #     return None

    def sort_snapshots(self):
        for thread in tqdm(self.threads, "Sorting snapshot data", unit=" snapshot"):
            thread.sort_snapshots()
            # thread.compare_call_stacks()

    def get_blockers_xml(self):
        blockers_node = self.doc.createElement("blockers")
        count = 0
        for blocked in self.blocked_snapshots:
            blocker_node = self.doc.createElement("blocker")
            blocker_id_node = self.doc.createElement("blocker_id")
            blocker_node.appendChild(blocker_id_node)
            blocker_id_node.appendChild(self.doc.createTextNode(str(blocked.get(0).blocker.thread.id)))
            blockers_node.appendChild(blocker_node)
            blocker_name_node = self.doc.createElement("blocker_name")
            blocker_node.appendChild(blocker_name_node)
            blocker_name_node.appendChild(self.doc.createTextNode(blocked.get(0).blocker.name))
            blocker_hash_node = self.doc.createElement("blocker_hash")
            blocker_node.appendChild(blocker_hash_node)
            blocker_hash_node.appendChild(self.doc.createTextNode(blocked.get(0).blocker.get_thread_hash()))
            blocker_size_node = self.doc.createElement("blocker_size")
            blocker_node.appendChild(blocker_size_node)
            blocked_size = len(blocked.get_threads_set())
            blocker_size_node.appendChild(self.doc.createTextNode(str(blocked_size)))
            if count > 9:
                break
            count = count + 1
        return blockers_node

    def print_thread_states(self):
        for thread in self.threads:
            logging.debug("max running states:" + str(thread.get_continuous_running_states()))
            logging.debug(thread.name + "(id: " + str(thread.id) + "; hash: " + thread.get_hash() + ") " +
                          "states: " + thread.get_snapshot_states())

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def __create_report_xml(self, output_file):
        """
        Generate an XML report containing information about the Javacoreset data.

        Parameters:
        - output_file (str): The path and filename of the output XML file.

        Returns:
        None
        """

        logging.info("Generating report xml")

        self.doc = parseString('''<?xml version="1.0" encoding="UTF-8" ?>
        <?xml-stylesheet type="text/xsl" href="data/report.xsl"?><doc/>''')

        doc_node = self.doc.documentElement

        javacore_count_node = self.doc.createElement("javacore_count")
        javacore_count_node.appendChild(self.doc.createTextNode(str(len(self.javacores))))
        doc_node.appendChild(javacore_count_node)
        report_info_node = self.doc.createElement("report_info")
        doc_node.appendChild(report_info_node)
        generation_time_node = self.doc.createElement("generation_time")
        report_info_node.appendChild(generation_time_node)
        generation_time_node.appendChild(self.doc.createTextNode(str(datetime.now().strftime(DATE_FORMAT))))

        generation_javacores_node = self.doc.createElement("javacores_generation_time")
        report_info_node.appendChild(generation_javacores_node)
        generation_javacores_node_starting_time = self.doc.createElement("starting_time")
        generation_javacores_node.appendChild(generation_javacores_node_starting_time)
        generation_javacores_node_starting_time.appendChild(
            self.doc.createTextNode(str(self.javacores[0].datetime.strftime(DATE_FORMAT))))
        generation_javacores_node_end_time = self.doc.createElement("end_time")
        generation_javacores_node.appendChild(generation_javacores_node_end_time)
        generation_javacores_node_end_time.appendChild(
            self.doc.createTextNode(str(self.javacores[-1].datetime.strftime(DATE_FORMAT))))

        javacore_list_node = self.doc.createElement("javacore_list")
        report_info_node.appendChild(javacore_list_node)
        for jc in self.javacores:
            javacore_node = self.doc.createElement("javacore")
            javacore_list_node.appendChild(javacore_node)
            javacore_file_node = self.doc.createElement("javacore_file_name")
            javacore_node.appendChild(javacore_file_node)
            javacore_file_node.appendChild(self.doc.createTextNode(jc.basefilename()))
            javacore_file_time_stamp_node = self.doc.createElement("javacore_file_time_stamp")
            javacore_node.appendChild(javacore_file_time_stamp_node)
            javacore_file_time_stamp_node.appendChild(self.doc.createTextNode(str(jc.datetime.strftime(DATE_FORMAT))))
            javacore_total_cpu_node = self.doc.createElement("javacore_cpu_percentage")
            javacore_node.appendChild(javacore_total_cpu_node)
            javacore_total_cpu_node.appendChild(self.doc.createTextNode(str(jc.get_cpu_percentage())))
            javacore_load_node = self.doc.createElement("javacore_load")
            javacore_node.appendChild(javacore_load_node)
            javacore_load_node.appendChild(self.doc.createTextNode(str(jc.get_load())))

        verbose_gc_list_node = self.doc.createElement("verbose_gc_list")
        report_info_node.appendChild(verbose_gc_list_node)

        total_collects_in_time_limits = 0
        for vgc in self.gc_parser.get_files():
            verbose_gc_node = self.doc.createElement("verbose_gc")
            verbose_gc_list_node.appendChild(verbose_gc_node)
            verbose_gc_file_name_node = self.doc.createElement("verbose_gc_file_name")
            verbose_gc_node.appendChild(verbose_gc_file_name_node)
            verbose_gc_file_name_node.appendChild(self.doc.createTextNode(vgc.get_file_name()))
            verbose_gc_collects_node = self.doc.createElement("verbose_gc_collects")
            verbose_gc_node.appendChild(verbose_gc_collects_node)
            verbose_gc_collects_node.appendChild(self.doc.createTextNode(str(vgc.get_number_of_collects())))
            total_collects_in_time_limits += vgc.get_number_of_collects()
            verbose_gc_total_collects_node = self.doc.createElement("verbose_gc_total_collects")
            verbose_gc_node.appendChild(verbose_gc_total_collects_node)
            verbose_gc_total_collects_node.appendChild(self.doc.createTextNode(str(vgc.get_total_number_of_collects())))
        verbose_gc_list_node.setAttribute("total_collects_in_time_limits", str(total_collects_in_time_limits))

        if len(self.har_files) > 0:
            har_files_node = self.doc.createElement("har_files")
            doc_node.appendChild(har_files_node)
            for har in self.har_files:
                har_files_node.appendChild(har.get_xml(self.doc))

        system_info_node = self.doc.createElement("system_info")
        doc_node.appendChild(system_info_node)

        tips_node = self.doc.createElement("tips")
        report_info_node.appendChild(tips_node)
        for tip in self.tips:
            tip_node = self.doc.createElement("tip")
            tips_node.appendChild(tip_node)
            tip_node.appendChild(self.doc.createTextNode(tip))

        user_args_list_node = self.doc.createElement("user_args_list")
        system_info_node.appendChild(user_args_list_node)
        for arg in self.user_args:
            arg_node = self.doc.createElement("user_arg")
            user_args_list_node.appendChild(arg_node)
            arg_node.appendChild(self.doc.createTextNode(arg))

        number_of_cpus_node = self.doc.createElement("number_of_cpus")
        system_info_node.appendChild(number_of_cpus_node)
        number_of_cpus_node.appendChild(self.doc.createTextNode(self.number_of_cpus))

        xmx_node = self.doc.createElement("xmx")
        system_info_node.appendChild(xmx_node)
        xmx_node.appendChild(self.doc.createTextNode(self.xmx))

        xms_node = self.doc.createElement("xms")
        system_info_node.appendChild(xms_node)
        xms_node.appendChild(self.doc.createTextNode(self.xms))

        xmn_node = self.doc.createElement("xmn")
        system_info_node.appendChild(xmn_node)
        xmn_node.appendChild(self.doc.createTextNode(self.xmn))

        verbose_gc_node = self.doc.createElement("verbose_gc")
        system_info_node.appendChild(verbose_gc_node)
        verbose_gc_node.appendChild(self.doc.createTextNode(str(self.verbose_gc)))

        gc_policy_node = self.doc.createElement("gc_policy")
        system_info_node.appendChild(gc_policy_node)
        gc_policy_node.appendChild(self.doc.createTextNode(self.gc_policy))

        compressed_refs_node = self.doc.createElement("compressed_refs")
        system_info_node.appendChild(compressed_refs_node)
        compressed_refs_node.appendChild(self.doc.createTextNode(str(self.compressed_refs)))

        architecture_node = self.doc.createElement("architecture")
        system_info_node.appendChild(architecture_node)
        architecture_node.appendChild(self.doc.createTextNode(self.architecture))

        java_version_node = self.doc.createElement("java_version")
        system_info_node.appendChild(java_version_node)
        java_version_node.appendChild(self.doc.createTextNode(self.java_version))

        os_level_node = self.doc.createElement("os_level")
        system_info_node.appendChild(os_level_node)
        os_level_node.appendChild(self.doc.createTextNode(self.os_level))

        doc_node.appendChild(self.get_blockers_xml())
        doc_node.appendChild(self.threads.get_xml(self.doc))
        doc_node.appendChild(self.stacks.get_xml(self.doc))
        doc_node.appendChild(self.gc_parser.get_xml(self.doc))

        self.doc.appendChild(doc_node)

        stream = open(output_file, 'w')
        self.doc.writexml(stream, indent="  ", addindent="  ", newl='\n', encoding="utf-8")
        stream.close()
        self.doc.unlink()
        self.report_xml_file = output_file

        logging.info("Finished generating report xml")

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def get_javacore_set_in_xml(self):
        """
        Returns the JavaCore set in the XML report file.

        Parameters:
        self (JavacoreSet): The instance of the javacore_set class.

        Returns:
        str: The JavaCore set in the XML format.
        """
        file = None
        try:
            file = open(self.report_xml_file, "r")
            content = file.read()
            return content
        finally:
            file.close()

    @staticmethod
    def validate_uncontrolled_data_used_in_path(path_params):
        fullpath = os.path.normpath(os.path.join(path_params))
        if not fullpath.startswith(path_params[0]):
            raise Exception("Security exception: Uncontrolled data used in path expression")
        return fullpath

    @staticmethod
    def __create_index_html(input_dir, output_dir):

        # Copy index.xml and report.xsl to temp - for index.html we don't need to generate anything. Copying is enough.
        # index_xml = validate_uncontrolled_data_used_in_path([output_dir, "data", "xml", "index.xml"])
        index_xml = os.path.normpath(str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "index.xml"))
        shutil.copy2(index_xml, input_dir)

        report_xsl = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "report.xsl"))
        shutil.copy2(report_xsl, input_dir)

        xslt_doc = etree.parse(input_dir + "/report.xsl")
        xslt_transformer = etree.XSLT(xslt_doc)

        parser = etree.XMLParser(resolve_entities=True)
        source_doc = etree.parse(input_dir + "/index.xml", parser)
        output_doc = xslt_transformer(source_doc)

        output_html_file = output_dir + "/index.html"
        logging.info("Generating file " + output_html_file)
        output_doc.write(output_html_file, pretty_print=True)

    @staticmethod
    def generate_htmls_from_xmls_xsls(report_xml_file, data_input_dir, output_dir):

        logging.info(f"Starting generating htmls from data from {data_input_dir}")

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        shutil.copy2(report_xml_file, data_input_dir)

        # https://docs.python.org/3.8/library/multiprocessing.html
        threads_no = JavacoreSet.get_number_of_parallel_threads()
        logging.info(f"Using {threads_no} threads to generate html files")

        list_files = os.listdir(data_input_dir)
        progress_bar = tqdm(desc="Generating html files", unit=' files')

        # Generating list of tuples. This is required attribute for p.map function executed few lines below.
        generate_html_from_xml_xsl_files_params = []
        for file in list_files:
            generate_html_from_xml_xsl_files_params.append((file, data_input_dir, output_dir, progress_bar))

        with Pool(threads_no) as p:
            p.map(JavacoreSet.generate_html_from_xml_xsl_files, generate_html_from_xml_xsl_files_params)

        progress_bar.close()
        logging.info(f"Generated html files in {output_dir}")

    # Run with the same number of threads as you have processes but leave one thread for something else.
    @staticmethod
    def get_number_of_parallel_threads():
        return max(1, os.cpu_count() - 1)

    @staticmethod
    def generate_html_from_xml_xsl_files(args):

        collection_file, collection_input_dir, output_dir, progress_bar = args

        if not collection_file.endswith(".xsl"): return

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

        progress_bar.update(1)

    @staticmethod
    def create_xml_xsl_for_collection(tmp_dir, xml_xsls_prefix_path, collection, output_file_prefix):
        logging.info("Creating xmls and xsls in " + tmp_dir)
        os.mkdir(tmp_dir)
        extensions = [".xsl", ".xml"]
        for extension in extensions:
            file_content = Path(xml_xsls_prefix_path + extension).read_text()
            for element in tqdm(collection, desc="Creating xml/xsl files", unit=" files"):
                element_id = element.get_id()
                filename = output_file_prefix + "_" + str(element_id) + extension
                if filename.startswith("_"):
                    filename = filename[1:]
                file = os.path.join(tmp_dir, filename)
                logging.debug("Writing file " + file)
                f = open(file, "w")
                f.write(file_content.format(id=element_id))
                f.close()

    @staticmethod
    def parse_mem_arg(line):
        line = line.split()[-1]  # avoid matching the '2' in tag name 2CIUSERARG
        tokens = re.findall("\d+[KkMmGg]?$", line)
        if len(tokens) != 1: return UNKNOWN
        return tokens[0]

    def parse_xmx(self, line):
        self.xmx = self.parse_mem_arg(line)

    def parse_xms(self, line):
        self.xms = self.parse_mem_arg(line)

    def parse_xmn(self, line):
        self.xmn = self.parse_mem_arg(line)

    def parse_gc_policy(self, line):
        self.gc_policy = line[line.rfind(":") + 1:].strip()

    def parse_compressed_refs(self, line):
        if line.__contains__(COMPRESSED_REFS): self.compressed_refs = True
        if line.__contains__(NO_COMPRESSED_REFS): self.compressed_refs = False

    def parse_verbose_gc(self, line):
        if line.__contains__(VERBOSE_GC): self.verbose_gc = True

    def add_user_arg(self, line):
        # 2CIUSERARG               -Djava.lang.stringBuffer.growAggressively=false
        # Search for - and trim everything before
        # (from https://stackoverflow.com/questions/30945784/how-to-remove-all-characters-before-a-specific
        # -character-in-python)
        arg = line[line.find('-'):].rstrip()
        logging.debug("User arg: " + arg)
        self.user_args.append(arg)

    def parse_user_args(self, line):
        self.add_user_arg(line)
        if line.__contains__(XMX): self.parse_xmx(line)
        if line.__contains__(XMS): self.parse_xms(line)
        if line.__contains__(XMN): self.parse_xmn(line)
        if line.__contains__(GC_POLICY): self.parse_gc_policy(line)
        if line.__contains__(COMPRESSED_REFS) or line.__contains__(NO_COMPRESSED_REFS): self.parse_compressed_refs(line)
        if line.__contains__(VERBOSE_GC): self.parse_verbose_gc(line)

    def blocked_collection(self, blocker):
        """
        Returns the Snapshot collection for given blocker.

        @param blocker: The thread for which we want to get a blocker.
        @return: SnapshotCollection object containing all thread snapshots of given thread or None if there is no such
            collection.
        """
        if blocker:
            for snapshot_collection in self.blocked_snapshots:
                if snapshot_collection.size() > 0:
                    if snapshot_collection.get(0).get_blocker().thread_id == blocker.thread_id:
                        return snapshot_collection
        return None

    # TODO: IMO thread snapshot should contain the information about list of blocking threads and java thread should
    # return the list of blocking threads.
    def __generate_blocked_snapshots_list(self):
        for javacore in self.javacores:
            for snapshot in javacore.snapshots:
                blocker = snapshot.get_blocker()
                if blocker:
                    blocked = self.blocked_collection(blocker)
                    if not blocked:
                        blocked = SnapshotCollection()
                        self.blocked_snapshots.append(blocked)
                    blocked.add(snapshot)
                    blocker.blocking.add(snapshot)
        self.blocked_snapshots.sort(reverse=True, key=lambda collection: len(collection.get_threads_set()))

    def print_blockers(self):
        for blocked in self.blocked_snapshots:
            logging.debug(blocked.get(0).blocker.name + ": " + str(blocked.size()))

    def generate_tips(self):
        for tip in tips.TIPS_LIST:
            tip_class = getattr(tips, tip)
            self.tips.extend(tip_class.generate(self))
