#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Javacore Thread Function Classifier

This module provides a class-based interface for classifying the function of threads
in Java core dumps using a pre-trained XGBoost machine learning model.

Usage:
    from classify_javacore_inference import JavacoreClassifier
    
    # Initialize classifier (loads model once)
    classifier = JavacoreClassifier()
    
    # Make prediction
    result = classifier.predict(
        name = "WebContainer : 5",
        cpu_usage = 0.05,
        allocated_mem = 1024000,
        state = "R",
        blocking_threads = 0,
        stack_trace = "at java.lang.Thread.run(Thread.java:748)...",
        stack_trace_depth = 15
    )
    
    print(f"Predicted function: {result}")
"""

# from javacore_analyser.javacore_set import JavacoreSet # If I import this one the model loading crashes
import logging
import time
import numpy as np
from xgboost import XGBClassifier
import json
import re
from typing import Optional, Dict, List, Tuple, Union
from pathlib import Path
from javacore_analyser.thread_snapshot import ThreadSnapshot
from importlib.resources import files


class JavacoreClassifier:
    """
    A classifier for predicting thread functions in Java core dumps.
    
    This class loads a pre-trained XGBoost model and provides methods to classify
    threads based on their characteristics including name, CPU usage, memory allocation,
    state, blocking threads, stack trace, and stack trace depth.
    
    Attributes:
        model_path (str): Path to the XGBoost model file
        input_params_path (str): Path to the input parameters JSON file
        label_mapping_path (str): Path to the label encoder mapping JSON file
        case_insensitive (bool): Whether to use case-insensitive word matching
        model (XGBClassifier): The loaded XGBoost classifier
        model_input_parameters (List[str]): List of input parameter names
        classes (Dict): Mapping from prediction indices to class labels
        tn_vocabulary (List[Tuple[int, re.Pattern]]): Pre-compiled thread name vocabulary patterns
            with their target column indices.
        st_vocabulary (List[Tuple[int, re.Pattern]]): Pre-compiled stack trace vocabulary patterns
            with their target column indices.
        state_values (List[str]): Valid thread state values
        _col_index (Dict[str, int]): O(1) lookup from feature name to column index
    """
    
    # Valid thread state values
    VALID_STATES = ['R', 'CW', 'S', 'Z', 'P', 'B']
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        input_params_path: Optional[str] = None,
        label_mapping_path: Optional[str] = None,
        case_insensitive: bool = False
    ):
        """
        Initialize the JavacoreClassifier.
        
        Args:
            model_path: Path to the XGBoost model file (if None, loads from package resources)
            input_params_path: Path to the input parameters JSON file (if None, loads from package resources)
            label_mapping_path: Path to the label encoder mapping JSON file (if None, loads from package resources)
            case_insensitive: Whether to use case-insensitive word matching
            
        Raises:
            FileNotFoundError: If any of the required files are not found
            json.JSONDecodeError: If JSON files are malformed
        """
        logging.info("Initializing JavacoreClassifier")
        # Store configuration
        self.model_path = model_path
        self.input_params_path = input_params_path
        self.label_mapping_path = label_mapping_path
        self.case_insensitive = case_insensitive
        # Initialize and load the XGBoost model
        self._load_model()
        # Load input parameters and label mappings
        self._load_configurations()
        # Extract vocabularies from input parameters (pre-compiles regex patterns)
        self._extract_vocabularies()
    
    def _load_model(self) -> None:
        """
        Load the XGBoost model from file or package resources.
        
        Raises:
            FileNotFoundError: If model file is not found
        """
        # Initialize classifier with the same hyperparameters used during training
        self.model = XGBClassifier(
            n_estimators = 500,
            learning_rate = 0.05,
            eval_metric = "mlogloss",
            early_stopping_rounds = 5,
            n_jobs = -1
        )
    
        if self.model_path is not None:
            # Load from provided file path
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            #print(f"Loading model from file: {self.model_path}")   #Uncomment for debug
            self.model.load_model(self.model_path)
        else:
            # Load from package resources
            ml_package = files('javacore_analyser.ml')
            model_file = ml_package / 'javacoreThreadsClassifierModel.ubj'
            # XGBoost requires a file path, so we need to use as_file context manager
            from importlib.resources import as_file
            with as_file(model_file) as model_path:
                #print(f"Loading model from package resources: {model_path}")   #Uncomment for debug
                self.model.load_model(str(model_path))

        logging.info("Model loaded successfully")


    def _load_configurations(self) -> None:
        """
        Load input parameters and label encoder mappings from JSON files or package resources.
        
        Raises:
            FileNotFoundError: If configuration files are not found
            json.JSONDecodeError: If JSON files are malformed
        """
        # Load input parameter names
        if self.input_params_path is not None:
            # Load from provided file path
            if not Path(self.input_params_path).exists():
                raise FileNotFoundError(
                    f"Input parameters file not found: {self.input_params_path}"
                )
            with open(self.input_params_path, 'r') as f:
                self.model_input_parameters = json.load(f)
        else:
            # Load from package resources
            ml_package = files('javacore_analyser.ml')
            params_file = ml_package / 'javacoreThreadsClassifierInputParameters.json'
            self.model_input_parameters = json.loads(params_file.read_text())
        
        # Load class label mappings
        if self.label_mapping_path is not None:
            # Load from provided file path
            if not Path(self.label_mapping_path).exists():
                raise FileNotFoundError(
                    f"Label mapping file not found: {self.label_mapping_path}"
                )
            with open(self.label_mapping_path, 'r') as f:
                raw_classes = json.load(f)
        else:
            # Load from package resources
            ml_package = files('javacore_analyser.ml')
            mapping_file = ml_package / 'javacoreThreadsClassifierLabelEncoderMapping.json'
            raw_classes = json.loads(mapping_file.read_text())
        
        # Clean up NaN values in class labels - replace with "Unknown"
        self.classes = []
        for idx, class_label in enumerate(raw_classes):
            if class_label is None or (isinstance(class_label, float) and np.isnan(class_label)):
                logging.warning(f"Class label at index {idx} is NaN/None, replacing with 'Unknown'")
                self.classes.append("Unknown")
            else:
                self.classes.append(class_label)

    def _extract_vocabularies(self) -> None:
        """
        Extract thread name and stack trace vocabularies from input parameters.

        For each vocabulary (thread name / stack trace) this builds:
        - A combined alternation regex  ``\\b(word1|word2|...)\\b`` that scans the
          input text exactly once per predict() call instead of once per word.
        - A ``Dict[str, int]`` mapping each matched word back to its column index so
          ``_fill_word_counts`` can update the feature vector in O(matches) time.

        This is done once at model load time so predict() incurs no compile cost.

        Thread name vocabulary items have 'tn_' prefix.
        Stack trace vocabulary items have 'st_' prefix.
        """
        # Build O(1) column-index lookup dict
        self._col_index: Dict[str, int] = {name: idx for idx, name in enumerate(self.model_input_parameters)}

        flags = re.IGNORECASE if self.case_insensitive else 0

        # Keep per-word lists for the fallback single-predict path and tests
        self.tn_vocabulary: List[Tuple[int, re.Pattern]] = []
        self.st_vocabulary: List[Tuple[int, re.Pattern]] = []

        tn_words: Dict[str, int] = {}  # word -> col_idx
        st_words: Dict[str, int] = {}

        for col_name, col_idx in self._col_index.items():
            if col_name.startswith("tn_"):
                word = col_name[3:]
                self.tn_vocabulary.append((col_idx, re.compile(rf"\b{re.escape(word)}\b", flags)))
                tn_words[word] = col_idx
            elif col_name.startswith("st_"):
                word = col_name[3:]
                self.st_vocabulary.append((col_idx, re.compile(rf"\b{re.escape(word)}\b", flags)))
                st_words[word] = col_idx

        # Combined single-scan patterns  (\b(alt1|alt2|...)\b)
        self._tn_combined: Optional[re.Pattern] = (
            re.compile(r"\b(" + "|".join(re.escape(w) for w in tn_words) + r")\b", flags)
            if tn_words else None
        )
        self._tn_word_col: Dict[str, int] = tn_words

        self._st_combined: Optional[re.Pattern] = (
            re.compile(r"\b(" + "|".join(re.escape(w) for w in st_words) + r")\b", flags)
            if st_words else None
        )
        self._st_word_col: Dict[str, int] = st_words

    def _fill_word_counts(
        self,
        text: str,
        combined_pattern: Optional[re.Pattern],
        word_col: Dict[str, int],
        feature_vector: np.ndarray
    ) -> None:
        """
        Count vocabulary word occurrences in *text* using a single combined regex scan
        and write counts directly into *feature_vector*.

        One ``findall`` call on the combined alternation pattern replaces N individual
        ``findall`` calls (one per vocabulary word), reducing the regex work from O(N)
        scans to O(1) scan + O(matches) dict lookups.

        Args:
            text: Plain string to search (must not be None/NaN).
            combined_pattern: Pre-compiled ``\\b(w1|w2|...)\\b`` pattern, or None if
                the vocabulary is empty.
            word_col: Dict mapping each vocabulary word to its column index.
            feature_vector: 1-D numpy array updated in-place.
        """
        if not combined_pattern:
            return
        for match in combined_pattern.findall(text):
            col_idx = word_col.get(match)
            if col_idx is not None:
                feature_vector[col_idx] += 1

    def _normalize_cpu_usage(self, cpu_value: Union[str, float, int]) -> float:
        """
        Normalize CPU usage value to float.
        
        Handles:
        - Comma as decimal separator (converts to dot)
        - Scientific notation with uppercase E (converts to lowercase e)
        - String to float conversion
        
        Args:
            cpu_value: CPU usage value (can be string, float, or int)
            
        Returns:
            Normalized CPU usage as float
            
        Raises:
            ValueError: If value cannot be converted to float
        """
        if isinstance(cpu_value, (int, float)):
            return float(cpu_value)
        
        # Convert to string and normalize
        cpu_str = str(cpu_value)
        cpu_str = cpu_str.replace(',', '.').replace('E', 'e')
        
        try:
            return float(cpu_str)
        except ValueError:
            raise ValueError(f"Cannot convert CPU usage to float: {cpu_value}")

    def _encode_state(self, state: str) -> Dict[str, int]:
        """
        One-hot encode the thread state.

        Args:
            state: Thread state

        Returns:
            Dictionary mapping state column names to binary values.
            If state is not valid, all encoded values are 0.
        """
        # Create one-hot encoding. Invalid states produce all zeros.
        encoding = {}
        for valid_state in self.VALID_STATES:
            col_name = f"state_{valid_state}"
            encoding[col_name] = 1 if state == valid_state and state in self.VALID_STATES else 0

        return encoding
    
    def _build_feature_vector(
        self,
        name: str,
        cpu_usage: Union[str, float, int],
        allocated_mem: Union[float, int],
        state: str,
        blocking_threads: int,
        stack_trace: str,
        stack_trace_depth: int
    ) -> np.ndarray:
        """
        Build and return a single 1-D feature vector for one thread snapshot.

        The caller is responsible for normalising *stack_trace* to a plain string
        (None / NaN must already be replaced with "").

        Returns:
            1-D numpy array of shape (n_features,)
        """
        feature_vector = np.zeros(len(self.model_input_parameters), dtype=np.float64)

        self._fill_word_counts(stack_trace, self._st_combined, self._st_word_col, feature_vector)
        self._fill_word_counts(name, self._tn_combined, self._tn_word_col, feature_vector)

        for valid_state in self.VALID_STATES:
            col_name = f"state_{valid_state}"
            if col_name in self._col_index:
                feature_vector[self._col_index[col_name]] = 1 if state == valid_state else 0

        feature_vector[self._col_index['cpu_usage']] = self._normalize_cpu_usage(cpu_usage)
        feature_vector[self._col_index['allocated_mem']] = float(allocated_mem)
        feature_vector[self._col_index['blocking_threads']] = int(blocking_threads)
        feature_vector[self._col_index['stack_trace_depth']] = int(stack_trace_depth)

        return feature_vector

    def predict(
        self,
        name: str,
        cpu_usage: Union[str, float, int],
        allocated_mem: Union[float, int],
        state: str,
        blocking_threads: int,
        stack_trace: Optional[str],
        stack_trace_depth: int
    ) -> str:
        """
        Predict the function of a thread based on its characteristics.

        Uses a pre-allocated numpy array as the feature vector and writes all features
        directly by integer column index, avoiding per-call pandas DataFrame overhead.

        Args:
            name: Thread name
            cpu_usage: CPU usage value (can be string with comma separator)
            allocated_mem: Allocated memory in bytes
            state: Thread state (R, CW, S, Z, P, B)
            blocking_threads: Number of blocking threads
            stack_trace: Stack trace text (can be None or NaN)
            stack_trace_depth: Depth of the stack trace

        Returns:
            Predicted thread function class name

        Raises:
            ValueError: If input parameters are invalid

        Example:
            >>> classifier = JavacoreClassifier()
            >>> result = classifier.predict(
            ...     name="WebContainer : 5",
            ...     cpu_usage=0.05,
            ...     allocated_mem=1024000,
            ...     state="R",
            ...     blocking_threads=0,
            ...     stack_trace="at java.lang.Thread.run(Thread.java:748)",
            ...     stack_trace_depth=15
            ... )
            >>> print(result)
            'WebContainer'
        """
        # Handle NaN or None stack trace
        if stack_trace is None or (isinstance(stack_trace, float) and np.isnan(stack_trace)):
            stack_trace = ""
        stack_trace = str(stack_trace)

        feature_vector = self._build_feature_vector(
            name, cpu_usage, allocated_mem, state, blocking_threads, stack_trace, stack_trace_depth
        )

        # Run prediction — reshape to (1, n_features) as required by XGBoost
        prediction = self.model.predict(feature_vector.reshape(1, -1))
        return self.classes[prediction[0]]

    def predict_thread_snapshot(
        self,
        snapshot: ThreadSnapshot
    ) -> str:
        """
        Predict the function of a thread based on its characteristics taking a ThreadSnapshot as parameter.
        """
        logging.debug(f"Predicting thread snapshot: {snapshot.name[:40]}")
        t0 = time.perf_counter()

        name = snapshot.name or ""
        stack_trace = snapshot.stack_trace
        if stack_trace is None:
            stack_trace = ""
        else:
            stack_trace = stack_trace.to_string().replace("\n", " ").replace("\r", " ")

        predicted_class = self.predict(
            name=name,
            cpu_usage=snapshot.cpu_usage,
            allocated_mem=snapshot.allocated_mem,
            state=snapshot.state,
            blocking_threads=len(snapshot.blocking),
            stack_trace=stack_trace,
            stack_trace_depth=snapshot.get_java_stack_depth()
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logging.debug(f"Predicted '{name[:40]}': {predicted_class} ({elapsed_ms:.1f}ms)")
        return predicted_class

    def predict_snapshots_batch(self, snapshots: List[ThreadSnapshot]) -> List[str]:
        """
        Classify a list of ThreadSnapshot objects in a single model.predict() call.

        Building all feature vectors up-front and passing the resulting matrix to
        XGBoost at once eliminates the per-call overhead of invoking model.predict()
        thousands of times and lets XGBoost exploit its internal parallelism
        (n_jobs=-1) across the full batch.

        Args:
            snapshots: List of ThreadSnapshot objects to classify.

        Returns:
            List of predicted class label strings, one per snapshot, in the same order.
        """
        if not snapshots:
            return []

        t0 = time.perf_counter()
        n_features = len(self.model_input_parameters)
        matrix = np.zeros((len(snapshots), n_features), dtype=np.float64)

        for i, snapshot in enumerate(snapshots):
            name = snapshot.name or ""
            stack_trace = snapshot.stack_trace
            if stack_trace is None:
                stack_trace = ""
            else:
                stack_trace = stack_trace.to_string().replace("\n", " ").replace("\r", " ")

            matrix[i] = self._build_feature_vector(
                name=name,
                cpu_usage=snapshot.cpu_usage,
                allocated_mem=snapshot.allocated_mem,
                state=snapshot.state,
                blocking_threads=len(snapshot.blocking),
                stack_trace=stack_trace,
                stack_trace_depth=snapshot.get_java_stack_depth()
            )

        predictions = self.model.predict(matrix)
        results = [self.classes[p] for p in predictions]
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logging.info(f"Batch classified {len(snapshots)} snapshots in {elapsed_ms:.1f}ms")
        return results
