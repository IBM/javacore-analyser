#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import fnmatch
import logging
import os
from typing import Any, Optional

from tqdm import tqdm

from javacore_analyser import tips
from javacore_analyser.ai.performance_recommendations_prompter import PerformanceRecommendationsPrompter
from javacore_analyser.code_snapshot_collection import CodeSnapshotCollection
from javacore_analyser.constants import MIN_JAVACORE_SIZE
from javacore_analyser.exceptions import InvalidLLMMethodError
from javacore_analyser.har_file import HarFile
from javacore_analyser.java_thread import Thread
from javacore_analyser.javacore import Javacore
from javacore_analyser.jvm_info import JvmInfo
from javacore_analyser.plugin_manager import PluginManager
from javacore_analyser.properties import Properties
from javacore_analyser.snapshot_collection import SnapshotCollection
from javacore_analyser.snapshot_collection_collection import SnapshotCollectionCollection
from javacore_analyser.verbose_gc import VerboseGcParser
from javacore_analyser.ml.classify_javacore_inference import JavacoreClassifier


class JavacoreSet:
    """represents a single javacore collection
    consisting of one or more javacore files"""

    def __init__(self, path):
        self.path = path  # path of the folder where the javacores are located
        self.files: list[str] = []
        self.javacores: list[Any] = []
        self.excluded_javacores: list[Any] = []
        self.verbose_gc_files: list[str] = []
        self.threads = SnapshotCollectionCollection(Thread)
        self.stacks = SnapshotCollectionCollection(CodeSnapshotCollection)
        self._jvm_info: Optional[JvmInfo] = None

        #self.ai_overview = ""
        self.ai_tips: str = ""

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
        self.ml_classifier: Any = None
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

    def populate_snapshot_collections(self):
        for javacore in self.javacores:
            javacore.print_javacore()
            for s in tqdm(javacore.snapshots, desc="Populating snapshot collection", unit=" javacore"):
                self.threads.add_snapshot(s)
                self.stacks.add_snapshot(s)
    
    def classify_threads(self):
        """Classify all thread snapshots upfront in a single batch model.predict() call.

        Collecting every ThreadSnapshot into one numpy matrix and calling model.predict()
        once eliminates the per-call XGBoost overhead that caused ~18 ms × N slowness.
        After the batch run each Thread.classify() simply aggregates already-stored labels.
        """
        logging.info("Computing thread classifications")

        # Collect every snapshot across all Thread objects into a flat list
        thread_list = list(self.threads)
        if not thread_list:
            logging.info("No threads to classify")
            return

        # Flatten: one list of every ThreadSnapshot across all Thread objects
        all_snapshots = [s for thread in thread_list for s in thread.thread_snapshots]
        if not all_snapshots:
            logging.info("No snapshots to classify")
            return

        # One model.predict() call for the entire dataset
        labels = self.ml_classifier.predict_snapshots_batch(all_snapshots)

        # Pair each snapshot with its predicted label (same order as the batch input)
        # and store it so snapshot.get_classification() returns immediately without re-predicting
        for snapshot, label in zip(all_snapshots, labels):
            snapshot._ml_classification = label

        # Thread-level aggregation (counts labels per thread, no more predict calls)
        for thread in tqdm(thread_list, desc="Classifying threads", unit=" thread"):
            thread.classify()

        logging.info("Thread classification complete")

    @property
    def jvm_info(self) -> Optional[JvmInfo]:
        """Return the :class:`JvmInfo` from the first parsed javacore, or from verbose gc if no javacores, or ``None``."""
        if len(self.javacores) > 0:
            return self.javacores[0].jvm_info
        return self._jvm_info

    def print_java_settings(self):
        jvm_info = self.jvm_info
        if jvm_info is None:
            return
        logging.debug("number of CPUs: {}".format(jvm_info.number_of_cpus))
        logging.debug("Xmx: {}".format(jvm_info.xmx))
        logging.debug("Xms: {}".format(jvm_info.xms))
        logging.debug("Xmn: {}".format(jvm_info.xmn))
        logging.debug("Verbose GC: {}".format(jvm_info.verbose_gc))
        logging.debug("GC policy: {}".format(jvm_info.gc_policy))
        logging.debug("Compressed refs: {}".format(jvm_info.compressed_refs))
        logging.debug("Architecture: {}".format(jvm_info.architecture))
        logging.debug("Java version: {}".format(jvm_info.java_version))
        logging.debug("OS Level: {}".format(jvm_info.os_level))
        logging.debug("JVM Startup time: {}".format(jvm_info.jvm_start_time))
        logging.debug("Command line: {}".format(jvm_info.cmd_line))

    @staticmethod
    def create(path):
        jset = JavacoreSet(path)
        jset.populate_files_list()
        
        # Process javacores if available
        if len(jset.files) > 0:
            jset.data_types.add('javacores')
            first_javacore = jset.get_one_javacore()
            jset.parse_javacores()
            jset.sort_snapshots()
            jset.__generate_blocked_snapshots_list()
        else:
            logging.info("No javacore files found. Continuing with other data types.")
        
        # Process verbose GC files if available
        if len(jset.gc_parser.get_file_paths()) > 0:
            jset.data_types.add('verbosegc')
            jset.parse_verbose_gc_files()
            if len(jset.javacores) == 0:
                first_vgc_path = jset.gc_parser.get_file_paths()[0]
                jset._jvm_info = JvmInfo()
                jset._jvm_info.parse_verbose_gc(first_vgc_path)
        
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
        self.gc_parser.get_file_paths().sort()

    def parse_javacores(self):
        """ creates a Javacore object for each javacore...txt file in the given path """
        for filename in tqdm(self.files, "Parsing javacore files", unit=" file"):
            javacore = Javacore.create(filename, self)
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

    def print_thread_states(self):
        for thread in self.threads:
            logging.debug("max running states:" + str(thread.get_continuous_running_states()))
            logging.debug(thread.name + "(id: " + str(thread.id) + "; hash: " + thread.get_hash() + ") " +
                          "states: " + thread.get_snapshot_states())

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
