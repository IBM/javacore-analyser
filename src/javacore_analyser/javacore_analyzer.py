#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
import tempfile

from tqdm import tqdm

from javacore_analyser import tips
from javacore_analyser.ai.performance_recommendations_prompter import PerformanceRecommendationsPrompter
from javacore_analyser.blocking_analyzer import BlockingAnalyzer
from javacore_analyser.code_snapshot_collection import CodeSnapshotCollection
from javacore_analyser.constants import *
from javacore_analyser.exceptions import InvalidLLMMethodError
from javacore_analyser.file_discovery import FileDiscovery
from javacore_analyser.html_report_generator import HtmlReportGenerator, _create_xml_xsl_for_collection
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.plugin_coordinator import PluginCoordinator
from javacore_analyser.properties import Properties
from javacore_analyser.snapshot_collection_collection import SnapshotCollectionCollection
from javacore_analyser.verbose_gc import VerboseGcParser
from javacore_analyser.xml_report_generator import XmlReportGenerator
from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier


class JavacoreAnalyzer:
    """Core orchestrator for javacore analysis.

    Coordinates file discovery, javacore parsing, verbose GC parsing, HAR file handling,
    plugin execution, report generation, and AI integration.

    This class was previously named ``JavacoreSet``. A backward-compatible alias is
    provided in ``javacore_set.py``.
    """

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
        """Process Java core data and generate tips based on the analysis.

        Args:
            input_path (str): The path to the directory containing the javacore data.

        Returns:
            JavacoreAnalyzer: Instance containing the analysis results.
        """
        jset = JavacoreAnalyzer.create(input_path)
        jset.print_java_settings()
        jset.populate_snapshot_collections()
        if jset.use_ml:
            jset.classify_threads()
        jset.sort_snapshots()
        jset.print_blockers()
        jset.print_thread_states()
        jset.generate_tips()
        if Properties.get_instance().get_property("use_ai", False):
            jset.add_ai()
        return jset

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-8b-code-instruct
    def generate_report_files(self, output_dir):
        """Generate report files in HTML format.

        Args:
            output_dir (str): The directory where the generated report files will be saved.
        """
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_name = temp_dir.name
        logging.info("Created temp dir: " + temp_dir_name)
        XmlReportGenerator.create_report_xml(self, temp_dir_name + "/report.xml")
        placeholder_filename = os.path.join(output_dir, "data", "html", "processing_data.html")
        HtmlReportGenerator.generate_placeholder_htmls(
            placeholder_filename,
            os.path.join(output_dir, "threads"),
            self.threads, "thread")
        HtmlReportGenerator.generate_placeholder_htmls(
            placeholder_filename,
            os.path.join(output_dir, "javacores"),
            self.javacores, "")
        HtmlReportGenerator.create_index_html(temp_dir_name, output_dir, self.plugin_data)
        self.__generate_htmls_for_threads(output_dir, temp_dir_name)
        self.__generate_htmls_for_javacores(output_dir, temp_dir_name)

    def __generate_htmls_for_threads(self, output_dir, temp_dir_name):
        _create_xml_xsl_for_collection(os.path.join(temp_dir_name, "threads"),
                                       os.path.join(output_dir, "data", "xml", "threads"), "thread",
                                       self.threads,
                                       "thread")
        HtmlReportGenerator.generate_htmls_from_xmls_xsls(
            self.report_xml_file,
            os.path.join(temp_dir_name, "threads"),
            os.path.join(output_dir, "threads"))

    def __generate_htmls_for_javacores(self, output_dir, temp_dir_name):
        _create_xml_xsl_for_collection(os.path.join(temp_dir_name, "javacores"),
                                       os.path.join(output_dir, "data", "xml", "javacores"), "javacore",
                                       self.javacores,
                                       "")
        HtmlReportGenerator.generate_htmls_from_xmls_xsls(
            self.report_xml_file,
            os.path.join(temp_dir_name, "javacores"),
            os.path.join(output_dir, "javacores"))

    def populate_snapshot_collections(self):
        """Populate thread and stack snapshot collections from all parsed javacores."""
        for javacore in self.javacores:
            javacore.print_javacore()
            for s in tqdm(javacore.snapshots, desc="Populating snapshot collection", unit=" javacore"):
                self.threads.add_snapshot(s)
                self.stacks.add_snapshot(s)

    def classify_threads(self):
        """Classify all thread snapshots in a single batch model.predict() call.

        Collecting every ThreadSnapshot into one numpy matrix and calling model.predict()
        once eliminates the per-call XGBoost overhead that caused ~18 ms × N slowness.
        After the batch run each Thread.classify() simply aggregates already-stored labels.
        """
        logging.info("Computing thread classifications")

        thread_list = list(self.threads)
        if not thread_list:
            logging.info("No threads to classify")
            return

        all_snapshots = [s for thread in thread_list for s in thread.thread_snapshots]
        if not all_snapshots:
            logging.info("No snapshots to classify")
            return

        labels = self.ml_classifier.predict_snapshots_batch(all_snapshots)

        for snapshot, label in zip(all_snapshots, labels):
            snapshot._ml_classification = label

        for thread in tqdm(thread_list, desc="Classifying threads", unit=" thread"):
            thread.classify()

        logging.info("Thread classification complete")

    def print_java_settings(self):
        """Log JVM configuration settings at DEBUG level."""
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
        """Factory method: discover files, parse data, and return a ready JavacoreAnalyzer.

        Args:
            path (str): Path to the directory containing input files.

        Returns:
            JavacoreAnalyzer: Fully initialised instance.

        Raises:
            RuntimeError: If no valid data files (javacores, HAR, verbose GC) are found.
        """
        jset = JavacoreAnalyzer(path)
        _file_discovery = FileDiscovery()
        _file_discovery.populate_files_list(jset)

        # Process javacores if available
        if len(jset.files) > 0:
            jset.data_types.add('javacores')
            first_javacore = jset.get_one_javacore()
            _file_discovery.parse_common_data(jset, first_javacore)
            jset.parse_javacores()
            jset.sort_snapshots()
            BlockingAnalyzer.generate_blocked_snapshots_list(jset)
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
            PluginCoordinator.process_plugins(jset)

        # Ensure at least one data type is present
        if len(jset.data_types) == 0:
            raise RuntimeError(
                "No valid data files found (javacores, HAR files, or verbose GC files). Exiting with error 13"
            )

        return jset

    def get_one_javacore(self):
        """Return the first javacore file path in the collection.

        The objective is to get VM information like number of CPUs — it is assumed all
        javacores come from one collection, so this information will be the same in all
        files.
        """
        return self.files[0]

    def populate_files_list(self):
        """Populate self.files and related collections by walking self.path.

        Delegates to :class:`~javacore_analyser.file_discovery.FileDiscovery`.
        """
        FileDiscovery().populate_files_list(self)

    def parse_common_data(self, filename):
        """Extract information common to all javacores (CPUs, JVM settings, etc.).

        Delegates to :class:`~javacore_analyser.file_discovery.FileDiscovery`.

        Args:
            filename (str): Path (absolute or relative to self.path) of the javacore file.
        """
        FileDiscovery().parse_common_data(self, filename)

    def parse_javacores(self):
        """Create a Javacore object for each javacore file in self.files."""
        for filename in tqdm(self.files, "Parsing javacore files", unit=" file"):
            javacore = Javacore()
            javacore.create(filename, self)
            self.javacores.append(javacore)
        self.javacores.sort(key=lambda x: x.timestamp)

    def parse_verbose_gc_files(self):
        """Parse verbose GC files, optionally constrained by the javacore time range."""
        if len(self.javacores) > 0:
            start = self.javacores[0].datetime
            stop = self.javacores[-1].datetime
            self.gc_parser.parse_files(start, stop)
        else:
            # Parse all GC files without time constraints
            self.gc_parser.parse_files()

    def sort_snapshots(self):
        """Sort snapshots within every thread collection."""
        for thread in tqdm(self.threads, "Sorting snapshot data", unit=" snapshot"):
            thread.sort_snapshots()

    def get_blockers_xml(self):
        """Build and return the <blockers> XML node (requires self.doc to be initialised).

        Delegates to :class:`~javacore_analyser.xml_report_generator.XmlReportGenerator`.
        """
        return XmlReportGenerator.get_blockers_xml(self, self.doc)

    def print_thread_states(self):
        """Log thread state information at DEBUG level."""
        for thread in self.threads:
            logging.debug("max running states:" + str(thread.get_continuous_running_states()))
            logging.debug(thread.name + "(id: " + str(thread.id) + "; hash: " + thread.get_hash() + ") " +
                          "states: " + thread.get_snapshot_states())

    def get_javacore_set_in_xml(self):
        """Return the content of the XML report file as a string.

        Returns:
            str: The XML report content.
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
        """Raise an exception if the joined path escapes the first path component.

        Args:
            path_params: Sequence of path components passed to os.path.join.

        Returns:
            str: The normalised full path.

        Raises:
            Exception: If the resulting path escapes the base directory.
        """
        fullpath = os.path.normpath(os.path.join(path_params))
        if not fullpath.startswith(path_params[0]):
            raise Exception("Security exception: Uncontrolled data used in path expression")
        return fullpath

    @staticmethod
    def generate_plugin_section_header(section_id: str, section_title: str, description: str) -> str:
        """Generate a standardised HTML header for plugin sections.

        Delegates to :class:`~javacore_analyser.plugin_coordinator.PluginCoordinator`.
        """
        return PluginCoordinator.generate_plugin_section_header(section_id, section_title, description)

    def blocked_collection(self, blocker):
        """Return the SnapshotCollection for *blocker*, or None if not found.

        Delegates to :class:`~javacore_analyser.blocking_analyzer.BlockingAnalyzer`.

        Args:
            blocker: The blocking thread snapshot to look up.

        Returns:
            SnapshotCollection or None
        """
        return BlockingAnalyzer.blocked_collection(self.blocked_snapshots, blocker)

    def print_blockers(self):
        """Log debug information about blocking threads.

        Delegates to :class:`~javacore_analyser.blocking_analyzer.BlockingAnalyzer`.
        """
        BlockingAnalyzer.print_blockers(self)

    def generate_tips(self):
        """Generate analysis tips based on the collected data."""
        for tip in tips.TIPS_LIST:
            tip_class = getattr(tips, tip)
            self.tips.extend(tip_class.generate(self))

    def add_ai(self):
        """Initialise LLM backend and generate AI-powered performance recommendations.

        Supports 'huggingface' (local) or 'ollama' (server-based) methods configured via
        the ``llm_method`` property. Stores HTML-formatted recommendations in self.ai_tips.

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

    # -------------------------------------------------------------------------
    # Static helpers kept for backward compatibility
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_htmls_from_xmls_xsls(report_xml_file, data_input_dir, output_dir):
        """Delegate to :class:`~javacore_analyser.html_report_generator.HtmlReportGenerator`."""
        HtmlReportGenerator.generate_htmls_from_xmls_xsls(report_xml_file, data_input_dir, output_dir)

    @staticmethod
    def get_number_of_parallel_threads():
        """Delegate to :class:`~javacore_analyser.html_report_generator.HtmlReportGenerator`."""
        return HtmlReportGenerator.get_number_of_parallel_threads()

    @staticmethod
    def generate_html_from_xml_xsl_files(args):
        """Delegate to :class:`~javacore_analyser.html_report_generator.HtmlReportGenerator`."""
        HtmlReportGenerator.generate_html_from_xml_xsl_files(args)

    @staticmethod
    def create_xml_xsl_for_collection(tmp_dir, xml_xsls_prefix_path, collection, output_file_prefix):
        """Delegate to :class:`~javacore_analyser.html_report_generator.HtmlReportGenerator`."""
        HtmlReportGenerator.create_xml_xsl_for_collection(
            tmp_dir, xml_xsls_prefix_path, collection, output_file_prefix)

    @staticmethod
    def parse_mem_arg(line):
        """Delegate to :class:`~javacore_analyser.jvm_config_parser.JvmConfigParser`."""
        from javacore_analyser.jvm_config_parser import JvmConfigParser
        return JvmConfigParser.parse_mem_arg(line)

    # -------------------------------------------------------------------------
    # JVM config parsing helpers — kept as instance methods so that tests and
    # any existing callers that do ``obj.parse_xmx(line)`` still work and the
    # result is reflected in the object's own fields.
    # -------------------------------------------------------------------------

    def parse_xmx(self, line):
        """Parse Xmx value from *line* and store it in self.xmx."""
        self.xmx = self.parse_mem_arg(line)

    def parse_xms(self, line):
        """Parse Xms value from *line* and store it in self.xms."""
        self.xms = self.parse_mem_arg(line)

    def parse_xmn(self, line):
        """Parse Xmn value from *line* and store it in self.xmn."""
        self.xmn = self.parse_mem_arg(line)

    def parse_gc_policy(self, line):
        """Parse GC policy from *line* and store it in self.gc_policy."""
        self.gc_policy = line[line.rfind(":") + 1:].strip()

    def parse_compressed_refs(self, line):
        """Parse compressed refs flag from *line* and update self.compressed_refs."""
        if COMPRESSED_REFS in line:
            self.compressed_refs = True
        if NO_COMPRESSED_REFS in line:
            self.compressed_refs = False

    def parse_verbose_gc(self, line):
        """Set self.verbose_gc = True if *line* contains the verbose:gc flag."""
        if VERBOSE_GC in line:
            self.verbose_gc = True

    def add_user_arg(self, line):
        """Append the JVM user arg from *line* to self.user_args."""
        arg = line[line.find('-'):].rstrip()
        logging.debug("User arg: " + arg)
        self.user_args.append(arg)

    def parse_user_args(self, line):
        """Parse all JVM user-arg fields from *line* and update self attributes."""
        self.add_user_arg(line)
        if XMX in line:
            self.parse_xmx(line)
        if XMS in line:
            self.parse_xms(line)
        if XMN in line:
            self.parse_xmn(line)
        if GC_POLICY in line:
            self.parse_gc_policy(line)
        if COMPRESSED_REFS in line or NO_COMPRESSED_REFS in line:
            self.parse_compressed_refs(line)
        if VERBOSE_GC in line:
            self.parse_verbose_gc(line)
