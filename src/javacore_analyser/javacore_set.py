#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import fnmatch
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing.dummy import Pool  # Keep for HTML generation compatibility
from pathlib import Path
from typing import Optional
from xml.dom.minidom import parseString

import importlib_resources
from lxml import etree
from lxml.etree import XMLSyntaxError
from tqdm import tqdm

from javacore_analyser import tips
from javacore_analyser.ai.performance_recommendations_prompter import PerformanceRecommendationsPrompter
from javacore_analyser.code_snapshot_collection import CodeSnapshotCollection
from javacore_analyser.constants import *
from javacore_analyser.exceptions import InvalidLLMMethodError
from javacore_analyser.har_file import HarFile
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.plugin_manager import PluginManager
from javacore_analyser.properties import Properties
from javacore_analyser.snapshot_collection import SnapshotCollection
from javacore_analyser.snapshot_collection_collection import SnapshotCollectionCollection
from javacore_analyser.verbose_gc import VerboseGcParser
from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier


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
        # Remove file:// prefix if present to get the actual file path
        if url.startswith('file://'):
            url = url[7:]  # Remove 'file://' prefix
        
        # If the file exists on the file system, resolve it
        if os.path.exists(url):
            return self.resolve_filename(url, context)

        else: 
            return self.resolve_filename(self.temp_path + os.sep + url, context)


        # Return None if file not found (lxml will handle the error)
        return None


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
        self.jvm_start_time = ""
        self.cmd_line = ""
        self.user_args = []
        # end of static information
        self.files = []
        self.javacores = []
        self.excluded_javacores = []
        self.verbose_gc_files = []
        self.threads = SnapshotCollectionCollection(Thread)
        self.stacks = SnapshotCollectionCollection(CodeSnapshotCollection)
        self.report_xml_file = None

        #self.ai_overview = ""
        self.ai_tips = ""

        self.doc = None
        
        # Track what types of data files are present
        self.data_types = set()

        '''
        List where each element is SnapshotCollection containing all threads blocked by given thread.
        You can check the blocking thread by looking at snapshotCollection.get(0).get_blocker()
        '''
        # TODO this list is redundant with the data stored in Thread Snapshot. Should be removed in the future.
        self.blocked_snapshots = []
        self.tips = []
        self.gc_parser = VerboseGcParser()
        self.har_files = []
        
        # Plugin system attributes
        self.plugin_data = {}  # Store plugin results
        self.plugin_manager = None  # Will be set if plugins enabled

        # machine learning
        self.ml_classifier = None
        self.use_ml = Properties.get_instance().get_property("use_ml", False)
        if self.use_ml:
            self.ml_classifier = JavacoreClassifier()     

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
        if jset.use_ml:
            jset.classify_threads()
        jset.sort_snapshots()
        # jset.find_top_blockers()
        jset.print_blockers()
        jset.print_thread_states()
        jset.generate_tips()
        if Properties.get_instance().get_property("use_ai", False):
            jset.add_ai()
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
        self.__create_index_html(temp_dir_name, output_dir, self.plugin_data)
        self.__generate_htmls_for_threads(output_dir, temp_dir_name)
        self.__generate_htmls_for_javacores(output_dir, temp_dir_name)

    @staticmethod
    def __generate_placeholder_htmls(placeholder_file, directory, collection, file_prefix):
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
    
    def classify_threads(self):
        """Compute classifications for all threads upfront to improve report generation performance."""
        logging.info("Computing thread classifications")
        num_workers = self.get_number_of_parallel_threads()
        logging.debug(f"Using {num_workers} parallel threads for classification")
        
        # Convert to list for parallel processing
        thread_list = list(self.threads)
        
        if not thread_list:
            logging.info("No threads to classify")
            return
        
        # Classify threads in parallel using Pool
        with Pool(num_workers) as pool:
            # Use tqdm with imap for progress tracking
            list(tqdm(
                pool.imap(lambda t: t.classify(), thread_list),
                total=len(thread_list),
                desc="Classifying threads",
                unit=" thread"
            ))
        
        logging.info("Thread classification complete")

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
        logging.debug("JVM Startup time: {}".format(self.jvm_start_time))
        logging.debug("Command line: {}".format(self.cmd_line))

    @staticmethod
    def create(path):
        jset = JavacoreSet(path)
        jset.populate_files_list()
        
        # Process javacores if available
        if len(jset.files) > 0:
            jset.data_types.add('javacores')
            first_javacore = jset.get_one_javacore()
            jset.parse_common_data(first_javacore)
            jset.parse_javacores()
            jset.sort_snapshots()
            jset.__generate_blocked_snapshots_list()
            jset.classify_threads()
        else:
            logging.info("No javacore files found. Continuing with other data types.")
        
        # Process verbose GC files if available
        if len(jset.gc_parser.get_file_paths()) > 0:
            jset.data_types.add('verbosegc')
            jset.parse_verbose_gc_files()
        
        # Track HAR files if available
        if len(jset.har_files) > 0:
            jset.data_types.add('har')
        
        # Process plugins if enabled
        if Properties.get_instance().get_property("enable_plugins", False):
            jset._process_plugins()
        
        # Ensure at least one data type is present
        if len(jset.data_types) == 0:
            raise RuntimeError("No valid data files found (javacores, HAR files, or verbose GC files). Exiting with error 13")
        
        return jset

    def _process_plugins(self):
        """
        Process plugin data sources if plugins are enabled.
        
        This method:
        1. Creates a PluginManager instance
        2. Discovers and loads available plugins
        3. Finds files matching each plugin's patterns
        4. Processes files with each plugin
        5. Stores results in self.plugin_data
        
        All errors are handled gracefully with logging to ensure plugin failures
        don't break the main analysis workflow.
        """
        try:
            logging.info("Plugin processing enabled, initializing plugin manager")
            self.plugin_manager = PluginManager()
            
            # Discover and load plugins
            self.plugin_manager.discover_plugins()
            plugins = self.plugin_manager.get_all_plugins()
            
            if not plugins:
                logging.info("No plugins found in plugin directory")
                return
            
            logging.info(f"Found {len(plugins)} plugin(s), scanning for matching files")
            
            # Find files for each plugin
            plugin_files = self.plugin_manager.find_files_for_plugins(self.path)
            
            if not plugin_files:
                logging.info("No files found matching any plugin patterns")
                return
            
            # Process files with each plugin
            for plugin, files in plugin_files.items():
                try:
                    logging.info(f"Processing {len(files)} file(s) with plugin: {plugin.get_display_name()}")
                    data = plugin.process_files(files)
                    self.plugin_data[plugin.get_plugin_name()] = {
                        'plugin': plugin,
                        'data': data,
                        'files': files
                    }
                    logging.info(f"Successfully processed files with plugin: {plugin.get_display_name()}")
                except Exception as e:
                    logging.error(f"Error processing files with plugin {plugin.get_display_name()}: {e}")
                    
        except Exception as e:
            logging.error(f"Error during plugin processing: {e}")

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
                    full_path = os.path.join(dirpath, file)
                    file_size = os.path.getsize(full_path)
                    if file_size > MIN_JAVACORE_SIZE:
                        self.files.append(full_path)
                        logging.info("Javacore file found: " + file)
                    else:
                        logging.info(f"Excluding javacore file {file} with size {file_size} bytes")
                        self.excluded_javacores.append({"file": file,
                                                        "reason": tips.ExcludedJavacoresTip.SMALL_SIZE_JAVACORES.format(
                                                            file, file_size)})
                if fnmatch.fnmatch(file, '*verbosegc*'):
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
                elif line.startswith(STARTTIME):
                    self.jvm_start_time = line[line.find(":") + 1:].strip()
                    continue
                elif line.startswith(CMD_LINE):
                    self.cmd_line = line[len(CMD_LINE) + 1:].strip()
                    continue
        except Exception as ex:
            logging.exception(ex)
            if file is not None:
                logging.error(f'Error during processing file: {file.name} \n'
                              f'line number: {i} \n'
                              f'line: {curr_line}\n'
                              f'Check the exception below what happened')
        finally:
            if file is not None:
                file.close()

    def parse_javacores(self):
        """ creates a Javacore object for each javacore...txt file in the given path """
        for filename in tqdm(self.files, "Parsing javacore files", unit=" file"):
            javacore = Javacore()
            javacore.create(filename, self)
            self.javacores.append(javacore)
        self.javacores.sort(key=lambda x: x.timestamp)

    def parse_verbose_gc_files(self):
        if len(self.javacores) > 0:
            start = self.javacores[0].datetime
            stop = self.javacores[-1].datetime
            self.gc_parser.parse_files(start, stop)
        else:
            # Parse all GC files without time constraints
            self.gc_parser.parse_files()

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
        
        # Add data types information
        data_types_node = self.doc.createElement("data_types")
        doc_node.appendChild(data_types_node)
        for data_type in self.data_types:
            type_node = self.doc.createElement("type")
            type_node.appendChild(self.doc.createTextNode(data_type))
            data_types_node.appendChild(type_node)

        javacore_count_node = self.doc.createElement("javacore_count")
        javacore_count_node.appendChild(self.doc.createTextNode(str(len(self.javacores))))
        doc_node.appendChild(javacore_count_node)
        report_info_node = self.doc.createElement("report_info")
        doc_node.appendChild(report_info_node)
        generation_time_node = self.doc.createElement("generation_time")
        report_info_node.appendChild(generation_time_node)
        generation_time_node.appendChild(self.doc.createTextNode(str(datetime.now().strftime(DATE_FORMAT))))
        doc_node.setAttribute("use_ml", str(self.use_ml))

        # Only include javacore-specific data if javacores are present
        if 'javacores' in self.data_types and len(self.javacores) > 0:
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

        # Only include system info if javacores are present
        if 'javacores' in self.data_types:
            system_info_node = self.doc.createElement("system_info")
            doc_node.appendChild(system_info_node)
        else:
            system_info_node = None

        tips_node = self.doc.createElement("tips")
        report_info_node.appendChild(tips_node)
        for tip in self.tips:
            tip_node = self.doc.createElement("tip")
            tips_node.appendChild(tip_node)
            tip_node.appendChild(self.doc.createTextNode(tip))
        tips_node.setAttribute("ai_tips", self.ai_tips)

        # Only add system info details if javacores are present
        if system_info_node is not None:
            user_args_list_node = self.doc.createElement("user_args_list")
            #system_info_node.setAttribute("ai_overview", self.ai_overview)
            system_info_node.appendChild(user_args_list_node)
            for arg in self.user_args:
                arg_node = self.doc.createElement("user_arg")
                user_args_list_node.appendChild(arg_node)
                arg_node.appendChild(self.doc.createTextNode(arg))

            number_of_cpus_node = self.doc.createElement("number_of_cpus")
            system_info_node.appendChild(number_of_cpus_node)
            number_of_cpus_node.appendChild(self.doc.createTextNode(self.number_of_cpus if self.number_of_cpus else ""))

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

            jvm_startup_time = self.doc.createElement("jvm_start_time")
            system_info_node.appendChild(jvm_startup_time)
            jvm_startup_time.appendChild(self.doc.createTextNode(self.jvm_start_time))

            cmd_line = self.doc.createElement("cmd_line")
            system_info_node.appendChild(cmd_line)
            cmd_line.appendChild(self.doc.createTextNode(self.cmd_line))

        # Only add javacore-dependent data if javacores are present
        if 'javacores' in self.data_types:
            doc_node.appendChild(self.get_blockers_xml())
            doc_node.appendChild(self.threads.get_xml(self.doc))
            doc_node.appendChild(self.stacks.get_xml(self.doc))
        
        doc_node.appendChild(self.gc_parser.get_xml(self.doc))
        
        # Add plugin data to XML if plugins were processed
        if self.plugin_data:
            try:
                logging.info("Adding plugin data to report XML")
                plugins_node = self.doc.createElement("plugins")
                doc_node.appendChild(plugins_node)
                
                for plugin_name, plugin_info in self.plugin_data.items():
                    try:
                        plugin = plugin_info['plugin']
                        data = plugin_info['data']
                        
                        logging.debug(f"Generating XML for plugin: {plugin.get_display_name()}")
                        plugin_xml = plugin.generate_xml(self.doc, data)
                        plugins_node.appendChild(plugin_xml)
                        logging.debug(f"Successfully added XML for plugin: {plugin.get_display_name()}")
                        
                    except Exception as e:
                        logging.error(f"Error generating XML for plugin {plugin_name}: {e}")
                        
                logging.info(f"Successfully added {len(self.plugin_data)} plugin(s) to report XML")
                
            except Exception as e:
                logging.error(f"Error adding plugin data to XML: {e}")

        self.doc.appendChild(doc_node)

        with open(output_file, 'w', encoding='utf-8') as stream:
            self.doc.writexml(stream, indent="  ", addindent="  ", newl='\n', encoding="utf-8")
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
    def generate_plugin_section_header(section_id: str, section_title: str, description: str) -> str:
        """
        Generate standardized HTML header for plugin sections.
        
        This method creates a collapsible section header with documentation that follows
        the same pattern used throughout the javacore-analyser report. It provides a
        consistent user experience across all plugin sections.
        
        The generated HTML includes:
        - A collapsible section header (h3) with expand/collapse functionality
        - A nested documentation section explaining what the section contains
        - Proper CSS classes for styling consistency
        
        Args:
            section_id: Unique identifier for the section (used in HTML IDs and JavaScript)
            section_title: Human-readable title displayed in the section header
            description: HTML content describing what the section shows (can include lists, paragraphs, etc.)
        
        Returns:
            HTML string containing the section header and documentation wrapper
            
        Example:
            >>> header = JavacoreSet.generate_plugin_section_header(
            ...     "liberty_logs",
            ...     "Liberty System Out",
            ...     "This section shows analysis of Liberty log files."
            ... )
        """
        from html import escape
        
        # Escape the title for safe HTML output
        escaped_title = escape(section_title)
        
        # Generate the section header HTML
        # Note: description is expected to be pre-formatted HTML, so it's not escaped
        header_html = f'''<h3><a id="toggle_{section_id}" href="javascript:expand_it({section_id},toggle_{section_id})" class="expandit">{escaped_title}</a></h3>
<div id="{section_id}" style="display:none;">
    <a id="toggle{section_id}doc" href="javascript:expand_it({section_id}doc,toggle{section_id}doc)" class="expandit">
        What does this section tell me?</a>
    <div id="{section_id}doc" style="display:none;">
        {description}
    </div>

'''
        return header_html

    @staticmethod
    def __generate_plugins_xsl(temp_dir: str, plugin_data: dict) -> Optional[str]:
        """
        Generate plugins.xsl file dynamically from loaded plugin HTML content.
        
        This method creates a plugins.xsl file that wraps HTML content generated by plugins
        into a single XSL template named "plugins". The generated file is used by report.xsl
        to include plugin-specific content in the final HTML report.
        
        The method handles:
        - Calling generate_html() on each plugin to get HTML content
        - Wrapping HTML in CDATA sections with disable-output-escaping for proper injection
        - Combining all plugin HTML into a single plugins.xsl file
        - Creating a fallback empty template if no plugins are loaded or if errors occur
        - Comprehensive error handling and logging for HTML generation failures
        
        :param temp_dir: Temporary directory where XSL files are stored
        :type temp_dir: str
        :param plugin_data: Dictionary of loaded plugin data, where keys are plugin names and values
                           are dictionaries containing 'plugin' instances and 'data'
        :type plugin_data: dict
        :return: Path to generated plugins.xsl file, or None if generation fails
        :rtype: Optional[str]
        """
        plugins_xsl_path = os.path.join(temp_dir, "plugins.xsl")
        
        try:
            # Start building the plugins.xsl content
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
            
            # Add plugin sections if plugins are loaded
            if plugin_data:
                logging.info("Generating plugins.xsl with plugin HTML content")
                
                for plugin_name, plugin_info in plugin_data.items():
                    try:
                        plugin = plugin_info['plugin']
                        data = plugin_info.get('data', {})
                        
                        # Call generate_html() to get HTML content from the plugin
                        html_content = plugin.generate_html(data)
                        
                        if html_content:
                            # Generate section header with plugin description
                            section_id = plugin_name.replace('_', '')
                            section_header = JavacoreSet.generate_plugin_section_header(
                                section_id=section_id,
                                section_title=plugin.get_display_name(),
                                description=plugin.get_description()
                            )
                            
                            # Combine header with plugin content and close the section div
                            full_html = section_header + html_content + '\n</div>\n'
                            
                            # Wrap HTML content in CDATA with disable-output-escaping
                            # This allows the HTML to be injected directly into the report
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
                        # Add error message to report for debugging
                        plugins_xsl_content += f'''
        <!-- Plugin: {plugin_name} - Error generating HTML -->
        <xsl:text disable-output-escaping="yes"><![CDATA[
        <div class="error_row" style="padding: 10px; margin: 10px 0;">
            <strong>Error in plugin {plugin_name}:</strong> {str(e).replace('<', '<').replace('>', '>')}
        </div>
        ]]></xsl:text>

'''
            else:
                # No plugins loaded, create empty template
                plugins_xsl_content += "        <!-- No plugins loaded -->\n"
            
            # Close the template and stylesheet
            plugins_xsl_content += '''    </xsl:template>

</xsl:stylesheet>

<!-- Made with Bob -->
'''
            
            # Write plugins.xsl file
            with open(plugins_xsl_path, 'w', encoding='utf-8') as f:
                f.write(plugins_xsl_content)
            
            logging.info(f"Generated plugins.xsl at {plugins_xsl_path}")
            return plugins_xsl_path
            
        except Exception as e:
            logging.error(f"Error generating plugins.xsl: {e}")
            # Create empty plugins.xsl to prevent XSL errors
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


    @staticmethod
    def __create_index_html(input_dir, output_dir, plugin_data=None):

        # Copy index.xml and report.xsl to temp - for index.html we don't need to generate anything. Copying is enough.
        # index_xml = validate_uncontrolled_data_used_in_path([output_dir, "data", "xml", "index.xml"])
        index_xml = os.path.normpath(str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "index.xml"))
        shutil.copy2(index_xml, input_dir)

        report_xsl = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "report.xsl"))
        shutil.copy2(report_xsl, input_dir)

        # Copy sections directory containing modular XSL files
        # The report.xsl file uses <xsl:include> to reference these section files,
        # enabling a plugin architecture where sections can be added/removed independently
        sections_dir = os.path.normpath(
            str(importlib_resources.files("javacore_analyser") / "data" / "xml" / "sections"))
        sections_dest = os.path.join(input_dir, "sections")
        logging.debug(f"Sections source dir: {sections_dir}")
        logging.debug(f"Sections dest dir: {sections_dest}")
        logging.debug(f"Sections dir exists: {os.path.exists(sections_dir)}")
        if os.path.exists(sections_dir):
            shutil.copytree(sections_dir, sections_dest)
            logging.info(f"Copied sections directory to {sections_dest}")
            # List files in sections directory for debugging
            if os.path.exists(sections_dest):
                section_files = os.listdir(sections_dest)
                logging.info(f"Section files copied: {section_files}")
        else:
            logging.warning(f"Sections directory not found at {sections_dir}")

        # Generate plugins.xsl file dynamically
        JavacoreSet.__generate_plugins_xsl(input_dir, plugin_data)

        # Prepare XSLT file path and URI for processing
        # The file:// URI scheme is required by lxml's XSLT processor to properly
        # resolve relative paths in <xsl:include> directives
        report_xsl_path = os.path.join(input_dir, "report.xsl")
        report_xsl_uri = "file://" + os.path.abspath(report_xsl_path)
        
        logging.info(f"Report XSL path: {report_xsl_path}")
        logging.info(f"Report XSL URI: {report_xsl_uri}")
        
        # Create XML parser with custom FileResolver to handle xsl:include directives
        # The FileResolver intercepts URI resolution during XSLT parsing and converts
        # file:// URIs to actual file system paths, allowing lxml to locate and include
        # the modular section files referenced in report.xsl
        xslt_parser = etree.XMLParser()

        xslt_parser.resolvers.add(FileResolver(temp_path=input_dir))


        # Parse the XSLT document with the custom resolver
        xslt_doc = etree.parse(report_xsl_path, xslt_parser)
        # Set the base URL for the XSLT document to enable proper relative path resolution
        xslt_doc.docinfo.URL = report_xsl_uri
        logging.debug(f"XSLT doc base URL set to: {xslt_doc.docinfo.URL}")
        # Create the XSLT transformer from the parsed document
        xslt_transformer = etree.XSLT(xslt_doc)

        # Create separate parser for the XML source document that will be transformed
        # This parser is configured to resolve XML entities during parsing
        source_parser = etree.XMLParser(resolve_entities=True)
        source_doc = etree.parse(input_dir + "/index.xml", source_parser)
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
        progress_bar = tqdm(desc="Generating html files", unit=' file')

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

    def add_ai(self):
        """
        Initialize LLM backend and generate AI-powered performance recommendations.

        Supports 'huggingface' (local) or 'ollama' (server-based) methods configured via llm_method property.
        Stores HTML-formatted recommendations in self.ai_tips.

        Raises:
            ImportError: If LLM dependencies are not installed.
            InvalidLLMMethodError: If llm_method is invalid.
        """
        llm_method: str = Properties.get_instance().get_property("llm_method")
        if llm_method.lower() == "huggingface":
            try:
                from javacore_analyser.ai.huggingface_llm import HuggingFaceLLM
                ai = HuggingFaceLLM(self)
            except ImportError as e:
                raise ImportError(
                    "HuggingFace dependencies not installed. "
                    "Install with: pip install javacore_analyser[huggingface]"
                ) from e
        elif llm_method.lower() == "ollama":
            try:
                from javacore_analyser.ai.ollama_llm import OllamaLLM
                ai = OllamaLLM(self)
            except ImportError as e:
                raise ImportError(
                    "Ollama dependencies not installed. "
                    "Install with: pip install javacore_analyser[ollama]"
                ) from e
        elif llm_method.lower() == "watsonx":
            try:
                from javacore_analyser.ai.watsonx_llm import WatsonxLLM
                ai = WatsonxLLM(self)
            except ImportError as e:
                raise ImportError(
                    "WatsonX dependencies not installed. "
                    "Install with: pip install javacore_analyser[watsonx]"
                ) from e
        else:
            raise InvalidLLMMethodError(llm_method)
            
        self.ai_tips = ai.infuse_in_html(PerformanceRecommendationsPrompter(self))
