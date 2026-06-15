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
from xgboost import XGBClassifier
import pandas as pd
import json
import re
from typing import Optional, Dict, List, Union
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
        tn_vocabulary (List[str]): Thread name vocabulary
        st_vocabulary (List[str]): Stack trace vocabulary
        state_values (List[str]): Valid thread state values
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
        self.model_path = model_path
        self.input_params_path = input_params_path
        self.label_mapping_path = label_mapping_path
        self.case_insensitive = case_insensitive
        # Initialize and load the XGBoost model
        self._load_model()
        # Load input parameters and label mappings
        self._load_configurations()
        # Extract vocabularies from input parameters
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
        #print("Model loaded successfully")   #Uncomment for debug

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
                self.classes = json.load(f)
        else:
            # Load from package resources
            ml_package = files('javacore_analyser.ml')
            mapping_file = ml_package / 'javacoreThreadsClassifierLabelEncoderMapping.json'
            self.classes = json.loads(mapping_file.read_text())
    
    def _extract_vocabularies(self) -> None:
        """
        Extract thread name and stack trace vocabularies from input parameters.
        
        Thread name vocabulary items have 'tn_' prefix.
        Stack trace vocabulary items have 'st_' prefix.
        """
        self.tn_vocabulary = []
        self.st_vocabulary = []
        for item in self.model_input_parameters:
            if item.startswith("tn_"):
                # Remove 'tn_' prefix
                self.tn_vocabulary.append(item[3:])
            elif item.startswith("st_"):
                # Remove 'st_' prefix
                self.st_vocabulary.append(item[3:])
    
    def _count_word_occurrences(
        self,
        text: str,
        vocabulary: List[str],
        prefix: str
    ) -> Dict[str, int]:
        """
        Count occurrences of vocabulary words in text using word boundaries.
        
        Args:
            text: The text to search in
            vocabulary: List of words to count
            prefix: Prefix to add to column names (e.g., 'tn_' or 'st_')
            
        Returns:
            Dictionary mapping column names to word counts
        """
        # Handle NaN values by converting to empty string
        if isinstance(text, float) and pd.isna(text):
            text = ""
        
        counts = {}
        flags = re.IGNORECASE if self.case_insensitive else 0
        
        for word in vocabulary:
            col_name = f"{prefix}{word}"
            # Use word boundaries to match whole words only
            pattern = rf"\b{re.escape(word)}\b"
            count = len(re.findall(pattern, text, flags=flags))
            counts[col_name] = count
        
        return counts
    
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
        # Create zero-filled DataFrame with model input columns
        df_input = pd.DataFrame(
            [[0.0] * len(self.model_input_parameters)],
            columns=self.model_input_parameters
        )
        
        # Handle NaN or None stack trace
        if stack_trace is None or (isinstance(stack_trace, float) and pd.isna(stack_trace)):
            stack_trace = ""
        
        # Convert stack_trace to string if it's not already
        stack_trace = str(stack_trace)
        
        # Count word occurrences in stack trace
        st_counts = self._count_word_occurrences(
            stack_trace,
            self.st_vocabulary,
            "st_"
        )
        for col_name, count in st_counts.items():
            df_input.at[0, col_name] = count
        
        # Count word occurrences in thread name
        tn_counts = self._count_word_occurrences(
            name,
            self.tn_vocabulary,
            "tn_"
        )
        for col_name, count in tn_counts.items():
            df_input.at[0, col_name] = count
        
        # Encode thread state
        state_encoding = self._encode_state(state)
        for col_name, value in state_encoding.items():
            if col_name in df_input.columns:
                df_input.at[0, col_name] = value
        
        # Normalize and set CPU usage
        normalized_cpu = self._normalize_cpu_usage(cpu_usage)
        df_input.at[0, 'cpu_usage'] = normalized_cpu
        
        # Set fixed parameters
        df_input.at[0, 'allocated_mem'] = float(allocated_mem)
        df_input.at[0, 'blocking_threads'] = int(blocking_threads)
        df_input.at[0, 'stack_trace_depth'] = int(stack_trace_depth)
        
        # Run prediction
        prediction = self.model.predict(df_input)
        
        # Map prediction to class label
        predicted_class = self.classes[prediction[0]]
        return predicted_class

    def predict_thread_snapshot(
        self,
        snapshot: ThreadSnapshot
    ) -> str:
        """
        Predict the function of a thread based on its characteristics takning a ThreadSnapshot as parameter.
        """
        #Extract the features from the ThreadSnapshot
        name = snapshot.name or ""
        cpu_usage = snapshot.cpu_usage
        allocated_mem = snapshot.allocated_mem
        state = snapshot.state
        blocking_threads = len(snapshot.blocking)
        stack_trace = snapshot.stack_trace
        stack_trace_depth = snapshot.get_java_stack_depth()
        if stack_trace is None:
            stack_trace = ""
        else:
            stack_trace = stack_trace.to_string().replace("\n", " ").replace("\r", " ")

        #Predict the function of the thread
        predicted_class = self.predict(
            name=name,
            cpu_usage=cpu_usage,
            allocated_mem=allocated_mem,
            state=state,
            blocking_threads=blocking_threads,
            stack_trace=stack_trace,
            stack_trace_depth=stack_trace_depth
        )
        return predicted_class
    
